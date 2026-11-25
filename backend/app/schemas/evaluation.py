from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.interview import InterviewTurnResponse


class KnowledgeEvaluationResult(BaseModel):
    knowledge_score: float = Field(..., ge=0, le=100, description="Total technical knowledge score")
    technical_correctness: float = Field(..., ge=0, le=30, description="Correctness of factual/technical assertions")
    conceptual_depth: float = Field(..., ge=0, le=25, description="Understanding of underlying mechanics & principles")
    practical_application: float = Field(..., ge=0, le=25, description="Real-world engineering relevance and trade-offs")
    problem_solving: float = Field(..., ge=0, le=20, description="Analytical reasoning and systematic breakdown")
    missing_concepts: List[str] = Field(default_factory=list, description="Key concepts or trade-offs omitted")
    incorrect_concepts: List[str] = Field(default_factory=list, description="Inaccurate assertions or misconceptions")
    knowledge_feedback: str = Field(..., description="Actionable technical explanation and guidance")
    knowledge_strengths: List[str] = Field(default_factory=list, description="Demonstrated areas of technical competence")
    knowledge_weaknesses: List[str] = Field(default_factory=list, description="Gaps to review or study")


class CommunicationEvaluationResult(BaseModel):
    comm_score: float = Field(..., ge=0, le=100, description="Total communication proficiency score")
    clarity_score: float = Field(..., ge=0, le=30, description="Clear, logical structure and articulation")
    conciseness_score: float = Field(..., ge=0, le=25, description="Succinctness without excessive filler or tangents")
    professional_vocabulary: float = Field(..., ge=0, le=25, description="Appropriate professional and industry terminology")
    grammar_and_coherence: float = Field(..., ge=0, le=20, description="Sentence cohesion and grammatical fluency")
    structure_feedback: str = Field(..., description="Delivery guidance and structural improvement tips")
    comm_strengths: List[str] = Field(default_factory=list, description="Delivery strengths observed")
    comm_weaknesses: List[str] = Field(default_factory=list, description="Delivery areas to polish")


class DualEvaluationResponse(BaseModel):
    id: str
    turn_id: str
    session_id: str
    knowledge: KnowledgeEvaluationResult
    communication: CommunicationEvaluationResult
    synthesis_notes: Optional[str] = None
    follow_up_recommended: bool = False
    recommended_difficulty_shift: str = "maintain"  # step_up, maintain, step_down
    created_at: datetime

    class Config:
        from_attributes = True


class TurnSubmitRequest(BaseModel):
    candidate_answer: str = Field(..., min_length=1, description="Candidate's verbal/textual response")
    audio_answer_url: Optional[str] = Field(None, description="Optional audio recording reference")


class TurnSubmitResponse(BaseModel):
    turn: InterviewTurnResponse
    evaluation: DualEvaluationResponse
    next_turn: Optional[InterviewTurnResponse] = None
    session_status: str
    current_stage: str
    is_finished: bool = False
