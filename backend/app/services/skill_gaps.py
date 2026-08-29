from collections import defaultdict
from datetime import datetime, timezone
from math import sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    ActivityCompetency,
    Competency,
    CompetencyEvidence,
    CompetencyScoreHistory,
    Department,
    EmployeeCompetency,
    EmployeeRole,
    FutureSkillDemand,
    LearningProgress,
    PositionRole,
    RoleActivity,
    RoleCompetencyRequirement,
    SkillForecast,
    User,
)

LEVEL_LABELS = {1: "Beginner", 2: "Elementary", 3: "Intermediate", 4: "Advanced", 5: "Expert"}
LEVEL_SCORES = {1: 20.0, 2: 40.0, 3: 60.0, 4: 80.0, 5: 100.0}
EVIDENCE_WEIGHTS = {
    "ASSESSMENT": 0.40,
    "QUIZ": 0.25,
    "COURSE_COMPLETION": 0.15,
    "TRAINER_REVIEW": 0.10,
    "TELEMETRY": 0.10,
    "PRACTICE": 0.10,
    "ROLE_ACTIVITY": 0.10,
    "SELF_DECLARATION": 0.10,
}

ROLE_FOCUS = {
    "NSO": {"SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY", "METADATA_STANDARDS", "PYTHON", "SQL", "GIS", "DATA_VISUALIZATION", "ARTIFICIAL_INTELLIGENCE"},
    "SURVEY": {"SURVEY_DESIGN", "SAMPLING", "GIS", "DATA_QUALITY", "PYTHON", "DATA_VISUALIZATION"},
    "ANALYTICS": {"PYTHON", "SQL", "DATA_ENGINEERING", "MACHINE_LEARNING", "ARTIFICIAL_INTELLIGENCE", "CLOUD_COMPUTING", "APIS", "DATA_VISUALIZATION"},
    "ECON": {"NATIONAL_ACCOUNTS", "PRICE_STATISTICS", "INDUSTRIAL_STATISTICS", "SQL", "DATA_QUALITY", "DATA_VISUALIZATION"},
    "SOCIAL": {"LABOUR_STATISTICS", "SDG_INDICATORS", "SURVEY_DESIGN", "DATA_QUALITY", "DATA_VISUALIZATION"},
}
DEPARTMENT_PRIORITY = {
    "NSO": {"GIS", "PYTHON", "ARTIFICIAL_INTELLIGENCE", "DATA_QUALITY", "METADATA_STANDARDS", "DATA_VISUALIZATION"},
    "SURVEY": {"GIS", "SURVEY_DESIGN", "SAMPLING", "DATA_QUALITY", "PYTHON"},
    "ANALYTICS": {"PYTHON", "DATA_ENGINEERING", "MACHINE_LEARNING", "ARTIFICIAL_INTELLIGENCE", "CLOUD_COMPUTING"},
    "ECON": {"DATA_QUALITY", "SQL", "DATA_VISUALIZATION"},
    "SOCIAL": {"SDG_INDICATORS", "DATA_QUALITY", "SURVEY_DESIGN"},
}
ACTION_BY_CATEGORY = {
    "Technical": "Complete a practical learning resource and apply the skill to a current statistical work product.",
    "Statistical": "Take a domain-focused learning resource and validate the method on a current official-statistics workflow.",
    "Digital Governance": "Complete a governed-practice module and review the relevant control with your team.",
    "Behavioural & Managerial": "Choose a facilitated development activity and apply the skill to an active programme milestone.",
}


def score_to_level(score: float) -> int:
    if score < 20:
        return 1
    if score < 40:
        return 2
    if score < 60:
        return 3
    if score < 80:
        return 4
    return 5


def level_label(level: int) -> str:
    return LEVEL_LABELS.get(level, "Intermediate")


def required_score(competency: Competency) -> float:
    return LEVEL_SCORES.get(competency.required_level, 60.0)


def level_for_score(score: float) -> int:
    return min(LEVEL_SCORES, key=lambda level: abs(LEVEL_SCORES[level] - score))


def severity_for_gap(gap: float) -> str:
    # Preserve the Phase 2 contract: severity reflects absolute score deficit.
    if gap >= 30:
        return "critical"
    if gap >= 20:
        return "high"
    if gap >= 10:
        return "medium"
    return "low"


def priority_severity(priority_score: float) -> str:
    if priority_score >= 80:
        return "critical"
    if priority_score >= 60:
        return "high"
    if priority_score >= 35:
        return "medium"
    return "low"


def gap_priority(gap_score: float, role_relevance: float, department_priority: float, future_demand: float, learning_history_relevance: float) -> float:
    """Legacy Phase 2 scorer retained for compatibility and unit-test stability."""
    value = 0.40 * gap_score + 0.20 * role_relevance + 0.15 * department_priority + 0.15 * future_demand + 0.10 * learning_history_relevance
    return round(max(0.0, min(100.0, value)), 1)


def intelligence_priority(gap_score: float, role_relevance: float, activity_criticality: float, department_priority: float, future_demand: float) -> float:
    """FRAC-aware score: all inputs are normalised to 0-100."""
    value = 0.40 * gap_score + 0.20 * role_relevance + 0.15 * activity_criticality + 0.15 * department_priority + 0.10 * future_demand
    return round(max(0.0, min(100.0, value)), 1)


def _learning_history_relevance(db: Session, user_id: int, competency_id: int) -> float:
    from app.models import Course, TrainingProgramme
    for item in db.scalars(select(LearningProgress).where(LearningProgress.user_id == user_id)).all():
        resource = db.get(Course if item.resource_type == "course" else TrainingProgramme, item.resource_id)
        if resource and competency_id in (resource.competency_ids or []):
            return 35.0 if item.status == "completed" else 55.0
    return 85.0


def _role_activity_context(db: Session, user: User, competency_id: int) -> tuple[list[str], float, float, float]:
    assignments = db.scalars(select(EmployeeRole).where(EmployeeRole.employee_id == user.id, EmployeeRole.is_primary.is_(True))).all()
    if not assignments:
        return [], 40.0, 40.0, 40.0
    activity_names: list[str] = []
    relevance = 40.0
    criticality = 40.0
    importance = 40.0
    for assignment in assignments:
        role_activities = db.execute(
            select(RoleActivity, Activity, ActivityCompetency)
            .join(Activity, Activity.id == RoleActivity.activity_id)
            .join(ActivityCompetency, ActivityCompetency.activity_id == Activity.id)
            .where(RoleActivity.role_id == assignment.role_id, ActivityCompetency.competency_id == competency_id)
        ).all()
        for role_activity, activity, activity_competency in role_activities:
            activity_names.append(activity.name)
            relevance = max(relevance, min(100.0, 50.0 + activity_competency.importance * 50.0))
            criticality = max(criticality, role_activity.criticality)
            importance = max(importance, min(100.0, activity_competency.importance * 100.0))
    return sorted(set(activity_names)), round(relevance, 1), round(criticality, 1), round(importance, 1)


def _required_score_for_role(db: Session, user: User, competency: Competency) -> tuple[float, float]:
    assignments = db.scalars(select(EmployeeRole).where(EmployeeRole.employee_id == user.id, EmployeeRole.is_primary.is_(True))).all()
    levels = []
    importance = competency.weight * 50.0
    for assignment in assignments:
        requirement = db.scalar(select(RoleCompetencyRequirement).where(RoleCompetencyRequirement.role_id == assignment.role_id, RoleCompetencyRequirement.competency_id == competency.id))
        if requirement:
            levels.append(requirement.required_level)
            importance = max(importance, min(100.0, requirement.importance * 100.0))
    level = max(levels) if levels else competency.required_level
    return LEVEL_SCORES.get(level, required_score(competency)), round(importance, 1)


def _future_demand_map(db: Session) -> dict[int, float]:
    modern = {row.competency_id: row.projected_demand for row in db.scalars(select(FutureSkillDemand)).all()}
    legacy = {row.competency_id: row.projected_demand for row in db.scalars(select(SkillForecast)).all()}
    legacy.update(modern)
    return {key: round(float(value), 1) for key, value in legacy.items()}


def calculate_skill_gaps(db: Session, user: User) -> list[dict]:
    rows = db.execute(select(EmployeeCompetency, Competency).join(Competency, Competency.id == EmployeeCompetency.competency_id).where(EmployeeCompetency.user_id == user.id)).all()
    department = db.get(Department, user.department_id)
    department_code = department.code if department else ""
    department_focus = DEPARTMENT_PRIORITY.get(department_code, set())
    forecast_map = _future_demand_map(db)
    results = []
    for employee_competency, competency in rows:
        target, role_importance = _required_score_for_role(db, user, competency)
        current = round(float(employee_competency.score), 1)
        gap = round(max(0.0, target - current), 1)
        activities, role_relevance, activity_criticality, activity_importance = _role_activity_context(db, user, competency.id)
        if not activities:
            role_relevance = 95.0 if competency.code in ROLE_FOCUS.get(department_code, set()) else 62.0
            activity_criticality = 70.0 if role_relevance >= 90 else 45.0
        department_priority = 100.0 if competency.code in department_focus else 62.0
        future_demand = round(float(forecast_map.get(competency.id, 45.0)), 1)
        gap_score = round((gap / target) * 100 if target else 0, 1)
        history_relevance = _learning_history_relevance(db, user.id, competency.id)
        priority_score = intelligence_priority(gap_score, role_relevance, max(activity_criticality, activity_importance), department_priority, future_demand)
        severity = severity_for_gap(gap)
        results.append({
            "competency_id": competency.id, "competency": competency.name, "code": competency.code, "category": competency.category,
            "current_score": current, "required_score": target, "gap": gap, "severity": severity, "priority_severity": priority_severity(priority_score),
            "priority_score": priority_score, "gap_score": gap_score, "role_relevance": role_relevance, "activity_criticality": max(activity_criticality, activity_importance),
            "department_priority": department_priority, "future_demand": future_demand, "learning_history_relevance": history_relevance,
            "required_for_activities": activities, "activity_importance": role_importance,
            "explanation": f"{competency.name} is prioritised because it is required for {', '.join(activities) if activities else 'the mapped role responsibilities'} associated with your role. current score is {current:.0f}% against a {target:.0f}% target; the gap is {gap:.0f} points. Role relevance is {role_relevance:.0f}%, activity criticality is {max(activity_criticality, activity_importance):.0f}%, department priority is {department_priority:.0f}%, and future demand is {future_demand:.0f}%.",
            "recommended_next_action": ACTION_BY_CATEGORY.get(competency.category, ACTION_BY_CATEGORY["Technical"]),
            "current_level": level_label(employee_competency.level or score_to_level(current)), "required_level": level_label(level_for_score(target)),
        })
    return sorted(results, key=lambda item: (item["priority_score"], item["gap"]), reverse=True)


def competency_domain_summary(db: Session, user: User) -> dict:
    """Summarise the authoritative competency framework for one employee.

    Counts come from the competency table itself. Current and target averages
    are optional employee-context metrics and deliberately ignore a missing
    employee competency row instead of fabricating a zero score.
    """
    competencies = db.scalars(select(Competency).order_by(Competency.category, Competency.name)).all()
    employee_rows = db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all()
    current_by_id = {row.competency_id: float(row.score) for row in employee_rows}
    grouped: dict[str, dict[str, list[float]]] = {}
    for competency in competencies:
        bucket = grouped.setdefault(competency.category, {"current": [], "target": []})
        if competency.id in current_by_id:
            bucket["current"].append(current_by_id[competency.id])
            target, _ = _required_score_for_role(db, user, competency)
            bucket["target"].append(target)
    domains = []
    for name in sorted(grouped):
        bucket = grouped[name]
        domains.append({
            "name": name,
            "count": sum(1 for competency in competencies if competency.category == name),
            "average_current_score": round(sum(bucket["current"]) / len(bucket["current"]), 1) if bucket["current"] else None,
            "average_target_score": round(sum(bucket["target"]) / len(bucket["target"]), 1) if bucket["target"] else None,
        })
    return {"domains": domains, "total_competencies": len(competencies)}


def get_competency_profile(db: Session, user: User) -> dict:
    rows = db.execute(select(EmployeeCompetency, Competency).join(Competency, Competency.id == EmployeeCompetency.competency_id).where(EmployeeCompetency.user_id == user.id)).all()
    history_rows = db.scalars(select(CompetencyScoreHistory).where(CompetencyScoreHistory.user_id == user.id).order_by(CompetencyScoreHistory.id.desc())).all()
    latest_history: dict[int, CompetencyScoreHistory] = {}
    for history in history_rows:
        latest_history.setdefault(history.competency_id, history)
    competencies = []
    category_values: defaultdict[str, list[float]] = defaultdict(list)
    for employee_competency, competency in rows:
        current = round(float(employee_competency.score), 1)
        current_level = employee_competency.level or score_to_level(current)
        category_values[competency.category].append(current)
        history = latest_history.get(competency.id)
        competencies.append({
            "competency_id": competency.id, "code": competency.code, "name": competency.name, "category": competency.category,
            "current_score": current, "current_level": current_level, "current_level_label": level_label(current_level),
            "target_level": competency.required_level, "target_level_label": level_label(competency.required_level), "required_score": required_score(competency),
            "delta_from_previous": round(history.delta, 1) if history else None, "last_assessed_at": employee_competency.last_assessed_at,
            "confidence": round(float(employee_competency.confidence or 0.5), 2), "evidence_count": int(employee_competency.evidence_count or 0), "description": competency.description,
        })
    competencies.sort(key=lambda item: item["current_score"], reverse=True)
    weight_total = sum(item["current_score"] * next((c.weight for c in db.scalars(select(Competency).where(Competency.id == item["competency_id"])).all()), 1.0) for item in competencies)
    weight_sum = sum(next((c.weight for c in db.scalars(select(Competency).where(Competency.id == item["competency_id"])).all()), 1.0) for item in competencies) or 1.0
    return {"user_id": user.id, "overall_readiness": round(weight_total / weight_sum, 1), "category_scores": {category: round(sum(values) / len(values), 1) for category, values in category_values.items()}, "competencies": competencies, "strengths": competencies[:5], "weaknesses": sorted(competencies, key=lambda item: item["current_score"])[:5]}


def aggregate_evidence(db: Session, user_id: int, competency_id: int) -> tuple[float, float, int]:
    rows = db.scalars(select(CompetencyEvidence).where(CompetencyEvidence.employee_id == user_id, CompetencyEvidence.competency_id == competency_id).order_by(CompetencyEvidence.created_at, CompetencyEvidence.id)).all()
    latest_by_source: dict[str, CompetencyEvidence] = {}
    for row in rows:
        latest_by_source[row.source_type.upper()] = row
    if not latest_by_source:
        return 0.0, 0.0, 0
    numerator = 0.0
    denominator = 0.0
    confidence_total = 0.0
    for source, evidence in latest_by_source.items():
        weight = EVIDENCE_WEIGHTS.get(source, 0.05)
        confidence = max(0.05, min(1.0, float(evidence.confidence)))
        numerator += float(evidence.score) * weight * confidence
        denominator += weight * confidence
        confidence_total += weight * confidence
    return round(numerator / denominator if denominator else 0.0, 1), round(min(1.0, confidence_total), 2), len(rows)


def update_competency_from_evidence(db: Session, user_id: int, competency_id: int, score: float, source_type: str, source_id: str | None = None, confidence: float = 0.8, metadata: dict | None = None, attempt_id: int | None = None) -> dict:
    employee_competency = db.scalar(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user_id, EmployeeCompetency.competency_id == competency_id))
    if employee_competency is None:
        raise ValueError("Employee competency record not found")
    previous = float(employee_competency.score)
    evidence = CompetencyEvidence(employee_id=user_id, competency_id=competency_id, source_type=source_type.upper(), source_id=source_id, score=max(0.0, min(100.0, float(score))), confidence=max(0.0, min(1.0, float(confidence))), metadata_json=metadata or {})
    db.add(evidence)
    db.flush()
    updated, evidence_confidence, evidence_count = aggregate_evidence(db, user_id, competency_id)
    employee_competency.score = updated
    employee_competency.level = score_to_level(updated)
    employee_competency.source = source_type.lower()
    employee_competency.confidence = evidence_confidence
    employee_competency.evidence_count = evidence_count
    employee_competency.last_assessed_at = datetime.now(timezone.utc)
    calculation = f"weighted_evidence({source_type.upper()}={score:.1f}, weights={EVIDENCE_WEIGHTS})"
    delta = round(updated - previous, 1)
    db.add(CompetencyScoreHistory(user_id=user_id, competency_id=competency_id, assessment_attempt_id=attempt_id, evidence_id=evidence.id, previous_score=previous, new_score=updated, delta=delta, source=source_type.lower(), calculation=calculation))
    from app.models import CompetencyUpdateAudit
    db.add(CompetencyUpdateAudit(employee_id=user_id, competency_id=competency_id, old_score=previous, new_score=updated, source=source_type.upper(), evidence_id=evidence.id, calculation=calculation))
    return {"previous_score": previous, "updated_score": updated, "delta": delta, "evidence_id": evidence.id}


def update_competency_from_assessment(db: Session, user_id: int, competency_id: int, assessment_score: float, attempt_id: int) -> dict:
    return update_competency_from_evidence(db, user_id, competency_id, assessment_score, "ASSESSMENT", str(attempt_id), 0.9, {"assessment_attempt_id": attempt_id}, attempt_id)
