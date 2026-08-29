from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
    Competency,
    CompetencyScoreHistory,
)
from app.models import User
from app.core.language import localized_fields, normalize_language
from app.services.recommendations import refresh_recommendations
from app.services.skill_gaps import required_score, update_competency_from_assessment
from app.services.telemetry import build_event, record_event


def list_assessments(db: Session) -> list[dict]:
    rows = db.scalars(
        select(Assessment)
        .where(Assessment.is_published.is_(True))
        .order_by(Assessment.id)
    ).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "category": row.category,
            "question_count": len(row.competency_ids or []) * 2 if row.question_count == 0 else row.question_count,
            "competency_count": len(row.competency_ids or []),
        }
        for row in rows
    ]


def _question_rows(db: Session, assessment_id: int):
    return db.execute(
        select(AssessmentQuestion, Competency)
        .join(Competency, Competency.id == AssessmentQuestion.competency_id)
        .where(AssessmentQuestion.assessment_id == assessment_id)
        .order_by(AssessmentQuestion.id)
    ).all()


def _localized_question(question: AssessmentQuestion, language: str | None) -> tuple[list[str], str, str, str, bool]:
    requested = normalize_language(language)
    defaults = {"question": question.question, "explanation": question.explanation}
    fields, _, localized = localized_fields(question.localizations, requested, defaults)
    translations = question.localizations.get(requested, {}) if isinstance(question.localizations, dict) else {}
    options = translations.get("options") if isinstance(translations, dict) else None
    if not isinstance(options, list) or len(options) != len(question.options or []):
        options = question.options or []
        localized = False if requested == "hi" else localized
    return [str(item) for item in options], fields["question"], fields["explanation"], requested, localized


def _question_response(question: AssessmentQuestion, competency: Competency, language: str) -> dict:
    options, question_text, explanation, requested, localized = _localized_question(question, language)
    return {
        "id": question.id,
        "competency_id": question.competency_id,
        "competency": competency.name,
        "category": competency.category,
        "question": question_text,
        "options": options,
        "difficulty": question.difficulty,
        # The correct answer is intentionally not part of the question response.
        "explanation": explanation,
        "requested_language": requested,
        "localized": localized,
    }


def assessment_detail(db: Session, assessment_id: int, language: str = "en") -> dict:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None or not assessment.is_published:
        raise HTTPException(status_code=404, detail="Assessment not found")
    questions = _question_rows(db, assessment.id)
    return {
        "id": assessment.id,
        "title": assessment.title,
        "description": assessment.description,
        "category": assessment.category,
        "question_count": len(questions),
        "competency_count": len(assessment.competency_ids or []),
        "questions": [_question_response(question, competency, language) for question, competency in questions],
    }


def start_assessment(db: Session, user_id: int, assessment_id: int, language: str = "en") -> dict:
    normalized_language = normalize_language(language)
    detail = assessment_detail(db, assessment_id, normalized_language)
    attempt = AssessmentAttempt(
        assessment_id=assessment_id,
        user_id=user_id,
        status="started",
        language=normalized_language,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    learner = db.get(User, user_id)
    if learner:
        record_event(db, learner, build_event("ASSESSMENT_START", learner, object_data={"id": str(assessment_id), "type": "assessment"}, edata={"attempt_id": attempt.id}))
    return {"attempt_id": attempt.id, "assessment": detail, "started_at": attempt.created_at}


def _find_attempt(db: Session, attempt_id: int, user_id: int) -> AssessmentAttempt:
    attempt = db.scalar(
        select(AssessmentAttempt).where(
            AssessmentAttempt.id == attempt_id,
            AssessmentAttempt.user_id == user_id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    return attempt


def submit_assessment(db: Session, user, attempt_id: int, answers: list[dict]) -> dict:
    attempt = _find_attempt(db, attempt_id, user.id)
    if attempt.status == "completed":
        return get_assessment_result(db, user.id, attempt.id)

    question_rows = _question_rows(db, attempt.assessment_id)
    expected_ids = {question.id for question, _ in question_rows}
    try:
        answer_map = {int(item["question_id"]): str(item["answer"]) for item in answers}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Each answer must include a valid question_id and answer") from exc

    if len(answer_map) != len(answers):
        raise HTTPException(status_code=400, detail="A question may only be answered once")
    if expected_ids != set(answer_map):
        missing = len(expected_ids - set(answer_map))
        extra = len(set(answer_map) - expected_ids)
        detail = f"Answer every question before submitting ({len(expected_ids)} required)"
        if missing:
            detail += f"; {missing} missing"
        if extra:
            detail += f"; {extra} invalid"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    correct = 0
    category_totals: dict[str, list[int]] = {}
    competency_totals: dict[int, list[int]] = {}
    response_events: list[dict] = []
    for question, competency in question_rows:
        selected = answer_map[question.id]
        localized_options, _, _, _, _ = _localized_question(question, attempt.language)
        english_options = question.options or []
        if selected in localized_options:
            selected_index = localized_options.index(selected)
        elif selected in english_options:
            selected_index = english_options.index(selected)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid option for question {question.id}")
        correct_index = english_options.index(question.correct_answer) if question.correct_answer in english_options else -1
        is_correct = selected_index == correct_index
        correct += int(is_correct)
        category_totals.setdefault(competency.category, [0, 0])
        category_totals[competency.category][0] += int(is_correct)
        category_totals[competency.category][1] += 1
        competency_totals.setdefault(competency.id, [0, 0])
        competency_totals[competency.id][0] += int(is_correct)
        competency_totals[competency.id][1] += 1
        db.add(
            AssessmentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                answer=selected,
                is_correct=is_correct,
            )
        )
        response_events.append({
            "object_data": {"id": str(question.id), "type": "assessment_question"},
            "edata": {"attempt_id": attempt.id, "question_id": question.id, "competency_id": competency.id, "is_correct": is_correct},
        })

    percentage = round((correct / len(question_rows)) * 100 if question_rows else 0, 1)
    attempt.status = "completed"
    attempt.score = percentage
    attempt.completed_at = datetime.now(timezone.utc)
    db.flush()

    # Blend the new evidence with the baseline rather than overwriting history.
    competency_scores: dict[str, float] = {}
    for competency_id, (right, total) in competency_totals.items():
        assessment_score = round((right / total) * 100 if total else 0, 1)
        competency_scores[str(competency_id)] = assessment_score
        update_competency_from_assessment(db, user.id, competency_id, assessment_score, attempt.id)
    db.commit()
    for response_event in response_events:
        record_event(db, user, build_event("RESPONSE", user, object_data=response_event["object_data"], edata=response_event["edata"]))
    record_event(db, user, build_event("ASSESSMENT_END", user, object_data={"id": str(attempt.assessment_id), "type": "assessment"}, edata={"attempt_id": attempt.id, "score": percentage, "correct_answers": correct, "total_questions": len(question_rows), "competency_scores": competency_scores}))
    record_event(db, user, build_event("SKILL_PROFILE_UPDATE", user, object_data={"id": str(user.id), "type": "skill_profile"}, edata={"source": "assessment", "attempt_id": attempt.id, "competencies_updated": len(competency_totals)}))

    # The next read is already personalized: updated scores feed gaps and recommendations.
    refresh_recommendations(db, user)
    return get_assessment_result(db, user.id, attempt.id)


def get_assessment_result(db: Session, user_id: int, attempt_id: int) -> dict:
    attempt = _find_attempt(db, attempt_id, user_id)
    if attempt.status != "completed":
        raise HTTPException(status_code=409, detail="Assessment has not been submitted")
    assessment = db.get(Assessment, attempt.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    question_rows = _question_rows(db, assessment.id)
    stored_answers = {
        answer.question_id: answer
        for answer in db.scalars(
            select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt.id)
        ).all()
    }
    category_values: dict[str, list[int]] = {}
    competency_values: dict[int, list[int]] = {}
    answer_review = []
    for question, competency in question_rows:
        answer = stored_answers.get(question.id)
        correct_value = int(answer.is_correct) if answer else 0
        category_values.setdefault(competency.category, []).append(correct_value)
        competency_values.setdefault(competency.id, []).append(correct_value)
        display_options, _, localized_explanation, _, _ = _localized_question(question, attempt.language)
        correct_index = (question.options or []).index(question.correct_answer) if question.correct_answer in (question.options or []) else 0
        answer_review.append(
            {
                "question_id": question.id,
                "competency": competency.name,
                "selected_answer": answer.answer if answer else "",
                "correct_answer": display_options[correct_index] if correct_index < len(display_options) else question.correct_answer,
                "is_correct": bool(answer and answer.is_correct),
                "explanation": localized_explanation,
            }
        )

    histories = db.scalars(
        select(CompetencyScoreHistory)
        .where(CompetencyScoreHistory.assessment_attempt_id == attempt.id)
        .order_by(CompetencyScoreHistory.id)
    ).all()
    competency_results = []
    for history in histories:
        competency = db.get(Competency, history.competency_id)
        if competency is None:
            continue
        values = competency_values.get(history.competency_id, [0])
        assessed = round(sum(values) / len(values) * 100, 1)
        competency_results.append(
            {
                "competency_id": history.competency_id,
                "competency": competency.name,
                "category": competency.category,
                "previous_score": history.previous_score,
                "assessment_score": assessed,
                "updated_score": history.new_score,
                "delta": history.delta,
                "required_score": required_score(competency),
                "gap_after": round(max(0, required_score(competency) - history.new_score), 1),
            }
        )

    category_scores = {
        category: round(sum(values) / len(values) * 100, 1)
        for category, values in category_values.items()
    }
    strengths = [item["competency"] for item in competency_results if item["assessment_score"] >= 70]
    weaknesses = [item["competency"] for item in competency_results if item["assessment_score"] < 60]
    correct_answers = sum(1 for answer in stored_answers.values() if answer.is_correct)
    return {
        "attempt_id": attempt.id,
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "status": "completed",
        "overall_score": float(attempt.score or 0),
        "percentage": float(attempt.score or 0),
        "correct_answers": correct_answers,
        "incorrect_answers": len(question_rows) - correct_answers,
        "total_questions": len(question_rows),
        "category_scores": category_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "competency_results": competency_results,
        "answer_review": answer_review,
        "completed_at": attempt.completed_at,
    }
