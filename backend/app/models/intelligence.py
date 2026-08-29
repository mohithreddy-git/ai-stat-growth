from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompetencyDomain(Base):
    __tablename__ = "competency_domains"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class CompetencyLevel(Base):
    __tablename__ = "competency_levels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    assessment_criteria: Mapped[str] = mapped_column(Text, default="")
    observable_behaviour: Mapped[str] = mapped_column(Text, default="")


class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class PositionRole(Base):
    __tablename__ = "position_roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")


class Activity(Base):
    __tablename__ = "activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text, default="")
    criticality: Mapped[float] = mapped_column(Float, default=50.0)


class RoleActivity(Base):
    __tablename__ = "role_activities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("position_roles.id"), index=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    criticality: Mapped[float] = mapped_column(Float, default=50.0)

    __table_args__ = (UniqueConstraint("role_id", "activity_id", name="uq_role_activity"),)


class ActivityCompetency(Base):
    __tablename__ = "activity_competencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    required_level: Mapped[int] = mapped_column(Integer, default=3)
    importance: Mapped[float] = mapped_column(Float, default=1.0)

    __table_args__ = (UniqueConstraint("activity_id", "competency_id", name="uq_activity_competency"),)


class RoleCompetencyRequirement(Base):
    __tablename__ = "role_competency_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("position_roles.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    required_level: Mapped[int] = mapped_column(Integer, default=3)
    importance: Mapped[float] = mapped_column(Float, default=1.0)

    __table_args__ = (UniqueConstraint("role_id", "competency_id", name="uq_role_competency"),)


class EmployeeRole(Base):
    __tablename__ = "employee_roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("position_roles.id"), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),)


class CompetencyEvidence(Base):
    __tablename__ = "competency_evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class CompetencyVectorSnapshot(Base):
    __tablename__ = "competency_vector_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vector_type: Mapped[str] = mapped_column(String(20))
    vector_json: Mapped[list] = mapped_column(JSON, default=list)
    dimensions_json: Mapped[list] = mapped_column(JSON, default=list)
    weighted_distance: Mapped[float] = mapped_column(Float, default=0)
    cosine_similarity: Mapped[float] = mapped_column(Float, default=0)
    alignment_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AssessmentItem(Base):
    __tablename__ = "assessment_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[Optional[int]] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True, index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(160))
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    source: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="GENERATED", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    generated_by: Mapped[str] = mapped_column(String(40), default="mock")
    localizations: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AssessmentItemReview(Base):
    __tablename__ = "assessment_item_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_item_id: Mapped[int] = mapped_column(ForeignKey("assessment_items.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(32))
    note: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FutureSkillDemand(Base):
    __tablename__ = "future_skill_demand"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    current_demand: Mapped[float] = mapped_column(Float, default=0)
    projected_demand: Mapped[float] = mapped_column(Float, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0)
    priority: Mapped[str] = mapped_column(String(32), default="medium")
    period: Mapped[str] = mapped_column(String(32), default="2026-2030")
    source: Mapped[str] = mapped_column(String(120), default="prototype_seed")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    affected_departments: Mapped[list] = mapped_column(JSON, default=list)


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mid: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    eid: Mapped[str] = mapped_column(String(40), index=True)
    ets: Mapped[int] = mapped_column(Integer, index=True)
    ver: Mapped[str] = mapped_column(String(20), default="3.0")
    actor: Mapped[dict] = mapped_column(JSON, default=dict)
    context: Mapped[dict] = mapped_column(JSON, default=dict)
    object: Mapped[dict] = mapped_column(JSON, default=dict)
    edata: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class CompetencyUpdateAudit(Base):
    __tablename__ = "competency_update_audits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    old_score: Mapped[float] = mapped_column(Float)
    new_score: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40))
    evidence_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competency_evidence.id"), nullable=True, index=True)
    calculation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RecommendationSnapshot(Base):
    __tablename__ = "recommendation_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PublishedQuiz(Base):
    __tablename__ = "published_quizzes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[Optional[int]] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    item_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="PUBLISHED", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuizItemAnswer(Base):
    __tablename__ = "quiz_item_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quiz_attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id"), index=True)
    assessment_item_id: Mapped[int] = mapped_column(ForeignKey("assessment_items.id"), index=True)
    selected_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
