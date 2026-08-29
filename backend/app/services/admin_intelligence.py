from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AssessmentAttempt, Competency, Department, EmployeeCompetency, FutureSkillDemand, LearningProgress, Role, SkillForecast, User
from app.services.skill_gaps import calculate_skill_gaps


def _employee_users(db: Session) -> list[User]:
    employee_role = db.scalar(select(Role).where(Role.name == "EMPLOYEE"))
    query = select(User).where(User.is_active.is_(True))
    if employee_role:
        query = query.where(User.role_id == employee_role.id)
    return db.scalars(query).all()


def overview(db: Session) -> dict:
    users = _employee_users(db)
    scores = [float(row.score) for user in users for row in db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all()]
    gaps = [gap for user in users for gap in calculate_skill_gaps(db, user)]
    progress = db.scalars(select(LearningProgress)).all()
    attempts = db.scalars(select(AssessmentAttempt).where(AssessmentAttempt.status == "completed")).all()
    return {
        "total_officials": len(users),
        "average_competency": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "critical_skill_gaps": sum(1 for gap in gaps if gap["severity"] == "critical"),
        "training_completion_rate": round(sum(1 for row in progress if row.status == "completed") / len(progress) * 100, 1) if progress else 0.0,
        "assessment_performance": round(sum(float(row.score or 0) for row in attempts) / len(attempts), 1) if attempts else 0.0,
        "learning_hours": round(sum(float(row.learning_hours or 0) for row in progress), 1),
        "department_count": len(db.scalars(select(Department)).all()),
    }


def departments(db: Session) -> list[dict]:
    users = _employee_users(db)
    rows = []
    for department in db.scalars(select(Department).order_by(Department.name)).all():
        members = [user for user in users if user.department_id == department.id]
        member_scores = [float(row.score) for user in members for row in db.scalars(select(EmployeeCompetency).where(EmployeeCompetency.user_id == user.id)).all()]
        member_gaps = [gap for user in members for gap in calculate_skill_gaps(db, user)]
        rows.append({"department_id": department.id, "department": department.name, "officials": len(members), "average_competency": round(sum(member_scores) / len(member_scores), 1) if member_scores else 0.0, "critical_gaps": sum(1 for gap in member_gaps if gap["severity"] == "critical"), "average_gap": round(sum(gap["gap"] for gap in member_gaps) / len(member_gaps), 1) if member_gaps else 0.0})
    return rows


def skill_gaps(db: Session) -> list[dict]:
    users = _employee_users(db)
    grouped: dict[int, dict] = {}
    for user in users:
        for gap in calculate_skill_gaps(db, user):
            bucket = grouped.setdefault(gap["competency_id"], {"competency_id": gap["competency_id"], "competency": gap["competency"], "category": gap["category"], "employees": 0, "average_current_score": 0.0, "average_gap": 0.0, "critical_count": 0, "priority_score": 0.0})
            bucket["employees"] += 1; bucket["average_current_score"] += gap["current_score"]; bucket["average_gap"] += gap["gap"]; bucket["priority_score"] += gap["priority_score"]
            bucket["critical_count"] += int(gap["severity"] == "critical")
    for bucket in grouped.values():
        n = bucket["employees"]; bucket["average_current_score"] = round(bucket["average_current_score"] / n, 1); bucket["average_gap"] = round(bucket["average_gap"] / n, 1); bucket["priority_score"] = round(bucket["priority_score"] / n, 1)
    return sorted(grouped.values(), key=lambda row: (row["priority_score"], row["average_gap"]), reverse=True)


def training_effectiveness(db: Session) -> list[dict]:
    from app.models import Course, TrainingProgramme
    resources = {("course", row.id): row.title for row in db.scalars(select(Course)).all()}
    resources.update({("training_programme", row.id): row.programme_name for row in db.scalars(select(TrainingProgramme)).all()})
    grouped: dict[tuple[str, int], list[LearningProgress]] = defaultdict(list)
    for row in db.scalars(select(LearningProgress)).all(): grouped[(row.resource_type, row.resource_id)].append(row)
    result = []
    for key, rows in grouped.items():
        result.append({"resource_type": key[0], "resource_id": key[1], "title": resources.get(key, "Unknown resource"), "learners": len(rows), "completion_rate": round(sum(row.completion_percent for row in rows) / len(rows), 1), "completed": sum(row.status == "completed" for row in rows), "learning_hours": round(sum(row.learning_hours for row in rows), 1)})
    return sorted(result, key=lambda row: (row["completion_rate"], row["learners"]), reverse=True)


def forecast(db: Session) -> list[dict]:
    modern = db.scalars(select(FutureSkillDemand)).all()
    result = []
    if modern:
        for row in modern:
            competency = db.get(Competency, row.competency_id)
            result.append({"competency_id": row.competency_id, "competency": competency.name if competency else "Unknown", "current_demand": row.current_demand, "projected_demand": row.projected_demand, "growth_rate": row.growth_rate, "priority": row.priority, "period": row.period, "source": row.source, "confidence": row.confidence, "affected_departments": row.affected_departments or []})
    else:
        for row in db.scalars(select(SkillForecast)).all():
            competency = db.get(Competency, row.competency_id)
            result.append({"competency_id": row.competency_id, "competency": competency.name if competency else "Unknown", "current_demand": row.current_demand, "projected_demand": row.projected_demand, "growth_rate": row.growth_rate, "priority": row.training_priority, "period": row.period, "source": row.source, "confidence": row.confidence, "affected_departments": row.affected_departments or []})
    return sorted(result, key=lambda row: row["projected_demand"], reverse=True)
