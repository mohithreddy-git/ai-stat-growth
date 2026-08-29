from pydantic import BaseModel, Field


class DemoResetResponse(BaseModel):
    status: str
    message: str
    seeded_counts: dict[str, int]
    runtime_counts: dict[str, int]


class AdminOverviewResponse(BaseModel):
    total_officials: int
    average_competency: float
    critical_skill_gaps: int
    training_completion_rate: float
    assessment_performance: float
    learning_hours: float
    department_count: int


class DepartmentIntelligenceResponse(BaseModel):
    department_id: int
    department: str
    officials: int
    average_competency: float
    critical_gaps: int
    average_gap: float


class GapAggregateResponse(BaseModel):
    competency_id: int
    competency: str
    category: str
    employees: int
    average_current_score: float
    average_gap: float
    critical_count: int
    priority_score: float


class TrainingEffectivenessResponse(BaseModel):
    resource_type: str
    resource_id: int
    title: str
    learners: int
    completion_rate: float
    completed: int
    learning_hours: float


class ForecastResponse(BaseModel):
    competency_id: int
    competency: str
    current_demand: float
    projected_demand: float
    growth_rate: float
    priority: str
    period: str
    source: str
    confidence: float = Field(ge=0, le=1)
    affected_departments: list[str]
