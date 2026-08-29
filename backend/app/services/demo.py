from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.models import AssessmentAttempt, AssessmentItem, AssessmentItemReview, CompetencyEvidence, CompetencyScoreHistory, CompetencyUpdateAudit, CompetencyVectorSnapshot, DocumentChunk, LearningProgress, Recommendation, RecommendationSnapshot, TelemetryEvent, UploadedDocument, User
from app.services.seed import seed_database


def reset_demo_database(db: Session) -> dict:
    """Recreate the existing local schema and reseed the deterministic demo.

    This is intentionally a development/demo operation. It keeps the current
    model and seed architecture, but clears learner-generated runtime state so
    a presentation can restart from the documented Ananya baseline.
    """
    settings = get_settings()
    if not (settings.demo_mode and settings.app_env.lower() in {"development", "demo", "test"}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo reset is disabled")

    db.rollback()
    # The endpoint reuses the request session; detach objects from the old
    # schema before dropping and recreating rows with the same primary keys.
    db.expunge_all()
    bind = db.get_bind()
    Base.metadata.drop_all(bind=bind)
    Base.metadata.create_all(bind=bind)
    seeded = seed_database(db)

    # The seed keeps a small learning-history sample for normal exploration.
    # A reset is stricter: the presenter starts with no learner-generated
    # progress, attempts, documents, telemetry, reviews, or snapshots.
    db.query(LearningProgress).delete()
    db.commit()

    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    if upload_dir.exists():
        for child in upload_dir.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()

    return {
        "status": "reset",
        "message": "Synthetic demo data restored; learner runtime state cleared.",
        "seeded_counts": seeded,
        "runtime_counts": {
            "learning_progress": db.scalar(select(func.count()).select_from(LearningProgress)) or 0,
            "assessment_attempts": db.scalar(select(func.count()).select_from(AssessmentAttempt)) or 0,
            "uploaded_documents": db.scalar(select(func.count()).select_from(UploadedDocument)) or 0,
            "document_chunks": db.scalar(select(func.count()).select_from(DocumentChunk)) or 0,
            "assessment_items": db.scalar(select(func.count()).select_from(AssessmentItem)) or 0,
            "assessment_item_reviews": db.scalar(select(func.count()).select_from(AssessmentItemReview)) or 0,
            "telemetry_events": db.scalar(select(func.count()).select_from(TelemetryEvent)) or 0,
            "recommendations": db.scalar(select(func.count()).select_from(Recommendation)) or 0,
            "recommendation_snapshots": db.scalar(select(func.count()).select_from(RecommendationSnapshot)) or 0,
            "vector_snapshots": db.scalar(select(func.count()).select_from(CompetencyVectorSnapshot)) or 0,
            "score_history": db.scalar(select(func.count()).select_from(CompetencyScoreHistory)) or 0,
            "competency_update_audits": db.scalar(select(func.count()).select_from(CompetencyUpdateAudit)) or 0,
            "competency_evidence": db.scalar(select(func.count()).select_from(CompetencyEvidence)) or 0,
            "users": db.scalar(select(func.count()).select_from(User)) or 0,
        },
    }
