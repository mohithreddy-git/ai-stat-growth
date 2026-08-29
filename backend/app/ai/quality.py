from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GeneratedMCQ(BaseModel):
    question: str = Field(min_length=8, max_length=2000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=4, max_length=3000)
    competency_id: int = Field(gt=0)
    topic: str = Field(min_length=1, max_length=160)
    difficulty: Literal["easy", "medium", "hard"]
    source: dict[str, Any] = Field(min_length=1)

    @model_validator(mode="after")
    def provenance_is_present(self) -> "GeneratedMCQ":
        if not str(self.source.get("document_id", "")).strip() or not str(self.source.get("chunk_id", "")).strip():
            raise ValueError("source must include document_id and chunk_id")
        return self

    @field_validator("options")
    @classmethod
    def options_are_unique(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if len(cleaned) != 4 or any(not value for value in cleaned) or len({value.casefold() for value in cleaned}) != 4:
            raise ValueError("A question requires four unique non-empty options")
        return cleaned


@dataclass
class QualityResult:
    valid: bool
    reasons: list[str]
    confidence: float


class QuestionQualityValidator:
    allowed_difficulties = {"easy", "medium", "hard"}

    @staticmethod
    def validate(
        item: GeneratedMCQ,
        source_text: str,
        existing_questions: list[str] | None = None,
        known_competency_ids: set[int] | None = None,
    ) -> QualityResult:
        """Validate both normal Pydantic instances and hostile/raw model output.

        ``model_construct`` and provider adapters can bypass normal Pydantic
        validation, so this boundary must never raise ``IndexError`` or
        ``AttributeError`` while deciding whether an item is publishable.
        """
        reasons: list[str] = []
        options = getattr(item, "options", None)
        question = str(getattr(item, "question", "") or "").strip()
        explanation = str(getattr(item, "explanation", "") or "").strip()
        source = getattr(item, "source", None)
        correct_index = getattr(item, "correct_index", None)
        difficulty = str(getattr(item, "difficulty", "") or "").casefold()
        competency_id = getattr(item, "competency_id", None)

        if not isinstance(options, list) or len(options) != 4:
            reasons.append("exactly four options are required")
            normalized_options: list[str] = []
        else:
            normalized_options = [str(value or "").strip() for value in options]
            if any(not value for value in normalized_options):
                reasons.append("options must be non-empty")
            if len({value.casefold() for value in normalized_options}) != 4:
                reasons.append("options must be unique")
        valid_index = isinstance(correct_index, int) and not isinstance(correct_index, bool) and correct_index in range(4)
        if not valid_index:
            reasons.append("correct_index must be between 0 and 3")
        if difficulty not in QuestionQualityValidator.allowed_difficulties:
            reasons.append("difficulty must be easy, medium, or hard")
        if not isinstance(source, dict) or not str(source.get("document_id", "")).strip() or not str(source.get("chunk_id", "")).strip():
            reasons.append("source provenance is incomplete")
            source = {}
        if known_competency_ids is not None and competency_id not in known_competency_ids:
            reasons.append("competency does not exist")
        if not question:
            reasons.append("question is empty")
        if not source_text or not source_text.strip():
            reasons.append("source text is empty")

        correct_answer = normalized_options[correct_index] if valid_index and len(normalized_options) == 4 else ""
        source_lower = source_text.casefold() if isinstance(source_text, str) else ""
        source_terms = set(re.findall(r"[a-z0-9]{4,}", source_lower))
        question_terms = set(re.findall(r"[a-z0-9]{4,}", question.casefold()))
        if source_terms and not (source_terms & question_terms or correct_answer.casefold() in source_lower):
            reasons.append("question is not supported by the source context")
        if valid_index and correct_answer and correct_answer.casefold() not in source_lower:
            reasons.append("correct answer is not traceable to source context")
        normalized = re.sub(r"\W+", " ", question.casefold()).strip()
        if normalized and any(normalized == re.sub(r"\W+", " ", str(candidate).casefold()).strip() for candidate in (existing_questions or [])):
            reasons.append("duplicate question")
        if correct_answer and correct_answer.casefold() in question.casefold():
            reasons.append("answer leakage in question")
        if re.search(r"\b(all of the above|none of the above|both a and b)\b", question.casefold()):
            reasons.append("ambiguous answer pattern")
        if not explanation:
            reasons.append("explanation is empty")
        return QualityResult(valid=not reasons, reasons=reasons, confidence=0.92 if not reasons else 0.0)
