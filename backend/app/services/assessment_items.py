from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers import ProviderError, get_llm_provider
from app.ai.quality import GeneratedMCQ, QuestionQualityValidator
from app.models import AssessmentItem, AssessmentItemReview, AuditLog, Competency, DocumentChunk, Role, UploadedDocument, User
from app.schemas.intelligence import AssessmentItemGenerateRequest
from app.services.documents import retrieve_chunks


def _item_response(item: AssessmentItem) -> dict[str, Any]:
    return {"id": item.id, "document_id": item.document_id, "question": item.question, "options": item.options, "correct_index": item.correct_index, "explanation": item.explanation, "competency_id": item.competency_id, "topic": item.topic, "difficulty": item.difficulty, "source": item.source or {}, "status": item.status, "confidence": item.confidence, "generated_by": item.generated_by, "created_at": item.created_at}


def _source_text(source: dict[str, Any]) -> str:
    return str(source.get("source_text", ""))


def _fallback_candidate(competency: Competency, chunk: DocumentChunk, topic: str, difficulty: str, index: int) -> GeneratedMCQ:
    answer = chunk.text[:320].strip()
    stems = [
        "Which statement is directly supported by the uploaded material",
        "Which claim is explicitly present in the uploaded material",
        "Which point can be verified from the uploaded material",
        "Which description matches the uploaded source section",
        "Which practice is identified in the uploaded source",
    ]
    source = {"document_id": chunk.document_id, "chunk_id": chunk.chunk_id, "page_number": chunk.page_number, "slide_number": chunk.slide_number, "section": chunk.section, "source_text": chunk.text}
    return GeneratedMCQ(
        question=f"{stems[index % len(stems)]} on {topic} (item {index + 1})?",
        options=[answer, "This statement is not present in the uploaded source.", "The source leaves this point unspecified.", "The uploaded source presents a different conclusion."],
        correct_index=0,
        explanation=f"The first option is supported by source chunk {chunk.chunk_id}; the other options are not claims established by this excerpt.",
        competency_id=competency.id, topic=topic, difficulty=difficulty, source=source,
    )


def _provider_candidate(provider, competency: Competency, chunk: DocumentChunk, topic: str, difficulty: str, language: str) -> GeneratedMCQ | None:
    if getattr(provider, "name", "mock") == "mock":
        return None
    source = {"document_id": chunk.document_id, "chunk_id": chunk.chunk_id, "page_number": chunk.page_number, "slide_number": chunk.slide_number, "section": chunk.section, "source_text": chunk.text}
    system = (
        "Generate exactly one MCQ as a JSON object. Use only the supplied source context; do not invent facts or use unsupported world knowledge. "
        "Return four unique options, exactly one correct answer, a concise explanation, and the requested difficulty."
    )
    prompt = (
        f"Language: {language}. Topic: {topic}. Difficulty: {difficulty}. Competency id: {competency.id}.\n"
        f"Source provenance: {source}\n\nSource context:\n{chunk.text}\n\n"
        "Return fields question, options, correct_index, explanation, competency_id, topic, difficulty, and source."
    )
    try:
        candidate = asyncio.run(provider.generate_structured(prompt, GeneratedMCQ, system=system))
        # Provenance and competency are server-owned facts, never trusted from
        # model output even when the remaining fields validate.
        return GeneratedMCQ.model_validate({**candidate.model_dump(), "competency_id": competency.id, "topic": topic, "difficulty": difficulty, "source": source})
    except (ProviderError, ValueError, TypeError):
        return None


def generate_items(db: Session, user: User, request: AssessmentItemGenerateRequest) -> list[dict]:
    if request.document_id is None:
        raise HTTPException(status_code=422, detail="document_id is required for source-grounded generation")
    document = db.get(UploadedDocument, request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    role = db.get(Role, user.role_id)
    if document.uploaded_by != user.id and (not role or role.name != "ADMIN"):
        raise HTTPException(status_code=403, detail="You may only generate from your own documents")
    if document.status != "processed":
        raise HTTPException(status_code=409, detail="Process the document before generating assessment items")
    competency_id = request.competency_id or db.scalar(select(Competency.id).order_by(Competency.id))
    competency = db.get(Competency, competency_id)
    if competency is None:
        raise HTTPException(status_code=404, detail="Competency not found")
    chunks = retrieve_chunks(db, document.id, request.topic, limit=max(1, request.count))
    if not chunks:
        # Topic is an optional authoring hint, not permission to abandon a
        # valid source. If it has no match, generate from the processed source
        # chunks in document order; every question still carries provenance and
        # is validated against that source text.
        chunks = db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.id)
            .limit(max(1, request.count))
        ).all()
    if not chunks:
        raise HTTPException(status_code=422, detail="No source chunks are available for generation")
    existing = [item.question for item in db.scalars(select(AssessmentItem).where(AssessmentItem.document_id == document.id)).all()]
    provider = get_llm_provider()
    generated: list[dict] = []
    for index in range(request.count):
        chunk = chunks[index % len(chunks)]
        if len(chunk.text.strip()) < 8:
            continue
        difficulty = ["easy", "medium", "hard"][index % 3] if request.difficulty == "mixed" else request.difficulty
        candidate = _provider_candidate(provider, competency, chunk, request.topic, difficulty, request.language)
        generated_by = getattr(provider, "name", "mock") if candidate else "mock"
        if candidate is None:
            candidate = _fallback_candidate(competency, chunk, request.topic, difficulty, index)
        quality = QuestionQualityValidator.validate(candidate, chunk.text, existing + [item["question"] for item in generated])
        if not quality.valid:
            continue
        item = AssessmentItem(document_id=document.id, competency_id=competency.id, question=candidate.question, options=candidate.options, correct_index=candidate.correct_index, explanation=candidate.explanation, topic=candidate.topic, difficulty=candidate.difficulty, source=candidate.source, status="GENERATED", confidence=quality.confidence, generated_by=generated_by)
        db.add(item); db.flush()
        # Keep the externally visible queue state compatible with Phase 2 while
        # preserving the complete state machine in the review/audit ledger.
        _write_review(db, item, user, "GENERATED", "Generated from processed source context")
        item.status = "VALIDATED"
        _write_review(db, item, user, "VALIDATED", "Passed schema and source-quality validation")
        item.status = "PENDING_REVIEW"
        _write_review(db, item, user, "PENDING_REVIEW", "Queued for human review")
        generated.append(_item_response(item)); existing.append(item.question)
    if not generated:
        raise HTTPException(status_code=422, detail="No valid questions could be generated from the source")
    db.commit()
    return generated


def review_queue(db: Session) -> list[dict]:
    rows = db.scalars(select(AssessmentItem).where(AssessmentItem.status.in_(["PENDING_REVIEW", "VALIDATED", "GENERATED"])).order_by(AssessmentItem.id)).all()
    return [_item_response(row) for row in rows]


def get_item(db: Session, item_id: int) -> AssessmentItem:
    item = db.get(AssessmentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Assessment item not found")
    return item


def _write_review(db: Session, item: AssessmentItem, reviewer: User, action: str, note: str = "", payload: dict | None = None) -> None:
    db.add(AssessmentItemReview(assessment_item_id=item.id, reviewer_id=reviewer.id, action=action, note=note, payload=payload or {}))
    db.add(AuditLog(user_id=reviewer.id, action=f"assessment_item_{action.lower()}", resource_type="assessment_item", resource_id=str(item.id), metadata_json={"note": note}))


def review_action(db: Session, item_id: int, reviewer: User, action: str, note: str = "") -> dict:
    item = get_item(db, item_id)
    if action == "approve":
        if item.status not in {"PENDING_REVIEW", "VALIDATED"}:
            raise HTTPException(status_code=409, detail="Only validated pending items can be approved")
        item.status = "APPROVED"
    elif action == "reject":
        if item.status not in {"GENERATED", "VALIDATED", "PENDING_REVIEW"}:
            raise HTTPException(status_code=409, detail="Only unapproved review items can be rejected")
        item.status = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Unsupported review action")
    _write_review(db, item, reviewer, action.upper(), note)
    db.commit(); db.refresh(item)
    return _item_response(item)


def edit_item(db: Session, item_id: int, reviewer: User, payload: dict) -> dict:
    item = get_item(db, item_id)
    if item.status == "PUBLISHED":
        raise HTTPException(status_code=409, detail="Published assessment items are immutable")
    values = {key: value for key, value in payload.items() if value is not None}
    if "competency_id" in values and db.get(Competency, values["competency_id"]) is None:
        raise HTTPException(status_code=404, detail="Competency not found")
    merged = {"question": values.get("question", item.question), "options": values.get("options", item.options), "correct_index": values.get("correct_index", item.correct_index), "explanation": values.get("explanation", item.explanation), "competency_id": values.get("competency_id", item.competency_id), "topic": values.get("topic", item.topic), "difficulty": values.get("difficulty", item.difficulty), "source": item.source or {}}
    candidate = GeneratedMCQ(**merged)
    quality = QuestionQualityValidator.validate(candidate, _source_text(item.source or {}), [row.question for row in db.scalars(select(AssessmentItem).where(AssessmentItem.id != item.id)).all()])
    if not quality.valid:
        raise HTTPException(status_code=422, detail={"message": "Edited item failed quality validation", "reasons": quality.reasons})
    item.question = candidate.question; item.options = candidate.options; item.correct_index = candidate.correct_index; item.explanation = candidate.explanation; item.competency_id = candidate.competency_id; item.topic = candidate.topic; item.difficulty = candidate.difficulty; item.confidence = quality.confidence
    _write_review(db, item, reviewer, "EDIT", payload)
    item.status = "VALIDATED"
    _write_review(db, item, reviewer, "VALIDATED", "Edited item passed schema and source-quality validation")
    item.status = "PENDING_REVIEW"
    _write_review(db, item, reviewer, "PENDING_REVIEW", "Edited item requeued for human review")
    db.commit(); db.refresh(item)
    return _item_response(item)


def publish_quiz(db: Session, user: User, title: str, item_ids: list[int], document_id: int | None = None) -> dict:
    from app.models import PublishedQuiz
    if len(set(item_ids)) != len(item_ids):
        raise HTTPException(status_code=422, detail="Each assessment item may appear only once")
    items = [get_item(db, item_id) for item_id in item_ids]
    if any(item.status != "APPROVED" for item in items):
        raise HTTPException(status_code=409, detail="Only approved assessment items can be published")
    quiz = PublishedQuiz(title=title, document_id=document_id, item_ids=item_ids, created_by=user.id, status="PUBLISHED")
    for item in items:
        item.status = "PUBLISHED"
    db.add(quiz)
    db.add(AuditLog(user_id=user.id, action="quiz_published", resource_type="quiz", metadata_json={"item_ids": item_ids}))
    db.commit(); db.refresh(quiz)
    return {"id": quiz.id, "title": quiz.title, "document_id": quiz.document_id, "item_ids": quiz.item_ids, "status": quiz.status, "created_at": quiz.created_at}
