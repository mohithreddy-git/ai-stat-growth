from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


# These schemas intentionally use factories below so request/response instances
# never share mutable list/dict defaults.


class CompetencyEvidenceResponse(BaseModel):
    id: int
    competency_id: int
    source_type: str
    source_id: str | None = None
    score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ActivityRequirementResponse(BaseModel):
    activity_id: int
    competency_id: int
    activity: str
    criticality: float = Field(ge=0, le=100)
    required_level: int = Field(ge=1, le=5)
    required_score: float = Field(ge=0, le=100)
    importance: float = Field(ge=0, le=1)
    current_score: float = Field(ge=0, le=100)
    current_level: int = Field(ge=1, le=5)
    current_level_label: str
    gap: float = Field(ge=0, le=100)


class FRACProfileResponse(BaseModel):
    employee_id: int
    position_id: int | None = None
    position: str | None = None
    role_id: int | None = None
    role: str | None = None
    activities: list[ActivityRequirementResponse] = Field(default_factory=list)
    competencies: list[dict[str, Any]] = Field(default_factory=list)


class CompetencyVectorResponse(BaseModel):
    employee_id: int
    dimensions: list[dict[str, Any]]
    current_vector: list[float]
    target_vector: list[float]
    competency_specific_gaps: list[dict[str, Any]]
    critical_gaps: list[dict[str, Any]]
    weighted_distance: float
    cosine_similarity: float
    overall_alignment_score: float


class AssessmentItemPayload(BaseModel):
    question: str = Field(min_length=8, max_length=2000)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: str = Field(min_length=4, max_length=3000)
    competency_id: int = Field(gt=0)
    topic: str = Field(min_length=1, max_length=160)
    difficulty: Literal["easy", "medium", "hard"]
    source: dict[str, Any] = Field(min_length=1)

    @field_validator("source")
    @classmethod
    def source_has_provenance(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not str(value.get("document_id", "")).strip() or not str(value.get("chunk_id", "")).strip():
            raise ValueError("source must include document_id and chunk_id")
        return value

    @field_validator("options")
    @classmethod
    def unique_options(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned) or len({item.casefold() for item in cleaned}) != 4:
            raise ValueError("options must contain four non-empty unique values")
        return cleaned


class AssessmentItemResponse(AssessmentItemPayload):
    id: int
    status: Literal["GENERATED", "VALIDATED", "PENDING_REVIEW", "APPROVED", "REJECTED", "PUBLISHED"]
    confidence: float = Field(ge=0, le=1)
    generated_by: str
    document_id: int | None = None
    created_at: datetime


class AssessmentItemGenerateRequest(BaseModel):
    document_id: int | None = Field(default=None, gt=0)
    competency_id: int | None = Field(default=None, gt=0)
    topic: str = Field(default="Official Statistics", min_length=1, max_length=160)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"
    count: int = Field(default=5, ge=1, le=20)
    language: str = Field(default="English", min_length=2, max_length=40)


class ReviewActionRequest(BaseModel):
    note: str = Field(default="", max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)


class TelemetryActor(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    type: str = Field(default="User", min_length=1, max_length=40)


class TelemetryEnvelope(BaseModel):
    eid: Literal["ASSESSMENT_START", "RESPONSE", "ASSESSMENT_END", "COURSE_START", "COURSE_PROGRESS", "COURSE_COMPLETE", "DOCUMENT_UPLOAD", "CONTENT_VIEW", "SEARCH", "RECOMMENDATION_VIEW", "RECOMMENDATION_ACCEPT", "RECOMMENDATION_REJECT", "FEEDBACK", "SKILL_PROFILE_UPDATE", "ERROR"]
    ets: int = Field(default=0, ge=0)
    ver: str = Field(default="3.0", pattern=r"^\d+\.\d+$")
    mid: str | None = Field(default=None, min_length=8, max_length=120)
    actor: TelemetryActor
    context: dict[str, Any] = Field(default_factory=dict)
    object: dict[str, Any] = Field(default_factory=dict)
    edata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class TelemetryAcceptedResponse(BaseModel):
    mid: str
    accepted: bool
    duplicate: bool = False


class TelemetryBatchRequest(BaseModel):
    events: list[TelemetryEnvelope] = Field(min_length=1, max_length=100)


class VelocityResponse(BaseModel):
    employee_id: int
    window_days: int
    learning_velocity: float
    learning_hours: float
    completed_resources: int
    assessment_accuracy: float
    completion_velocity: float
    engagement_rate: float
    recommendation_acceptance_rate: float
    competency_improvement_rate: float


class SkillProfileMetricResponse(BaseModel):
    competency_id: int
    competency: str
    score: float
    confidence: float
    evidence_count: int
    evidence_by_source: dict[str, int]
