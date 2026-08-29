from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.language import localized_fields, normalize_language
from app.integrations.seeded_sources import SeededIGOTAdapter, SeededNSSTAAdapter
from app.models import Competency, Course, LearningProgress, Recommendation, RecommendationSnapshot, TrainingProgramme, User
from app.services.skill_gaps import calculate_skill_gaps

WEIGHTS = {
    "gap_score": 0.40,
    "role_match": 0.20,
    "activity_match": 0.15,
    "department_priority": 0.10,
    "future_demand": 0.10,
    "historical_effectiveness": 0.05,
}


def _resource_relevance(resource: dict, gap: dict, user: User, db: Session) -> tuple[float, str, dict]:
    role_match = gap.get("role_relevance", 62.0)
    activity_match = gap.get("activity_criticality", 45.0)
    department_match = gap.get("department_priority", 62.0)
    gap_score = gap.get("gap_score", round((gap["gap"] / gap["required_score"]) * 100 if gap["required_score"] else 0, 1))
    historical_effectiveness = 85.0
    for progress in db.scalars(select(LearningProgress).where(LearningProgress.user_id == user.id)).all():
        if progress.resource_type == resource["resource_type"] and progress.resource_id == resource["id"]:
            historical_effectiveness = 45.0 if progress.status == "completed" else 60.0
    factors = {
        "gap_score": round(gap_score, 1), "role_match": round(role_match, 1), "activity_match": round(activity_match, 1),
        "department_priority": round(department_match, 1), "future_demand": round(gap["future_demand"], 1),
        "historical_effectiveness": round(historical_effectiveness, 1), "required_for_activities": gap.get("required_for_activities", []),
        "competency": gap["competency"], "current_score": gap["current_score"], "required_score": gap["required_score"], "gap": gap["gap"],
    }
    score = sum(WEIGHTS[key] * factors[key] for key in WEIGHTS)
    activity_text = ", ".join(factors["required_for_activities"]) or "your mapped role activities"
    reason = (
        f"{resource['title']} is ranked because {gap['competency']} is required for {activity_text}. "
        f"Current competency is {gap['current_score']:.0f}% against a {gap['required_score']:.0f}% target, leaving a {gap['gap']:.0f}-point gap. "
        f"Role relevance is {role_match:.0f}%, activity criticality is {activity_match:.0f}%, department priority is {department_match:.0f}%, and future demand is {gap['future_demand']:.0f}%."
    )
    return round(max(0.0, min(100.0, score)), 1), reason, factors


def _format_recommendation(resource: dict, gap: dict, score: float, reason: str, factors: dict, competency: Competency, language: str = "en", progress_status: str = "not_started", completion_percent: float = 0) -> dict:
    defaults = {
        "title": resource["title"],
        "description": resource["description"],
        "reason": reason,
        "expected_outcome": f"Build {competency.name} toward the {gap['required_level']} target and reduce the current {gap['gap']:.0f}-point gap.",
    }
    selected, requested_language, localized = localized_fields(resource.get("localizations"), language, defaults)
    localizations = resource.get("localizations") if isinstance(resource.get("localizations"), dict) else {}
    english = localizations.get("en") if isinstance(localizations.get("en"), dict) else {}
    hindi = localizations.get("hi") if isinstance(localizations.get("hi"), dict) else {}
    return {
        "id": resource["id"], "resource_type": resource["resource_type"], "external_id": resource["external_id"],
        "title": selected["title"], "source": resource["source"], "competency_id": competency.id, "competency": competency.name,
        "description": selected["description"], "duration": resource["duration"], "duration_label": resource["duration_label"],
        "requested_language": requested_language, "localized": localized,
        "localization_label": localizations.get("label"),
        "title_en": english.get("title") or resource["title"], "title_hi": hindi.get("title"),
        "description_en": english.get("description") or resource["description"], "description_hi": hindi.get("description"),
        "reason_en": english.get("reason") or reason, "reason_hi": hindi.get("reason"),
        "expected_outcome_en": english.get("expected_outcome") or defaults["expected_outcome"], "expected_outcome_hi": hindi.get("expected_outcome"),
        "difficulty": resource["difficulty"], "relevance_score": score, "priority": gap["priority_severity"], "priority_score": gap["priority_score"],
        "role_match": factors.get("role_match", gap["role_relevance"]), "activity_match": factors.get("activity_match", gap["activity_criticality"]), "reason": selected["reason"],
        "expected_outcome": selected["expected_outcome"],
        "current_score": gap["current_score"], "required_score": gap["required_score"], "gap": gap["gap"],
        "role_relevance": gap["role_relevance"], "department_priority": gap["department_priority"], "future_demand": gap["future_demand"],
        "expected_improvement": min(25.0, max(3.0, round(gap["gap"] * 0.35, 1))), "url": resource["url"], "is_prototype": resource["is_prototype"],
        "progress_status": progress_status, "completion_percent": completion_percent,
        "activities": factors.get("required_for_activities", []), "explanation_data": factors,
        "historical_effectiveness": factors.get("historical_effectiveness", 0),
    }


def build_recommendations(db: Session, user: User, language: str = "en") -> list[dict]:
    gaps = [gap for gap in calculate_skill_gaps(db, user) if gap["gap"] > 0]
    if not gaps:
        return []
    gap_by_competency = {gap["competency_id"]: gap for gap in gaps}
    adapter_models = [(SeededIGOTAdapter(db), Course), (SeededNSSTAAdapter(db), TrainingProgramme)]
    resources: list[dict] = []
    for adapter, model in adapter_models:
        for row in db.scalars(select(model).where(model.is_prototype.is_(True))).all():
            matched = [gap_by_competency[comp_id] for comp_id in (row.competency_ids or []) if comp_id in gap_by_competency]
            if not matched:
                continue
            resource = adapter._serialize(row)
            gap = max(matched, key=lambda item: (item["priority_score"], item["gap"]))
            competency = db.get(Competency, gap["competency_id"])
            score, reason, factors = _resource_relevance(resource, gap, user, db)
            progress = db.scalar(select(LearningProgress).where(LearningProgress.user_id == user.id, LearningProgress.resource_type == resource["resource_type"], LearningProgress.resource_id == resource["id"]))
            resources.append(_format_recommendation(resource, gap, score, reason, factors, competency, language, progress.status if progress else "not_started", progress.completion_percent if progress else 0))
    resources.sort(key=lambda item: (item["relevance_score"], item["gap"]), reverse=True)
    deduped = []
    seen: set[tuple[str, int]] = set()
    for resource in resources:
        key = (resource["resource_type"], resource["id"])
        if key not in seen:
            seen.add(key); deduped.append(resource)
        if len(deduped) == 15:
            break
    return deduped


def refresh_recommendations(db: Session, user: User, language: str = "en") -> list[dict]:
    recommendations = build_recommendations(db, user, normalize_language(language))
    db.execute(delete(Recommendation).where(Recommendation.user_id == user.id))
    for item in recommendations:
        factors = item.get("explanation_data", {})
        db.add(Recommendation(user_id=user.id, resource_type=item["resource_type"], resource_id=item["id"], competency_id=item["competency_id"], relevance_score=item["relevance_score"], priority=item["priority"], reason=item["reason"], expected_improvement=item["expected_improvement"], factors=factors, activities=item.get("activities", [])))
        db.add(RecommendationSnapshot(employee_id=user.id, resource_type=item["resource_type"], resource_id=item["id"], score=item["relevance_score"], factors={**factors, "reason": item["reason"], "expected_improvement": item["expected_improvement"]}))
    db.commit()
    return recommendations
