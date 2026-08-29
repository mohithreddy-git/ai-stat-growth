from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import Role, UploadedDocument, User
from app.schemas.intelligence import AssessmentItemGenerateRequest, AssessmentItemResponse, ReviewActionRequest
from app.schemas.studio import DocumentResponse, EditAssessmentItemRequest, QuizGenerateRequest, QuizPublishRequest, QuizResponse, QuizResultResponse, QuizSubmitRequest
from app.services.assessment_items import _item_response, edit_item, generate_items, get_item, publish_quiz, review_action, review_queue
from app.services.documents import list_documents, process_document, save_upload
from app.services.quizzes import get_quiz, submit_quiz
from app.services.telemetry import build_event, record_event

router = APIRouter(tags=["assessment studio"])


def _document_for_user(db, document_id: int, user: User):
    document = db.get(UploadedDocument, document_id)
    if document is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Document not found")
    role = db.get(Role, user.role_id)
    if document.uploaded_by != user.id and (not role or role.name != "ADMIN"):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only process your own documents")
    return document


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(db: DbSession, upload: UploadFile = File(...), current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    document = await save_upload(db, current_user.id, upload)
    record_event(
        db,
        current_user,
        build_event(
            "DOCUMENT_UPLOAD",
            current_user,
            object_data={"id": f"document:{document.id}", "type": "document"},
            edata={"filename": document.filename, "content_type": document.content_type, "size_bytes": document.size_bytes},
        ),
    )
    return list_documents(db, current_user.id)[0]


@router.get("/documents", response_model=list[DocumentResponse])
def documents(current_user: CurrentUser, db: DbSession):
    rows = list_documents(db, current_user.id)
    return rows


@router.post("/documents/{document_id}/process", response_model=DocumentResponse)
def process(document_id: int, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    _document_for_user(db, document_id, current_user)
    document = process_document(db, document_id)
    return next(row for row in list_documents(db) if row["id"] == document.id)


@router.post("/assessment-items/generate", response_model=list[AssessmentItemResponse])
def generate_assessment_items(payload: AssessmentItemGenerateRequest, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return generate_items(db, current_user, payload)


@router.get("/assessment-items/review-queue", response_model=list[AssessmentItemResponse])
def assessment_review_queue(db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return review_queue(db)


@router.get("/assessment-items/{item_id}", response_model=AssessmentItemResponse)
def assessment_item(item_id: int, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return _item_response(get_item(db, item_id))


@router.post("/assessment-items/{item_id}/approve", response_model=AssessmentItemResponse)
def approve_item(item_id: int, db: DbSession, payload: ReviewActionRequest | None = None, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return review_action(db, item_id, current_user, "approve", payload.note if payload else "")


@router.post("/assessment-items/{item_id}/reject", response_model=AssessmentItemResponse)
def reject_item(item_id: int, db: DbSession, payload: ReviewActionRequest | None = None, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return review_action(db, item_id, current_user, "reject", payload.note if payload else "")


@router.post("/assessment-items/{item_id}/edit", response_model=AssessmentItemResponse)
def edit_assessment_item(item_id: int, payload: EditAssessmentItemRequest, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return edit_item(db, item_id, current_user, payload.model_dump(exclude_none=True))


@router.post("/quizzes/generate", response_model=list[AssessmentItemResponse])
def generate_quiz(payload: QuizGenerateRequest, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    request = AssessmentItemGenerateRequest(document_id=payload.document_id, competency_id=payload.competency_id, topic=payload.topic, difficulty=payload.difficulty, count=payload.count, language=payload.language)
    return generate_items(db, current_user, request)


@router.post("/quizzes/publish", response_model=QuizResponse)
def publish(payload: QuizPublishRequest, db: DbSession, current_user: User = Depends(require_roles("TRAINER", "ADMIN"))):
    return publish_quiz(db, current_user, payload.title, payload.item_ids)


@router.get("/quizzes/{quiz_id}")
def quiz(quiz_id: int, current_user: CurrentUser, db: DbSession, language: str = Query(default="en", min_length=2, max_length=8)):
    result = get_quiz(db, quiz_id, language)
    record_event(
        db,
        current_user,
        build_event(
            "CONTENT_VIEW",
            current_user,
            object_data={"id": f"quiz:{quiz_id}", "type": "quiz"},
            edata={"item_count": len(result.get("items", []))},
        ),
    )
    return result


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizResultResponse)
def submit(quiz_id: int, payload: QuizSubmitRequest, current_user: CurrentUser, db: DbSession):
    return submit_quiz(db, current_user, quiz_id, payload.answers, payload.language)
