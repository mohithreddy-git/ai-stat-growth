from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import UserSummary
from app.services.auth import user_to_summary

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSummary)
def get_me(current_user: CurrentUser, db: DbSession):
    return user_to_summary(db, current_user)
