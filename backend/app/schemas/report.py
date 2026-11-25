from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeGapItem(BaseModel):
    topic: str = Field(..., description="Technical subject or architectural concept")
    severity: str = Field(..., description="'Critical', 'Moderate', or 'Minor'")
    evidence_quote: str = Field(..., description="Observed shortfall or missed concept from the interview")
    remedy_recommendation: str = Field(..., description="Concrete technical guidance to master this concept")


class LearningRecommendationItem(BaseModel):
    title: str = Field(..., description="Module or concept title")
    category: str = Field(..., description="Domain category (e.g. 'Systems & Architecture', 'Algorithms', 'Databases')")
    description: str = Field(..., description="Concept overview and importance for target role")
    actionable_exercise: str = Field(..., description="Hands-on coding or architectural project task")
    suggested_reading: Optional[str] = Field(None, description="Recommended documentation or classic engineering papers")


class RadarMetricItem(BaseModel):
    subject: str = Field(..., description="Competency dimension (e.g. 'System Design', 'Core Fundamentals')")
    candidate_score: float = Field(..., description="Candidate score 0-100")
    benchmark_score: float = Field(default=75.0, description="Industry hiring bar benchmark 0-100")


class StageScoreItem(BaseModel):
    stage: str
    stage_title: str
    knowledge_score: float
    comm_score: float
    turns_count: int


class SessionReportResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    job_role: str
    experience_level: str
    overall_knowledge_score: float
    overall_comm_score: float
    stage_breakdown: List[StageScoreItem]
    radar_metrics: List[RadarMetricItem]
    verified_skills: List[str]
    knowledge_gaps: List[KnowledgeGapItem]
    personalized_learning_plan: List[LearningRecommendationItem]
    executive_summary: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionReportListItem(BaseModel):
    id: str
    session_id: str
    job_role: str
    experience_level: str
    overall_knowledge_score: float
    overall_comm_score: float
    gaps_count: int
    created_at: datetime

    class Config:
        from_attributes = True
