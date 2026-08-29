from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.models import User
from app.schemas.admin import AdminOverviewResponse, DepartmentIntelligenceResponse, ForecastResponse, GapAggregateResponse, TrainingEffectivenessResponse
from app.services.admin_intelligence import departments, forecast, overview, skill_gaps, training_effectiveness

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/access-check")
def access_check(current_user: User = Depends(require_roles("ADMIN"))):
    return {"status": "ok", "message": "Admin route is protected", "user": current_user.employee_id}


@router.get("/workforce-access-check")
def workforce_access_check(current_user: User = Depends(require_roles("ADMIN"))):
    return {"status": "ok", "message": "Workforce analytics boundary is ready", "user": current_user.employee_id}


@router.get("/trainer-access-check")
def trainer_access_check(current_user: User = Depends(require_roles("TRAINER"))):
    return {"status": "ok", "message": "Trainer route is not exposed to employees", "user": current_user.employee_id}


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return overview(db)


@router.get("/departments", response_model=list[DepartmentIntelligenceResponse])
def admin_departments(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return departments(db)


@router.get("/skill-gaps", response_model=list[GapAggregateResponse])
def admin_skill_gaps(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return skill_gaps(db)


@router.get("/training-effectiveness", response_model=list[TrainingEffectivenessResponse])
def admin_training_effectiveness(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return training_effectiveness(db)


@router.get("/forecast", response_model=list[ForecastResponse])
def admin_forecast(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return forecast(db)

