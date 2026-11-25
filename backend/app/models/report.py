import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class SessionReport(Base):
    __tablename__ = "session_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_knowledge_score = Column(Float, nullable=False)
    overall_comm_score = Column(Float, nullable=False)

    stage_breakdown = Column(JSON, nullable=False)
    radar_metrics = Column(JSON, nullable=False)
    verified_skills = Column(JSON, nullable=False)
    knowledge_gaps = Column(JSON, nullable=False)
    personalized_learning_plan = Column(JSON, nullable=False)
    
    executive_summary = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    session = relationship("InterviewSession", back_populates="report")
    user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<SessionReport {self.id} session={self.session_id} know={self.overall_knowledge_score} comm={self.overall_comm_score}>"
