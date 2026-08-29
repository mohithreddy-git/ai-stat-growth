from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str
    email: str
    full_name: str
    designation: str
    division: str
    current_assignment: str
    years_experience: float
    domain: str
    current_role: str
    career_goal: str
    role: str
    department: str
    is_demo: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class BootstrapResponse(BaseModel):
    app_name: str
    environment: str
    phase: str
    ai_provider: str
    demo_mode: bool
    seeded_counts: dict[str, int]
    planned_modules: list[str]
