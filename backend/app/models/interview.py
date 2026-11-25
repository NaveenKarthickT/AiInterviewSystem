import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True, index=True)

    interview_type = Column(String(50), default="resume", nullable=False)  # resume, topic, role
    focus_topic = Column(String(200), nullable=True)

    job_role = Column(String(100), nullable=False)
    experience_level = Column(String(50), default="junior", nullable=False)
    interaction_mode = Column(String(20), default="text", nullable=False)
    status = Column(String(30), default="configured", nullable=False)
    
    current_stage = Column(String(50), default="intro", nullable=False)
    stages_config = Column(JSON, nullable=False)
    planned_trajectory = Column(JSON, nullable=True)

    current_turn_count = Column(Integer, default=0, nullable=False)
    avg_knowledge_score = Column(Float, default=0.0, nullable=False)
    avg_comm_score = Column(Float, default=0.0, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    resume = relationship("Resume", back_populates="interview_sessions")
    turns = relationship("InterviewTurn", back_populates="session", cascade="all, delete-orphan", order_by="InterviewTurn.turn_number")
    evaluations = relationship("DualEvaluation", back_populates="session", cascade="all, delete-orphan")
    report = relationship("SessionReport", uselist=False, back_populates="session", cascade="all, delete-orphan")
    optimizations = relationship("ResumeOptimization", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<InterviewSession {self.id} role={self.job_role} status={self.status}>"


class InterviewTurn(Base):
    __tablename__ = "interview_turns"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    turn_number = Column(Integer, nullable=False)
    stage = Column(String(50), nullable=False)
    difficulty_level = Column(String(20), default="intermediate", nullable=False)

    question_text = Column(Text, nullable=False)
    context_rationale = Column(Text, nullable=True)
    expected_concepts = Column(JSON, nullable=True)

    candidate_answer = Column(Text, nullable=True)
    audio_answer_url = Column(String(512), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    answered_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("InterviewSession", back_populates="turns")
    evaluation = relationship("DualEvaluation", uselist=False, back_populates="turn", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<InterviewTurn {self.turn_number} stage={self.stage} session={self.session_id}>"
