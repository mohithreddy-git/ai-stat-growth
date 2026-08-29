from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate_user, user_to_summary

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession):
    authenticated = authenticate_user(db, payload.email, payload.password)
    if authenticated is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token, user = authenticated
    return {"access_token": token, "token_type": "bearer", "user": user_to_summary(db, user)}
