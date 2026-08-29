from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.core.language import normalize_language
from app.models import AssessmentAttempt, Competency, Course, Department, LearningProgress, Role, TrainingProgramme, User
from app.schemas.employee import (
    CompetencyDomainSummaryResponse,
    CompetencyProfileResponse,
    EmployeeDashboardResponse,
    EmployeeProfileResponse,
    LearningProgressResponse,
    LearningProgressUpsertRequest,
    LearningResourceResponse,
    SkillGapResponse,
)
from app.schemas.intelligence import CompetencyEvidenceResponse, CompetencyVectorResponse, FRACProfileResponse
from app.services.auth import user_to_summary
from app.services.learning import list_learning_progress, upsert_learning_progress
from app.services.recommendations import refresh_recommendations
from app.services.skill_gaps import calculate_skill_gaps, competency_domain_summary, get_competency_profile
from app.services.intelligence import competency_vector, evidence_for_employee, frac_profile

router = APIRouter(prefix="/users", tags=["employee intelligence"])


def _target_user(db: Session, current_user: User, user_id: int) -> User:
    role = db.get(Role, current_user.role_id)
    if current_user.id != user_id and (role is None or role.name != "ADMIN"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only access your own employee data")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    return target


def _profile(db: Session, user: User) -> dict:
    role = db.get(Role, user.role_id)
    department = db.get(Department, user.department_id)
    frac = frac_profile(db, user)
    previous_trainings = []
    progress_rows = db.scalars(select(LearningProgress).where(
        LearningProgress.user_id == user.id,
        LearningProgress.status == "completed",
    ).order_by(LearningProgress.id)).all()
    for item in progress_rows:
        resource = db.get(Course if item.resource_type == "course" else TrainingProgramme, item.resource_id)
        if resource:
            previous_trainings.append(resource.title if item.resource_type == "course" else resource.programme_name)
    return {
        **user_to_summary(db, user),
        "department": department.name if department else "Unknown department",
        "educational_qualification": user.educational_qualification,
        "previous_trainings": previous_trainings,
        "role": role.name if role else "UNKNOWN",
        "position": frac.get("position"),
        "frac_role": frac.get("role"),
        "frac_activities": sorted({item["activity"] for item in frac.get("activities", [])}),
    }


def _latest_assessment(db: Session, user_id: int) -> AssessmentAttempt | None:
    return db.scalar(select(AssessmentAttempt).where(
        AssessmentAttempt.user_id == user_id,
        AssessmentAttempt.status == "completed",
    ).order_by(AssessmentAttempt.id.desc()))


@router.get("/{user_id}", response_model=EmployeeProfileResponse)
def get_employee_profile(user_id: int, current_user: CurrentUser, db: DbSession):
    return _profile(db, _target_user(db, current_user, user_id))


@router.get("/{user_id}/competencies", response_model=CompetencyProfileResponse)
def get_employee_competencies(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return get_competency_profile(db, target)


@router.get("/{user_id}/competency-domain-summary", response_model=CompetencyDomainSummaryResponse)
def get_employee_competency_domain_summary(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return competency_domain_summary(db, target)


@router.get("/{user_id}/frac-profile", response_model=FRACProfileResponse)
def get_employee_frac_profile(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return frac_profile(db, target)


@router.get("/{user_id}/competency-vector", response_model=CompetencyVectorResponse)
def get_employee_competency_vector(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return competency_vector(db, target)


@router.get("/{user_id}/evidence", response_model=list[CompetencyEvidenceResponse])
def get_employee_evidence(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return evidence_for_employee(db, target.id)


@router.get("/{user_id}/skill-gaps", response_model=list[SkillGapResponse])
def get_employee_skill_gaps(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return calculate_skill_gaps(db, target)


@router.get("/{user_id}/recommendations", response_model=list[LearningResourceResponse])
def get_employee_recommendations(user_id: int, current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    target = _target_user(db, current_user, user_id)
    return refresh_recommendations(db, target, normalize_language(language))


@router.get("/{user_id}/learning-progress", response_model=list[LearningProgressResponse])
def get_employee_learning_progress(user_id: int, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return list_learning_progress(db, target)


@router.post("/{user_id}/learning-progress", response_model=LearningProgressResponse)
def save_employee_learning_progress(user_id: int, payload: LearningProgressUpsertRequest, current_user: CurrentUser, db: DbSession):
    target = _target_user(db, current_user, user_id)
    return upsert_learning_progress(db, target, payload.model_dump())


@router.get("/{user_id}/dashboard", response_model=EmployeeDashboardResponse)
def get_employee_dashboard(user_id: int, current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    target = _target_user(db, current_user, user_id)
    profile = _profile(db, target)
    competency = get_competency_profile(db, target)
    gaps = calculate_skill_gaps(db, target)
    recommendations = refresh_recommendations(db, target, normalize_language(language))
    progress = list_learning_progress(db, target)
    latest = _latest_assessment(db, target.id)
    return {
        "profile": profile,
        "competency": competency,
        "skill_gaps": gaps,
        "recommendations": recommendations,
        "learning_progress": progress,
        "learning_hours": round(sum(item["learning_hours"] for item in progress), 1),
        "completed_courses": sum(1 for item in progress if item["status"] == "completed"),
        "assessment_score": latest.score if latest else None,
        "recent_assessment_id": latest.id if latest else None,
    }


@router.get("/framework/all", response_model=list[dict])
def list_competency_framework(current_user: CurrentUser, db: DbSession):
    rows = db.scalars(select(Competency).order_by(Competency.category, Competency.name)).all()
    return [{
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "category": row.category,
        "description": row.description,
        "beginner_definition": row.beginner_definition,
        "intermediate_definition": row.intermediate_definition,
        "advanced_definition": row.advanced_definition,
        "required_level": row.required_level,
        "required_score": {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}.get(row.required_level, 60),
        "weight": row.weight,
    } for row in rows]
