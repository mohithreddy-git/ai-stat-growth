from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import Assessment, Competency, Course, Department, SkillForecast, TrainingProgramme, User
from app.schemas.auth import BootstrapResponse

router = APIRouter(prefix="/bootstrap", tags=["application"])


@router.get("", response_model=BootstrapResponse)
def bootstrap(current_user: CurrentUser, db: DbSession):
    settings = get_settings()
    counts = {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "departments": db.scalar(select(func.count()).select_from(Department)) or 0,
        "competencies": db.scalar(select(func.count()).select_from(Competency)) or 0,
        "courses": db.scalar(select(func.count()).select_from(Course)) or 0,
        "training_programmes": db.scalar(select(func.count()).select_from(TrainingProgramme)) or 0,
        "assessments": db.scalar(select(func.count()).select_from(Assessment)) or 0,
        "skill_forecasts": db.scalar(select(func.count()).select_from(SkillForecast)) or 0,
    }
    return {
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "phase": "Phase 4 · SIH competition-ready prototype",
        "ai_provider": settings.llm_provider,
        "demo_mode": settings.demo_mode and settings.app_env.lower() in {"development", "demo", "test"},
        "seeded_counts": counts,
        "planned_modules": [
            "Government SSO and production identity integration",
            "Authenticated iGOT and NSSTA/TPAC connectors",
            "Official FRAC catalogue ingestion and governance",
            "Durable background workers and production observability",
        ],
    }
