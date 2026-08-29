from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.language import localized_fields, normalize_language
from app.models import Assessment, Competency, Course, TrainingProgramme
from app.schemas.assessment import (
    AssessmentDetailResponse,
    AssessmentResultResponse,
    AssessmentStartRequest,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentSummaryResponse,
)
from app.schemas.employee import CompetencyResponse
from app.schemas.resources import CourseResponse, TrainingProgrammeResponse
from app.services.assessments import assessment_detail, get_assessment_result, list_assessments, start_assessment, submit_assessment

router = APIRouter(tags=["learning foundation"])


@router.get("/assessments", response_model=list[AssessmentSummaryResponse])
def get_assessments(current_user: CurrentUser, db: DbSession):
    return list_assessments(db)


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(assessment_id: int, current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    return assessment_detail(db, assessment_id, normalize_language(language))


@router.post("/assessments/start", response_model=AssessmentStartResponse)
def begin_assessment(payload: AssessmentStartRequest, current_user: CurrentUser, db: DbSession):
    return start_assessment(db, current_user.id, payload.assessment_id, normalize_language(payload.language))


@router.post("/assessments/{attempt_id}/submit", response_model=AssessmentResultResponse)
def submit_assessment_attempt(attempt_id: int, payload: AssessmentSubmitRequest, current_user: CurrentUser, db: DbSession):
    return submit_assessment(db, current_user, attempt_id, [answer.model_dump() for answer in payload.answers])


@router.get("/assessments/{attempt_id}/result", response_model=AssessmentResultResponse)
def get_assessment_attempt_result(attempt_id: int, current_user: CurrentUser, db: DbSession):
    return get_assessment_result(db, current_user.id, attempt_id)


@router.get("/competencies", response_model=list[CompetencyResponse])
def get_competencies(current_user: CurrentUser, db: DbSession):
    rows = db.scalars(select(Competency).order_by(Competency.category, Competency.name)).all()
    return [{
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "category": row.category,
        "competency_type": row.competency_type,
        "description": row.description,
        "beginner_definition": row.beginner_definition,
        "intermediate_definition": row.intermediate_definition,
        "advanced_definition": row.advanced_definition,
        "required_level": row.required_level,
        "required_score": {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}.get(row.required_level, 60),
        "weight": row.weight,
    } for row in rows]


@router.get("/courses", response_model=list[CourseResponse])
def get_courses(current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    requested = normalize_language(language)
    rows = db.scalars(select(Course).order_by(Course.id)).all()
    response = []
    for row in rows:
        localized, _, fully_localized = localized_fields(row.localizations, requested, {"title": row.title, "description": row.description})
        records = row.localizations if isinstance(row.localizations, dict) else {}
        english = records.get("en") if isinstance(records.get("en"), dict) else {}
        hindi = records.get("hi") if isinstance(records.get("hi"), dict) else {}
        response.append({
            "id": row.id,
            "course_id": row.course_id,
            "title": localized["title"],
            "description": localized["description"],
            "source": row.source,
            "duration_hours": row.duration_hours,
            "difficulty": row.difficulty,
            "language": row.language,
            "requested_language": requested,
            "localized": fully_localized,
            "localization_label": records.get("label"),
            "title_en": english.get("title") or row.title,
            "title_hi": hindi.get("title"),
            "description_en": english.get("description") or row.description,
            "description_hi": hindi.get("description"),
            "skills": row.skills or [],
            "competency_ids": row.competency_ids or [],
            "role_tags": row.role_tags or [],
            "department_tags": row.department_tags or [],
            "url": row.url,
            "completion_status": row.completion_status or "not_started",
            "is_prototype": row.is_prototype,
        })
    return response


@router.get("/training-programmes", response_model=list[TrainingProgrammeResponse])
def get_training_programmes(current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    requested = normalize_language(language)
    rows = db.scalars(select(TrainingProgramme).order_by(TrainingProgramme.id)).all()
    response = []
    for row in rows:
        localized, _, fully_localized = localized_fields(row.localizations, requested, {"title": row.programme_name, "description": row.description})
        records = row.localizations if isinstance(row.localizations, dict) else {}
        english = records.get("en") if isinstance(records.get("en"), dict) else {}
        hindi = records.get("hi") if isinstance(records.get("hi"), dict) else {}
        response.append({
            "id": row.id,
            "programme_id": row.programme_id,
            "programme_name": localized["title"],
            "description": localized["description"],
            "category": row.category,
            "duration_days": row.duration_days,
            "target_group": row.target_group,
            "requested_language": requested,
            "localized": fully_localized,
            "localization_label": records.get("label"),
            "title_en": english.get("title") or row.programme_name,
            "title_hi": hindi.get("title"),
            "description_en": english.get("description") or row.description,
            "description_hi": hindi.get("description"),
            "competency_ids": row.competency_ids or [],
            "role_tags": row.role_tags or [],
            "recommended_for": row.recommended_for or [],
            "schedule": row.schedule,
            "url": row.url,
            "source": row.source,
            "is_prototype": row.is_prototype,
        })
    return response
