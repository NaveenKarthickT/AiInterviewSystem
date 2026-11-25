import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ResumeOptimization(Base):
    __tablename__ = "resume_optimizations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    target_role = Column(String(100), nullable=False)
    
    # List of optimization recommendations (KEEP, MODIFY, VERIFY, REMOVE)
    item_recommendations = Column(JSON, nullable=False)
    
    # Recommended career roles based on verified competency
    job_role_recommendations = Column(JSON, nullable=False)

    status = Column(String(30), default="draft", nullable=False)  # draft, approved, exported
    
    # Final approved ATS content
    optimized_content = Column(JSON, nullable=True)

    exported_pdf_path = Column(String(512), nullable=True)
    exported_docx_path = Column(String(512), nullable=True)

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

    # Relationships
    session = relationship("InterviewSession", back_populates="optimizations")
    resume = relationship("Resume", back_populates="optimizations")
    user = relationship("User", back_populates="optimizations")

    def __repr__(self) -> str:
        return f"<ResumeOptimization {self.id} role={self.target_role} status={self.status}>"
