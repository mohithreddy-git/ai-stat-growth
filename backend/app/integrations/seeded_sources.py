from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Course, TrainingProgramme


class SeededIGOTAdapter:
    """Prototype adapter over seeded API-shaped records; replace with an authenticated API client in production."""

    source_name = "iGOT (prototype dataset)"

    def __init__(self, db: Session):
        self.db = db

    def search(self, *, competency_ids: list[int], role: str | None = None, department: str | None = None) -> list[dict[str, Any]]:
        rows = self.db.scalars(select(Course).where(Course.is_prototype.is_(True))).all()
        return [self._serialize(row) for row in rows if set(competency_ids).intersection(row.competency_ids or [])]

    @staticmethod
    def _serialize(row: Course) -> dict[str, Any]:
        return {
            "id": row.id,
            "resource_type": "course",
            "external_id": row.course_id,
            "title": row.title,
            "description": row.description,
            "source": row.source,
            "duration": row.duration_hours,
            "duration_label": f"{row.duration_hours:g} hours",
            "difficulty": row.difficulty,
            "skills": row.skills or [],
            "competency_ids": row.competency_ids or [],
            "role_tags": row.role_tags or [],
            "department_tags": row.department_tags or [],
            "language": row.language,
            "url": row.url,
            "is_prototype": row.is_prototype,
            "localizations": row.localizations or {},
        }


class SeededNSSTAAdapter:
    """Prototype adapter over seeded NSSTA/TPAC-shaped records; replace with an approved API client later."""

    source_name = "NSSTA / TPAC (prototype dataset)"

    def __init__(self, db: Session):
        self.db = db

    def search(self, *, competency_ids: list[int], role: str | None = None, department: str | None = None) -> list[dict[str, Any]]:
        rows = self.db.scalars(select(TrainingProgramme).where(TrainingProgramme.is_prototype.is_(True))).all()
        return [self._serialize(row) for row in rows if set(competency_ids).intersection(row.competency_ids or [])]

    @staticmethod
    def _serialize(row: TrainingProgramme) -> dict[str, Any]:
        return {
            "id": row.id,
            "resource_type": "training_programme",
            "external_id": row.programme_id,
            "title": row.programme_name,
            "description": row.description,
            "source": row.source,
            "duration": row.duration_days,
            "duration_label": f"{row.duration_days} days",
            "difficulty": "facilitated",
            "competency_ids": row.competency_ids or [],
            "role_tags": row.role_tags or [],
            "recommended_for": row.recommended_for or [],
            "schedule": row.schedule,
            "url": row.url,
            "is_prototype": row.is_prototype,
            "localizations": row.localizations or {},
        }
