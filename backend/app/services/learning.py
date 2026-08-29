from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Course, EmployeeCompetency, LearningProgress, TrainingProgramme, User
from app.services.telemetry import build_event, record_event


def _resource(db: Session, resource_type: str, resource_id: int):
    model = Course if resource_type == "course" else TrainingProgramme
    resource = db.get(model, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Learning resource not found")
    return resource


def _serialize(db: Session, progress: LearningProgress) -> dict:
    resource = _resource(db, progress.resource_type, progress.resource_id)
    title = resource.title if progress.resource_type == "course" else resource.programme_name
    return {
        "id": progress.id,
        "resource_type": progress.resource_type,
        "resource_id": progress.resource_id,
        "resource_title": title,
        "source": resource.source,
        "status": progress.status,
        "completion_percent": progress.completion_percent,
        "learning_hours": progress.learning_hours,
        "last_activity_at": progress.last_activity_at,
    }


def list_learning_progress(db: Session, user: User) -> list[dict]:
    rows = db.scalars(
        select(LearningProgress)
        .where(LearningProgress.user_id == user.id)
        .order_by(LearningProgress.updated_at.desc(), LearningProgress.id.desc())
    ).all()
    return [_serialize(db, row) for row in rows]


def upsert_learning_progress(db: Session, user: User, payload: dict) -> dict:
    resource = _resource(db, payload["resource_type"], payload["resource_id"])
    row = db.scalar(select(LearningProgress).where(
        LearningProgress.user_id == user.id,
        LearningProgress.resource_type == payload["resource_type"],
        LearningProgress.resource_id == payload["resource_id"],
    ))
    was_completed = bool(row and row.status == "completed")
    if was_completed and payload["status"] != "completed":
        raise HTTPException(status_code=409, detail="Completed learning resources cannot move backwards")
    if row is None:
        row = LearningProgress(
            user_id=user.id,
            resource_type=payload["resource_type"],
            resource_id=payload["resource_id"],
        )
        db.add(row)
    row.status = payload["status"]
    row.completion_percent = 100.0 if payload["status"] == "completed" else payload["completion_percent"]
    row.learning_hours = payload["learning_hours"]
    row.last_activity_at = datetime.now(timezone.utc)
    just_completed = row.status == "completed" and not was_completed

    # Keep the progress row, evidence ledger, score history, and recommendations
    # in one transaction. A failed evidence update must not leave a false
    # completion behind.
    if just_completed:
        from app.services.skill_gaps import update_competency_from_evidence
        for competency_id in (resource.competency_ids or []):
            competency_row = db.scalar(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id, EmployeeCompetency.competency_id == competency_id))
            if competency_row:
                update_competency_from_evidence(
                    db,
                    user.id,
                    competency_id,
                    min(100.0, float(competency_row.score) + 10.0),
                    "COURSE_COMPLETION",
                    f"{row.resource_type}:{row.resource_id}",
                    0.45,
                    {"resource_type": row.resource_type, "resource_id": row.resource_id},
                )
        db.flush()
    db.commit()
    db.refresh(row)

    if just_completed:
        from app.services.recommendations import refresh_recommendations
        refresh_recommendations(db, user)

    # Completion uses a stable message id, so a browser retry cannot create a
    # second completion event or second telemetry-derived evidence record.
    event_type = "COURSE_COMPLETE" if row.status == "completed" else "COURSE_START" if row.completion_percent <= 25 else "COURSE_PROGRESS"
    event = build_event(event_type, user, object_data={"id": f"{row.resource_type}:{row.resource_id}", "type": row.resource_type}, edata={"completion_percent": row.completion_percent, "learning_hours": row.learning_hours})
    if event_type == "COURSE_COMPLETE":
        event["mid"] = f"course-complete:{user.id}:{row.resource_type}:{row.resource_id}"
    if event_type != "COURSE_COMPLETE" or just_completed or not was_completed:
        record_event(db, user, event)
    return _serialize(db, row)
