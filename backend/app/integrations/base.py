from typing import Any, Protocol


class LearningSourceAdapter(Protocol):
    """Stable contract for API-backed learning sources."""

    source_name: str

    async def search(self, *, competency_ids: list[int], role: str | None = None, department: str | None = None) -> list[dict[str, Any]]:
        ...


class IGOTAdapter(LearningSourceAdapter, Protocol):
    source_name: str


class NSSTAAdapter(LearningSourceAdapter, Protocol):
    source_name: str
