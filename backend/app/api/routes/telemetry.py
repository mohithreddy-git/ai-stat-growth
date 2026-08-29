from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import Role, User
from app.schemas.intelligence import SkillProfileMetricResponse, TelemetryAcceptedResponse, TelemetryBatchRequest, TelemetryEnvelope, VelocityResponse
from app.schemas.studio import OrganizationSummaryResponse
from app.services.telemetry import list_events, organization_summary, recent_events, record_batch, record_event, skill_profile, velocity

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _can_read_user(db: Session, current_user: User, user_id: int) -> None:
    role = db.get(Role, current_user.role_id)
    if current_user.id != user_id and (not role or role.name != "ADMIN"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only access your own telemetry")


@router.post("/events", response_model=TelemetryAcceptedResponse)
def create_event(payload: TelemetryEnvelope, current_user: CurrentUser, db: DbSession):
    return record_event(db, current_user, payload.model_dump())


@router.post("/batch", response_model=list[TelemetryAcceptedResponse])
def create_batch(payload: TelemetryBatchRequest, current_user: CurrentUser, db: DbSession):
    return record_batch(db, current_user, [event.model_dump() for event in payload.events])


@router.get("/events/{user_id}")
def events(user_id: int, current_user: CurrentUser, db: DbSession):
    _can_read_user(db, current_user, user_id)
    return list_events(db, current_user, user_id)


@router.get("/learner/{user_id}/velocity", response_model=VelocityResponse)
def learner_velocity(user_id: int, current_user: CurrentUser, db: DbSession):
    _can_read_user(db, current_user, user_id)
    return velocity(db, user_id)


@router.get("/learner/{user_id}/skill-profile", response_model=list[SkillProfileMetricResponse])
def learner_skill_profile(user_id: int, current_user: CurrentUser, db: DbSession):
    _can_read_user(db, current_user, user_id)
    return skill_profile(db, user_id)


@router.get("/organization/summary", response_model=OrganizationSummaryResponse)
def organization_telemetry_summary(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return organization_summary(db)


@router.get("/organization/recent")
def organization_recent_telemetry(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return recent_events(db)
