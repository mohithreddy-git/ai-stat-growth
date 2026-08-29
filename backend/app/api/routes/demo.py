from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.models import User
from app.schemas.admin import DemoResetResponse
from app.services.demo import reset_demo_database

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset", response_model=DemoResetResponse)
def reset(db: DbSession, current_user: User = Depends(require_roles("ADMIN"))):
    return reset_demo_database(db)
