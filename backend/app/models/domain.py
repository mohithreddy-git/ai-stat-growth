from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Department(Base, TimestampMixin):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    designation: Mapped[str] = mapped_column(String(160))
    division: Mapped[str] = mapped_column(String(160), default="")
    current_assignment: Mapped[str] = mapped_column(String(240), default="")
    years_experience: Mapped[float] = mapped_column(Float, default=0)
    educational_qualification: Mapped[str] = mapped_column(String(240), default="")
    domain: Mapped[str] = mapped_column(String(160), default="")
    current_role: Mapped[str] = mapped_column(String(160), default="")
    career_goal: Mapped[str] = mapped_column(String(240), default="")
    password_hash: Mapped[str] = mapped_column(String(320))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class Competency(Base, TimestampMixin):
    __tablename__ = "competencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    competency_type: Mapped[str] = mapped_column(String(32), default="Functional", index=True)
    domain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competency_domains.id"), nullable=True, index=True)
    required_level_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competency_levels.id"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    beginner_definition: Mapped[str] = mapped_column(Text)
    intermediate_definition: Mapped[str] = mapped_column(Text)
    advanced_definition: Mapped[str] = mapped_column(Text)
    required_level: Mapped[int] = mapped_column(Integer, default=3)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    associated_roles: Mapped[list] = mapped_column(JSON, default=list)
    associated_courses: Mapped[list] = mapped_column(JSON, default=list)
    associated_assessments: Mapped[list] = mapped_column(JSON, default=list)


class EmployeeCompetency(Base, TimestampMixin):
    __tablename__ = "employee_competencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(64), default="baseline")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_employee_competency_user_comp", "user_id", "competency_id", unique=True),)


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    competency_ids: Mapped[list] = mapped_column(JSON, default=list)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    correct_answer: Mapped[str] = mapped_column(String(240))
    difficulty: Mapped[str] = mapped_column(String(32), default="medium")
    explanation: Mapped[str] = mapped_column(Text, default="")
    localizations: Mapped[dict] = mapped_column(JSON, default=dict)


class AssessmentAttempt(Base, TimestampMixin):
    __tablename__ = "assessment_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="started")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="en")


class CompetencyScoreHistory(Base):
    __tablename__ = "competency_score_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    assessment_attempt_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assessment_attempts.id"), nullable=True, index=True)
    evidence_id: Mapped[Optional[int]] = mapped_column(ForeignKey("competency_evidence.id"), nullable=True, index=True)
    previous_score: Mapped[float] = mapped_column(Float)
    new_score: Mapped[float] = mapped_column(Float)
    delta: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(64), default="assessment")
    calculation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("assessment_attempts.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("assessment_questions.id"), index=True)
    answer: Mapped[str] = mapped_column(String(240))
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(80), index=True)
    duration_hours: Mapped[float] = mapped_column(Float, default=1)
    difficulty: Mapped[str] = mapped_column(String(32), default="intermediate")
    language: Mapped[str] = mapped_column(String(32), default="English")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    competency_ids: Mapped[list] = mapped_column(JSON, default=list)
    role_tags: Mapped[list] = mapped_column(JSON, default=list)
    department_tags: Mapped[list] = mapped_column(JSON, default=list)
    url: Mapped[str] = mapped_column(String(500), default="#")
    completion_status: Mapped[str] = mapped_column(String(32), default="not_started")
    is_prototype: Mapped[bool] = mapped_column(Boolean, default=True)
    localizations: Mapped[dict] = mapped_column(JSON, default=dict)


class TrainingProgramme(Base, TimestampMixin):
    __tablename__ = "training_programmes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    programme_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    programme_name: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    duration_days: Mapped[int] = mapped_column(Integer, default=1)
    target_group: Mapped[str] = mapped_column(String(200), default="Officials")
    competency_ids: Mapped[list] = mapped_column(JSON, default=list)
    role_tags: Mapped[list] = mapped_column(JSON, default=list)
    recommended_for: Mapped[list] = mapped_column(JSON, default=list)
    schedule: Mapped[str] = mapped_column(String(160), default="To be scheduled")
    url: Mapped[str] = mapped_column(String(500), default="#")
    source: Mapped[str] = mapped_column(String(100), default="NSSTA / TPAC (prototype dataset)")
    is_prototype: Mapped[bool] = mapped_column(Boolean, default=True)
    localizations: Mapped[dict] = mapped_column(JSON, default=dict)


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[int] = mapped_column(Integer)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=0)
    priority: Mapped[str] = mapped_column(String(32), default="medium")
    reason: Mapped[str] = mapped_column(Text, default="")
    expected_improvement: Mapped[float] = mapped_column(Float, default=0)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    activities: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class LearningProgress(Base, TimestampMixin):
    __tablename__ = "learning_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    resource_type: Mapped[str] = mapped_column(String(32))
    resource_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="not_started")
    completion_percent: Mapped[float] = mapped_column(Float, default=0)
    learning_hours: Mapped[float] = mapped_column(Float, default=0)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class UploadedDocument(Base, TimestampMixin):
    __tablename__ = "uploaded_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    extracted_text_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("uploaded_documents.id"), index=True)
    chunk_id: Mapped[str] = mapped_column(String(100), index=True)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    embedding_ref: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    embedding_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)


class GeneratedQuestion(Base, TimestampMixin):
    __tablename__ = "generated_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("uploaded_documents.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    correct_answer: Mapped[str] = mapped_column(String(240))
    explanation: Mapped[str] = mapped_column(Text)
    competency: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(32), default="medium")
    source_location: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)


class QuizAttempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    document_id: Mapped[Optional[int]] = mapped_column(ForeignKey("uploaded_documents.id"), nullable=True, index=True)
    published_quiz_id: Mapped[Optional[int]] = mapped_column(ForeignKey("published_quizzes.id"), nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(8), default="en")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    topic_performance: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SkillForecast(Base, TimestampMixin):
    __tablename__ = "skill_forecasts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competency_id: Mapped[int] = mapped_column(ForeignKey("competencies.id"), index=True)
    current_demand: Mapped[float] = mapped_column(Float, default=0)
    projected_demand: Mapped[float] = mapped_column(Float, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0)
    affected_departments: Mapped[list] = mapped_column(JSON, default=list)
    training_priority: Mapped[str] = mapped_column(String(32), default="medium")
    period: Mapped[str] = mapped_column(String(32), default="2026-2030")
    source: Mapped[str] = mapped_column(String(120), default="prototype_seed")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_prototype: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
