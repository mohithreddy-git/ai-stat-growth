from datetime import datetime
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EmployeeProfileResponse(BaseModel):
    id: int
    employee_id: str
    email: str
    full_name: str
    designation: str
    department: str
    division: str
    current_assignment: str
    educational_qualification: str
    years_experience: float
    domain: str
    current_role: str
    career_goal: str
    previous_trainings: list[str]
    role: str
    is_demo: bool
    position: str | None = None
    frac_role: str | None = None
    frac_activities: list[str] = Field(default_factory=list)


class CompetencyResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str
    description: str
    beginner_definition: str
    intermediate_definition: str
    advanced_definition: str
    required_level: int
    required_score: float
    weight: float
    competency_type: str = "Functional"


class EmployeeCompetencyResponse(BaseModel):
    competency_id: int
    code: str
    name: str
    category: str
    current_score: float
    current_level: int
    current_level_label: str
    target_level: int
    target_level_label: str
    required_score: float
    delta_from_previous: float | None = None
    last_assessed_at: datetime | None = None
    description: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)


class CompetencyProfileResponse(BaseModel):
    user_id: int
    overall_readiness: float
    category_scores: dict[str, float]
    competencies: list[EmployeeCompetencyResponse]
    strengths: list[EmployeeCompetencyResponse]
    weaknesses: list[EmployeeCompetencyResponse]


class CompetencyDomainSummaryItem(BaseModel):
    name: str
    count: int = Field(ge=0)
    average_current_score: float | None = Field(default=None, ge=0, le=100)
    average_target_score: float | None = Field(default=None, ge=0, le=100)


class CompetencyDomainSummaryResponse(BaseModel):
    domains: list[CompetencyDomainSummaryItem] = Field(default_factory=list)
    total_competencies: int = Field(ge=0)


class SkillGapResponse(BaseModel):
    competency_id: int
    competency: str
    code: str
    category: str
    current_score: float
    required_score: float
    gap: float
    severity: Literal["critical", "high", "medium", "low"]
    priority_severity: Literal["critical", "high", "medium", "low"] = "low"
    priority_score: float = Field(ge=0, le=100)
    role_relevance: float = Field(ge=0, le=100)
    department_priority: float = Field(ge=0, le=100)
    future_demand: float = Field(ge=0, le=100)
    explanation: str
    recommended_next_action: str
    current_level: str
    required_level: str
    gap_score: float = Field(default=0, ge=0, le=100)
    activity_criticality: float = Field(default=0, ge=0, le=100)
    required_for_activities: list[str] = []


class LearningResourceResponse(BaseModel):
    id: int
    resource_type: Literal["course", "training_programme"]
    external_id: str
    title: str
    source: str
    competency_id: int
    competency: str
    description: str
    duration: float
    requested_language: Literal["en", "hi"] = "en"
    localized: bool = False
    localization_label: str | None = None
    title_en: str | None = None
    title_hi: str | None = None
    description_en: str | None = None
    description_hi: str | None = None
    reason_en: str | None = None
    reason_hi: str | None = None
    expected_outcome_en: str | None = None
    expected_outcome_hi: str | None = None
    duration_label: str
    difficulty: str
    relevance_score: float = Field(ge=0, le=100)
    priority: Literal["critical", "high", "medium", "low"]
    priority_score: float = Field(default=0, ge=0, le=100)
    role_match: float = Field(default=0, ge=0, le=100)
    activity_match: float = Field(default=0, ge=0, le=100)
    reason: str
    expected_outcome: str
    current_score: float
    required_score: float
    gap: float
    role_relevance: float
    department_priority: float
    future_demand: float
    expected_improvement: float
    url: str
    is_prototype: bool
    activities: list[str] = Field(default_factory=list)
    explanation_data: dict = Field(default_factory=dict)
    historical_effectiveness: float = 0
    progress_status: Literal["not_started", "in_progress", "completed"] = "not_started"
    completion_percent: float = Field(default=0, ge=0, le=100)


class LearningProgressResponse(BaseModel):
    id: int
    resource_type: Literal["course", "training_programme"]
    resource_id: int
    resource_title: str
    source: str
    status: Literal["not_started", "in_progress", "completed"]
    completion_percent: float = Field(ge=0, le=100)
    learning_hours: float = Field(ge=0)
    last_activity_at: datetime | None = None


class LearningProgressUpsertRequest(BaseModel):
    resource_type: Literal["course", "training_programme"]
    resource_id: int = Field(gt=0)
    status: Literal["not_started", "in_progress", "completed"]
    completion_percent: float = Field(ge=0, le=100)
    learning_hours: float = Field(ge=0, le=10000)

    @model_validator(mode="after")
    def validate_state(self) -> "LearningProgressUpsertRequest":
        if self.status == "not_started" and self.completion_percent != 0:
            raise ValueError("not_started progress must have completion_percent=0")
        return self


class EmployeeDashboardResponse(BaseModel):
    profile: EmployeeProfileResponse
    competency: CompetencyProfileResponse
    skill_gaps: list[SkillGapResponse]
    recommendations: list[LearningResourceResponse]
    learning_progress: list[LearningProgressResponse]
    learning_hours: float
    completed_courses: int
    assessment_score: float | None
    recent_assessment_id: int | None
