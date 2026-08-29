from typing import Literal

from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    id: int
    course_id: str
    title: str
    description: str
    source: str
    duration_hours: float
    difficulty: str
    language: str
    requested_language: Literal["en", "hi"] = "en"
    localized: bool = False
    localization_label: str | None = None
    title_en: str
    title_hi: str | None = None
    description_en: str
    description_hi: str | None = None
    skills: list[str]
    competency_ids: list[int]
    role_tags: list[str]
    department_tags: list[str]
    url: str
    completion_status: str
    is_prototype: bool


class TrainingProgrammeResponse(BaseModel):
    id: int
    programme_id: str
    programme_name: str
    description: str
    category: str
    duration_days: int
    target_group: str
    requested_language: Literal["en", "hi"] = "en"
    localized: bool = False
    localization_label: str | None = None
    title_en: str
    title_hi: str | None = None
    description_en: str
    description_hi: str | None = None
    competency_ids: list[int]
    role_tags: list[str]
    recommended_for: list[str]
    schedule: str
    url: str
    source: str
    is_prototype: bool
