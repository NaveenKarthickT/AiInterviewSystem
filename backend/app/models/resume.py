import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(512), nullable=False)
    raw_text = Column(Text, nullable=False)
    
    parsed_data = Column(JSON, nullable=True)
    extracted_skills = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="resumes")
    interview_sessions = relationship("InterviewSession", back_populates="resume", cascade="all, delete-orphan")
    optimizations = relationship("ResumeOptimization", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Resume {self.file_name} ({self.id})>"
