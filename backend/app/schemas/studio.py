from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime
    chunk_count: int = 0
    processing_error: str | None = None


class QuizGenerateRequest(BaseModel):
    document_id: int = Field(gt=0)
    count: int = Field(default=5, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"
    competency_id: int | None = Field(default=None, gt=0)
    topic: str = Field(default="Official Statistics", min_length=1, max_length=160)
    language: str = Field(default="English", min_length=2, max_length=40)


class QuizPublishRequest(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    item_ids: list[int] = Field(min_length=1, max_length=20)


class QuizSubmitRequest(BaseModel):
    answers: dict[int, int]
    language: str = Field(default="en", min_length=2, max_length=8)


class QuizResponse(BaseModel):
    id: int
    title: str
    document_id: int | None
    item_ids: list[int]
    status: str
    created_at: datetime


class QuizResultResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    score: float
    correct_answers: int
    total_questions: int
    topic_performance: dict[str, float]
    explanations: list[dict[str, Any]]
    requested_language: Literal["en", "hi"] = "en"


class EditAssessmentItemRequest(BaseModel):
    question: str | None = Field(default=None, min_length=8, max_length=2000)
    options: list[str] | None = Field(default=None, min_length=4, max_length=4)
    correct_index: int | None = Field(default=None, ge=0, le=3)
    explanation: str | None = Field(default=None, min_length=4, max_length=3000)
    topic: str | None = Field(default=None, min_length=1, max_length=160)
    difficulty: Literal["easy", "medium", "hard"] | None = None
    competency_id: int | None = Field(default=None, gt=0)


class OrganizationSummaryResponse(BaseModel):
    total_officials: int
    average_competency: float
    critical_skill_gaps: int
    completion_rate: float
    assessment_accuracy: float
    learning_hours: float
    competency_improvement_rate: float
