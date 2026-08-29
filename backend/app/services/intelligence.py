from math import sqrt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    ActivityCompetency,
    Competency,
    CompetencyEvidence,
    CompetencyVectorSnapshot,
    EmployeeCompetency,
    EmployeeRole,
    Position,
    PositionRole,
    RoleActivity,
    RoleCompetencyRequirement,
    User,
)
from app.services.skill_gaps import LEVEL_SCORES, level_label, required_score, score_to_level


def frac_profile(db: Session, user: User) -> dict[str, Any]:
    assignment = db.scalar(select(EmployeeRole).where(EmployeeRole.employee_id == user.id, EmployeeRole.is_primary.is_(True)))
    if not assignment:
        return {"employee_id": user.id, "position_id": None, "position": None, "role_id": None, "role": None, "activities": [], "competencies": []}
    role = db.get(PositionRole, assignment.role_id)
    position = db.get(Position, role.position_id) if role else None
    activities = []
    competency_map: dict[int, dict[str, Any]] = {}
    current_scores = {
        row.competency_id: (float(row.score), row.level or score_to_level(float(row.score)))
        for row in db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all()
    }
    role_activities = db.execute(
        select(RoleActivity, Activity).join(Activity, Activity.id == RoleActivity.activity_id).where(RoleActivity.role_id == assignment.role_id)
    ).all()
    for role_activity, activity in role_activities:
        requirements = db.execute(
            select(ActivityCompetency, Competency).join(Competency, Competency.id == ActivityCompetency.competency_id).where(ActivityCompetency.activity_id == activity.id)
        ).all()
        for requirement, competency in requirements:
            required_value = LEVEL_SCORES.get(requirement.required_level, 60.0)
            current_value, current_level = current_scores.get(requirement.competency_id, (0.0, 1))
            activities.append({
                "activity_id": activity.id, "activity": activity.name, "competency_id": requirement.competency_id, "criticality": role_activity.criticality,
                "required_level": requirement.required_level, "required_score": required_value, "importance": requirement.importance,
                "current_score": round(max(0.0, min(100.0, current_value)), 1), "current_level": current_level,
                "current_level_label": level_label(current_level), "gap": round(max(0.0, required_value - current_value), 1),
            })
            entry = competency_map.setdefault(competency.id, {"competency_id": competency.id, "competency": competency.name, "type": competency.competency_type, "required_for": []})
            if activity.name not in entry["required_for"]:
                entry["required_for"].append(activity.name)
    return {"employee_id": user.id, "position_id": position.id if position else None, "position": position.name if position else None, "role_id": role.id if role else None, "role": role.name if role else None, "activities": activities, "competencies": list(competency_map.values())}


def evidence_for_employee(db: Session, user_id: int, competency_id: int | None = None) -> list[dict[str, Any]]:
    query = select(CompetencyEvidence).where(CompetencyEvidence.employee_id == user_id)
    if competency_id:
        query = query.where(CompetencyEvidence.competency_id == competency_id)
    rows = db.scalars(query.order_by(CompetencyEvidence.created_at.desc(), CompetencyEvidence.id.desc())).all()
    return [{"id": row.id, "competency_id": row.competency_id, "source_type": row.source_type, "source_id": row.source_id, "score": row.score, "confidence": row.confidence, "metadata": row.metadata_json or {}, "created_at": row.created_at} for row in rows]


def competency_vector(db: Session, user: User) -> dict[str, Any]:
    profile_rows = db.execute(select(EmployeeCompetency, Competency).join(Competency, Competency.id == EmployeeCompetency.competency_id).where(EmployeeCompetency.user_id == user.id).order_by(Competency.id)).all()
    frac = frac_profile(db, user)
    requirements: dict[int, tuple[float, float]] = {}
    for item in frac["activities"]:
        competency_id = item.get("competency_id")
        if competency_id:
            current = requirements.get(competency_id, (0.0, 0.0))
            requirements[competency_id] = (max(current[0], item["required_score"]), max(current[1], item["importance"]))
    dimensions = []
    current_vector = []
    target_vector = []
    gaps = []
    for employee_competency, competency in profile_rows:
        target_score = requirements.get(competency.id, (required_score(competency), competency.weight))[0]
        current = max(0.0, min(100.0, float(employee_competency.score)))
        current_norm = round(current / 100.0, 4)
        target_norm = round(target_score / 100.0, 4)
        dimensions.append({"competency_id": competency.id, "code": competency.code, "competency": competency.name, "weight": float(competency.weight), "current_score": current, "target_score": target_score})
        current_vector.append(current_norm); target_vector.append(target_norm)
        gaps.append({"competency_id": competency.id, "competency": competency.name, "gap": round(max(target_score - current, 0), 1), "current": current, "target": target_score})
    weighted_distance = sqrt(sum(float(row["weight"]) * ((target_vector[i] - current_vector[i]) ** 2) for i, row in enumerate(dimensions))) if dimensions else 0.0
    dot = sum(c * t for c, t in zip(current_vector, target_vector))
    current_norm = sqrt(sum(c * c for c in current_vector)); target_norm = sqrt(sum(t * t for t in target_vector))
    cosine = dot / (current_norm * target_norm) if current_norm and target_norm else 0.0
    alignment = max(0.0, min(100.0, cosine * 100.0))
    gaps = sorted(gaps, key=lambda item: item["gap"], reverse=True)
    response = {"employee_id": user.id, "dimensions": dimensions, "current_vector": current_vector, "target_vector": target_vector, "competency_specific_gaps": gaps, "critical_gaps": [gap for gap in gaps if gap["gap"] >= 30], "weighted_distance": round(weighted_distance, 4), "cosine_similarity": round(cosine, 4), "overall_alignment_score": round(alignment, 1)}
    db.add(CompetencyVectorSnapshot(employee_id=user.id, vector_type="CURRENT", vector_json=current_vector, dimensions_json=dimensions, weighted_distance=weighted_distance, cosine_similarity=cosine, alignment_score=alignment))
    db.commit()
    return response
