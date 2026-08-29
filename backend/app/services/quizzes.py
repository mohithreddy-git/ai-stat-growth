from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import localized_fields, normalize_language
from app.models import AssessmentItem, Competency, CompetencyEvidence, PublishedQuiz, QuizAttempt, QuizItemAnswer, User
from app.services.recommendations import refresh_recommendations
from app.services.skill_gaps import update_competency_from_evidence


def _localized_item(item: AssessmentItem, language: str | None) -> tuple[str, list[str], str, bool]:
    requested = normalize_language(language)
    records = item.localizations if isinstance(item.localizations, dict) else {}
    translation = records.get(requested, {}) if isinstance(records.get(requested, {}), dict) else {}
    question = str(translation.get("question") or item.question)
    explanation = str(translation.get("explanation") or item.explanation)
    options = translation.get("options")
    localized = requested == "hi" and isinstance(options, list) and len(options) == len(item.options or []) and bool(translation.get("question"))
    return question, [str(option) for option in options] if localized else [str(option) for option in (item.options or [])], explanation, localized


def get_quiz(db: Session, quiz_id: int, language: str = "en") -> dict:
    quiz = db.get(PublishedQuiz, quiz_id)
    if quiz is None or quiz.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Published quiz not found")
    requested = normalize_language(language)
    items = db.scalars(select(AssessmentItem).where(AssessmentItem.id.in_(quiz.item_ids), AssessmentItem.status.in_(["APPROVED", "PUBLISHED"]))).all()
    return {"id": quiz.id, "title": quiz.title, "document_id": quiz.document_id, "status": quiz.status, "created_at": quiz.created_at, "requested_language": requested, "items": [{"id": item.id, "question": _localized_item(item, requested)[0], "options": _localized_item(item, requested)[1], "competency_id": item.competency_id, "topic": item.topic, "difficulty": item.difficulty, "source": item.source or {}, "localized": _localized_item(item, requested)[3]} for item in items]}


def submit_quiz(db: Session, user: User, quiz_id: int, answers: dict[int, int], language: str = "en") -> dict:
    quiz = db.get(PublishedQuiz, quiz_id)
    if quiz is None or quiz.status != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Published quiz not found")
    requested = normalize_language(language)
    items = db.scalars(select(AssessmentItem).where(AssessmentItem.id.in_(quiz.item_ids))).all()
    expected = {item.id for item in items}
    normalized = {int(key): int(value) for key, value in answers.items()}
    if set(normalized) != expected:
        raise HTTPException(status_code=400, detail="Answer every quiz question exactly once")
    attempt = QuizAttempt(user_id=user.id, published_quiz_id=quiz.id, document_id=quiz.document_id, language=requested)
    db.add(attempt); db.flush()
    correct = 0; topic_totals: dict[str, list[int]] = {}; explanations = []
    by_competency: dict[int, list[int]] = {}
    for item in items:
        selected = normalized[item.id]
        if selected not in range(4):
            raise HTTPException(status_code=400, detail=f"Invalid option for quiz item {item.id}")
        is_correct = selected == item.correct_index
        correct += int(is_correct)
        topic_totals.setdefault(item.topic, [0, 0]); topic_totals[item.topic][0] += int(is_correct); topic_totals[item.topic][1] += 1
        by_competency.setdefault(item.competency_id, [0, 0]); by_competency[item.competency_id][0] += int(is_correct); by_competency[item.competency_id][1] += 1
        db.add(QuizItemAnswer(quiz_attempt_id=attempt.id, assessment_item_id=item.id, selected_index=selected, is_correct=is_correct))
        _, _, localized_explanation, _ = _localized_item(item, requested)
        explanations.append({"item_id": item.id, "is_correct": is_correct, "correct_index": item.correct_index, "explanation": localized_explanation, "source": item.source or {}})
    score = round(correct / len(items) * 100 if items else 0, 1)
    attempt.score = score; attempt.topic_performance = {topic: round(values[0] / values[1] * 100, 1) for topic, values in topic_totals.items()}; attempt.completed_at = datetime.now(timezone.utc)
    db.flush()
    for competency_id, (right, total) in by_competency.items():
        score_for_competency = right / total * 100 if total else 0
        update_competency_from_evidence(db, user.id, competency_id, score_for_competency, "QUIZ", str(attempt.id), 0.75, {"quiz_id": quiz.id, "quiz_attempt_id": attempt.id})
    db.commit(); refresh_recommendations(db, user)
    return {"attempt_id": attempt.id, "quiz_id": quiz.id, "score": score, "correct_answers": correct, "total_questions": len(items), "topic_performance": attempt.topic_performance, "explanations": explanations, "requested_language": requested}
