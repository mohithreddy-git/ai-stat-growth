from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AssessmentAttempt, CompetencyScoreHistory, LearningProgress, TelemetryEvent, User

EVENT_TYPES = {"ASSESSMENT_START", "RESPONSE", "ASSESSMENT_END", "COURSE_START", "COURSE_PROGRESS", "COURSE_COMPLETE", "DOCUMENT_UPLOAD", "CONTENT_VIEW", "SEARCH", "RECOMMENDATION_VIEW", "RECOMMENDATION_ACCEPT", "RECOMMENDATION_REJECT", "FEEDBACK", "SKILL_PROFILE_UPDATE", "ERROR"}

# Telemetry is deliberately a supporting signal. These values cap its influence
# relative to formal assessments and completion evidence.
TELEMETRY_EVIDENCE_CONFIDENCE = 0.20
TELEMETRY_PROGRESS_SCORE = 5.0


def build_event(eid: str, user: User, *, object_data: dict | None = None, edata: dict | None = None, context: dict | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    if eid not in EVENT_TYPES:
        raise ValueError("Unsupported telemetry event")
    from app.core.config import get_settings
    return {"eid": eid, "ets": int(datetime.now(timezone.utc).timestamp() * 1000), "ver": get_settings().telemetry_version, "mid": str(uuid.uuid4()), "actor": {"id": user.employee_id, "type": "User"}, "context": context or {"channel": "AI_STAT_GROWTH", "pdata": {"id": "ai-stat-growth", "ver": "0.2.0"}}, "object": object_data or {}, "edata": edata or {}, "tags": tags or []}


def _record_telemetry_evidence(db: Session, user: User, payload: dict, mid: str) -> None:
    """Turn strong interaction signals into low-confidence evidence.

    Telemetry never writes a score directly. It adds a bounded, source-specific
    evidence row which the existing evidence aggregator can combine with formal
    assessment, quiz, course, trainer, and self-declaration evidence.
    """
    from app.models import Competency, CompetencyEvidence, Course, EmployeeCompetency, TrainingProgramme

    event_type = payload.get("eid")
    edata = payload.get("edata") or {}
    object_data = payload.get("object") or {}
    competency_ids: set[int] = set()
    scores_by_competency: dict[int, float] = {}
    score = TELEMETRY_PROGRESS_SCORE

    if event_type == "ASSESSMENT_END":
        # The assessment service supplies per-competency percentages so a
        # sequence of RESPONSE events cannot make the last answer dominate.
        raw_scores = edata.get("competency_scores")
        if not isinstance(raw_scores, dict):
            return
        for raw_competency_id, raw_score in raw_scores.items():
            try:
                competency_id = int(raw_competency_id)
                numeric_score = max(0.0, min(100.0, float(raw_score)))
            except (TypeError, ValueError):
                continue
            competency_ids.add(competency_id)
            # The current event carries one score; the per-competency value is
            # passed through the metadata below for the loop to consume.
            scores_by_competency[competency_id] = numeric_score
    elif event_type == "COURSE_COMPLETE":
        resource_id = str(object_data.get("id", ""))
        try:
            resource_type, raw_resource_id = resource_id.split(":", 1)
            resource_model = Course if resource_type == "course" else TrainingProgramme if resource_type == "training_programme" else None
            resource = db.get(resource_model, int(raw_resource_id)) if resource_model else None
        except (TypeError, ValueError):
            resource = None
        if resource is None:
            return
        competency_ids.update(int(item) for item in (resource.competency_ids or []) if str(item).isdigit())
        score = 100.0

    if not competency_ids:
        return
    new_evidence = []
    for competency_id in competency_ids:
        score = scores_by_competency.get(competency_id, TELEMETRY_PROGRESS_SCORE)
        if db.get(Competency, competency_id) is None:
            continue
        employee_competency = db.scalar(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id, EmployeeCompetency.competency_id == competency_id))
        if employee_competency is None:
            continue
        # A retry or client replay should not create a second evidence row.
        duplicate = db.scalar(select(CompetencyEvidence).where(
            CompetencyEvidence.employee_id == user.id,
            CompetencyEvidence.source_type == "TELEMETRY",
            CompetencyEvidence.source_id == mid,
            CompetencyEvidence.competency_id == competency_id,
        ))
        if duplicate is None:
            evidence = CompetencyEvidence(
                employee_id=user.id,
                competency_id=competency_id,
                source_type="TELEMETRY",
                source_id=mid,
                score=score,
                confidence=TELEMETRY_EVIDENCE_CONFIDENCE,
                metadata_json={"event_type": event_type, "object": object_data, "edata": edata},
            )
            db.add(evidence)
            new_evidence.append((employee_competency, evidence))

    if new_evidence:
        # Reuse the canonical evidence aggregator; telemetry becomes a real
        # intelligence input while remaining intentionally low-confidence.
        from app.services.skill_gaps import aggregate_evidence, score_to_level
        db.flush()
        for employee_competency, evidence in new_evidence:
            old_score = float(employee_competency.score)
            updated, confidence, count = aggregate_evidence(db, user.id, employee_competency.competency_id)
            employee_competency.score = updated
            employee_competency.level = score_to_level(updated)
            employee_competency.source = "telemetry"
            employee_competency.confidence = confidence
            employee_competency.evidence_count = count
            from app.models import CompetencyScoreHistory, CompetencyUpdateAudit
            calculation = f"weighted_evidence(TELEMETRY={score:.1f}, confidence={TELEMETRY_EVIDENCE_CONFIDENCE:.2f}, weights=EVIDENCE_WEIGHTS)"
            db.add(CompetencyScoreHistory(user_id=user.id, competency_id=employee_competency.competency_id, evidence_id=evidence.id, previous_score=old_score, new_score=updated, delta=round(updated - old_score, 1), source="telemetry", calculation=calculation))
            db.add(CompetencyUpdateAudit(employee_id=user.id, competency_id=employee_competency.competency_id, old_score=old_score, new_score=updated, source="TELEMETRY", evidence_id=evidence.id, calculation=calculation))


def record_event(db: Session, user: User, payload: dict) -> dict:
    mid = str(payload.get("mid") or uuid.uuid4())
    existing = db.scalar(select(TelemetryEvent).where(TelemetryEvent.mid == mid))
    if existing:
        return {"mid": mid, "accepted": True, "duplicate": True}
    actor = {"id": user.employee_id, "type": "User"}
    row = TelemetryEvent(
        mid=mid,
        eid=payload["eid"],
        ets=payload.get("ets") or int(datetime.now(timezone.utc).timestamp() * 1000),
        ver=payload.get("ver", "3.0"),
        actor=actor,
        context=payload.get("context", {}),
        object=payload.get("object", {}),
        edata=payload.get("edata", {}),
        tags=payload.get("tags", []),
        user_id=user.id,
    )
    db.add(row)
    _record_telemetry_evidence(db, user, payload, mid)
    try:
        db.commit()
    except IntegrityError:
        # ``mid`` is unique. If another request won the race, acknowledge it
        # as a replay; if the constraint failure was unrelated, re-raise it.
        db.rollback()
        existing = db.scalar(select(TelemetryEvent).where(TelemetryEvent.mid == mid))
        if existing is None:
            raise
        return {"mid": mid, "accepted": True, "duplicate": True}
    return {"mid": mid, "accepted": True, "duplicate": False}


def record_batch(db: Session, user: User, payloads: list[dict]) -> list[dict]:
    # Keep the public batch contract while isolating a malformed event from
    # already-accepted message IDs. Each accepted event remains atomic with
    # its telemetry-derived evidence.
    return [record_event(db, user, payload) for payload in payloads]


def _serialize_event(row: TelemetryEvent) -> dict[str, Any]:
    return {"eid": row.eid, "ets": row.ets, "ver": row.ver, "mid": row.mid, "actor": row.actor, "context": row.context, "object": row.object, "edata": row.edata, "tags": row.tags}


def list_events(db: Session, requester: User, user_id: int) -> list[dict]:
    rows = db.scalars(select(TelemetryEvent).where(TelemetryEvent.user_id == user_id).order_by(TelemetryEvent.ets.desc()).limit(500)).all()
    return [_serialize_event(row) for row in rows]


def recent_events(db: Session, limit: int = 50) -> list[dict]:
    safe_limit = max(1, min(100, int(limit)))
    rows = db.scalars(select(TelemetryEvent).order_by(TelemetryEvent.ets.desc(), TelemetryEvent.id.desc()).limit(safe_limit)).all()
    return [_serialize_event(row) for row in rows]


def velocity(db: Session, user_id: int, window_days: int = 30) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    progress = db.scalars(select(LearningProgress).where(LearningProgress.user_id == user_id, LearningProgress.last_activity_at >= since)).all()
    completed = sum(1 for row in progress if row.status == "completed")
    hours = round(sum(float(row.learning_hours or 0) for row in progress), 1)
    attempts = db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.user_id == user_id, AssessmentAttempt.completed_at >= since, AssessmentAttempt.status == "completed")).all()
    accuracy = round(sum(float(row.score or 0) for row in attempts) / len(attempts), 1) if attempts else 0.0
    events = db.scalars(select(TelemetryEvent).where(TelemetryEvent.user_id == user_id, TelemetryEvent.created_at >= since)).all()
    starts = sum(1 for row in events if row.eid in {"COURSE_START", "CONTENT_VIEW", "ASSESSMENT_START"})
    engagement = round(min(100.0, starts / max(1, window_days) * 100), 1)
    accepted = sum(1 for row in events if row.eid == "RECOMMENDATION_ACCEPT")
    viewed = accepted + sum(1 for row in events if row.eid in {"RECOMMENDATION_VIEW", "RECOMMENDATION_REJECT"})
    improvements = db.scalars(select(CompetencyScoreHistory).where(CompetencyScoreHistory.user_id == user_id, CompetencyScoreHistory.created_at >= since)).all()
    improvement_rate = round(sum(float(row.delta or 0) for row in improvements) / len(improvements), 1) if improvements else 0.0
    # Deterministic, low-influence telemetry metric: completed hours plus small
    # credit for completions and assessment activity, normalised by the window.
    learning_velocity = round((hours + completed * 2 + len(attempts)) / max(1, window_days), 3)
    return {"employee_id": user_id, "window_days": window_days, "learning_velocity": learning_velocity, "learning_hours": hours, "completed_resources": completed, "assessment_accuracy": accuracy, "completion_velocity": round(completed / max(1, window_days), 3), "engagement_rate": engagement, "recommendation_acceptance_rate": round(accepted / viewed * 100, 1) if viewed else 0.0, "competency_improvement_rate": improvement_rate}


def skill_profile(db: Session, user_id: int) -> list[dict[str, Any]]:
    from app.models import Competency, EmployeeCompetency
    rows = db.execute(select(EmployeeCompetency, Competency).join(Competency, Competency.id == EmployeeCompetency.competency_id).where(EmployeeCompetency.user_id == user_id).order_by(Competency.name)).all()
    return [{"competency_id": ec.competency_id, "competency": competency.name, "score": ec.score, "confidence": ec.confidence, "evidence_count": ec.evidence_count, "evidence_by_source": _evidence_counts(db, user_id, ec.competency_id)} for ec, competency in rows]


def _evidence_counts(db: Session, user_id: int, competency_id: int) -> dict[str, int]:
    from app.models import CompetencyEvidence
    rows = db.execute(select(CompetencyEvidence.source_type, func.count(CompetencyEvidence.id)).where(CompetencyEvidence.employee_id == user_id, CompetencyEvidence.competency_id == competency_id).group_by(CompetencyEvidence.source_type)).all()
    return {source: int(count) for source, count in rows}


def organization_summary(db: Session) -> dict[str, Any]:
    users = db.scalars(select(User).where(User.is_active.is_(True))).all()
    from app.models import EmployeeCompetency
    scores = [float(row.score) for row in db.scalars(select(EmployeeCompetency)).all()]
    progress = db.scalars(select(LearningProgress)).all()
    attempts = db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.status == "completed")).all()
    improvements = db.scalars(select(CompetencyScoreHistory)).all()
    from app.services.skill_gaps import calculate_skill_gaps
    critical_gaps = sum(1 for user in users for gap in calculate_skill_gaps(db, user) if gap["severity"] == "critical")
    return {"total_officials": len(users), "average_competency": round(sum(scores) / len(scores), 1) if scores else 0.0, "critical_skill_gaps": critical_gaps, "completion_rate": round(sum(1 for row in progress if row.status == "completed") / len(progress) * 100, 1) if progress else 0.0, "assessment_accuracy": round(sum(float(row.score or 0) for row in attempts) / len(attempts), 1) if attempts else 0.0, "learning_hours": round(sum(float(row.learning_hours or 0) for row in progress), 1), "competency_improvement_rate": round(sum(float(row.delta or 0) for row in improvements) / len(improvements), 1) if improvements else 0.0}
