import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DualEvaluation(Base):
    __tablename__ = "dual_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    turn_id = Column(String(36), ForeignKey("interview_turns.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    session_id = Column(String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # 1. Knowledge Evaluation (Independent technical score 0-100)
    knowledge_score = Column(Float, nullable=False)
    technical_correctness = Column(Float, nullable=False)   # 0 to 30
    conceptual_depth = Column(Float, nullable=False)        # 0 to 25
    practical_application = Column(Float, nullable=False)   # 0 to 25
    problem_solving = Column(Float, nullable=False)         # 0 to 20
    
    missing_concepts = Column(JSON, nullable=True)          # List[str]
    incorrect_concepts = Column(JSON, nullable=True)        # List[str]
    knowledge_feedback = Column(Text, nullable=False)
    knowledge_strengths = Column(JSON, nullable=True)       # List[str]
    knowledge_weaknesses = Column(JSON, nullable=True)      # List[str]

    # 2. Communication Evaluation (Independent delivery score 0-100)
    comm_score = Column(Float, nullable=False)
    clarity_score = Column(Float, nullable=False)           # 0 to 30
    conciseness_score = Column(Float, nullable=False)       # 0 to 25
    professional_vocabulary = Column(Float, nullable=False) # 0 to 25
    grammar_and_coherence = Column(Float, nullable=False)   # 0 to 20
    
    structure_feedback = Column(Text, nullable=False)
    comm_strengths = Column(JSON, nullable=True)            # List[str]
    comm_weaknesses = Column(JSON, nullable=True)           # List[str]

    # Overall Turn Synthesis & Next Step Advice
    synthesis_notes = Column(Text, nullable=True)
    follow_up_recommended = Column(Boolean, default=False, nullable=False)
    recommended_difficulty_shift = Column(String(20), default="maintain", nullable=False)  # step_up, maintain, step_down

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    turn = relationship("InterviewTurn", back_populates="evaluation")
    session = relationship("InterviewSession", back_populates="evaluations")

    def __repr__(self) -> str:
        return f"<DualEvaluation turn={self.turn_id} know={self.knowledge_score} comm={self.comm_score}>"
