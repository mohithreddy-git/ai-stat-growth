from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant import answer

router = APIRouter(prefix="/ai", tags=["assistant"])


@router.post("/chat", response_model=AssistantResponse)
def chat(payload: AssistantRequest, current_user: CurrentUser, db: DbSession):
    return answer(db, current_user, payload.message, payload.mode, payload.document_id, payload.top_k, payload.language)
