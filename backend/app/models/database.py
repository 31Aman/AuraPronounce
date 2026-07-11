import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")
    consent_logs = relationship("ConsentLog", back_populates="user", cascade="all, delete-orphan")
    deletion_requests = relationship("DeletionRequest", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class ConsentLog(Base):
    __tablename__ = "consent_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(255), nullable=False, index=True)
    consented = Column(Boolean, nullable=False, default=False)
    purpose = Column(String(255), nullable=False)
    ip_address_encrypted = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="consent_logs")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="uploads")
    analysis = relationship("Analysis", back_populates="upload", uselist=False, cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    upload_id = Column(String(36), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    fluency_score = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)
    completeness_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    suggestions = Column(Text, nullable=True)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    upload = relationship("Upload", back_populates="analysis")
    scores = relationship("Scores", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    word_scores = relationship("WordScore", back_populates="analysis", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="analysis")


class Scores(Base):
    __tablename__ = "scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    stress_score = Column(Float, nullable=False)
    rhythm_score = Column(Float, nullable=False)
    pauses_score = Column(Float, nullable=False)
    timing_score = Column(Float, nullable=False)
    intonation_score = Column(Float, nullable=False)
    phoneme_similarity_score = Column(Float, nullable=False)

    analysis = relationship("Analysis", back_populates="scores")


class WordScore(Base):
    __tablename__ = "word_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(100), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    is_mispronounced = Column(Boolean, default=False)
    is_unclear = Column(Boolean, default=False)
    phonemes_expected = Column(String(255), nullable=True)
    phonemes_actual = Column(String(255), nullable=True)

    analysis = relationship("Analysis", back_populates="word_scores")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    analysis_id = Column(String(36), ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(100), nullable=False)
    issue = Column(String(255), nullable=False)
    correct_pronunciation = Column(String(255), nullable=False)
    suggestion = Column(Text, nullable=False)
    difficulty_level = Column(String(50), default="Medium")

    analysis = relationship("Analysis", back_populates="feedback")


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email_encrypted = Column(Text, nullable=False)
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")  # pending, completed, failed

    user = relationship("User", back_populates="deletion_requests")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    analysis_id = Column(String(36), ForeignKey("analysis.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    details_encrypted = Column(Text, nullable=False)
    ip_address_encrypted = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")
    analysis = relationship("Analysis", back_populates="audit_logs")
