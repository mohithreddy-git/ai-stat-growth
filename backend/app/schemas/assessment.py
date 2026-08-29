from datetime import datetime

from pydantic import BaseModel, Field
from typing import Literal


class AssessmentSummaryResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    question_count: int
    competency_count: int


class AssessmentQuestionResponse(BaseModel):
    id: int
    competency_id: int
    competency: str
    category: str
    question: str
    options: list[str]
    difficulty: str
    explanation: str | None = None
    requested_language: Literal["en", "hi"] = "en"
    localized: bool = False


class AssessmentDetailResponse(AssessmentSummaryResponse):
    questions: list[AssessmentQuestionResponse]


class AssessmentStartRequest(BaseModel):
    assessment_id: int = Field(gt=0)
    language: str = Field(default="en", min_length=2, max_length=8)


class AssessmentStartResponse(BaseModel):
    attempt_id: int
    assessment: AssessmentDetailResponse
    started_at: datetime


class AssessmentAnswerInput(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=240)


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswerInput] = Field(min_length=1)


class CompetencyResultResponse(BaseModel):
    competency_id: int
    competency: str
    category: str
    previous_score: float
    assessment_score: float
    updated_score: float
    delta: float
    required_score: float
    gap_after: float


class AssessmentAnswerReviewResponse(BaseModel):
    question_id: int
    competency: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class AssessmentResultResponse(BaseModel):
    attempt_id: int
    assessment_id: int
    assessment_title: str
    status: Literal["completed"]
    overall_score: float
    percentage: float
    correct_answers: int
    incorrect_answers: int
    total_questions: int
    category_scores: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    competency_results: list[CompetencyResultResponse]
    answer_review: list[AssessmentAnswerReviewResponse]
    completed_at: datetime
