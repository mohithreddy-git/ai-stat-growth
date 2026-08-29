from typing import Any, Literal

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    mode: Literal["general", "document"] = "general"
    document_id: int | None = Field(default=None, gt=0)
    top_k: int = Field(default=3, ge=1, le=8)
    language: str = Field(default="en", min_length=2, max_length=8)


class AssistantResponse(BaseModel):
    answer: str
    mode: Literal["general", "document"]
    provider: str
    sources: list[dict[str, Any]] = []
    requested_language: Literal["en", "hi"] = "en"
    localized: bool = False
