from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StagePlan(BaseModel):
    stage: str = Field(..., description="Stage identifier (e.g. 'intro', 'technical', 'problem_solving')")
    title: str = Field(..., description="Human-readable title")
    focus_goal: str = Field(..., description="Primary objective of this stage for this candidate")
    target_skills_or_topics: List[str] = Field(default_factory=list, description="Specific skills, projects, or concepts to verify")
    estimated_questions: int = Field(default=2, description="Target question count")


class InterviewTrajectory(BaseModel):
    session_summary: str = Field(..., description="Executive summary of the interview strategy")
    candidate_fit_notes: str = Field(..., description="Synthesis of candidate's resume against target role")
    stages: List[StagePlan] = Field(default_factory=list, description="Planned sequential interview stages")


class InterviewCreateRequest(BaseModel):
    interview_type: Optional[str] = Field(default="resume", description="'resume', 'topic', or 'role'")
    resume_id: Optional[str] = None
    focus_topic: Optional[str] = None
    job_role: str = Field(..., min_length=2, max_length=100)
    experience_level: str = Field(default="junior")  # entry_level, junior, mid_level
    interaction_mode: str = Field(default="text")  # text or voice
    selected_stages: Optional[List[str]] = None
    custom_instructions: Optional[str] = None


class InterviewTurnResponse(BaseModel):
    id: str
    session_id: str
    turn_number: int
    stage: str
    difficulty_level: str
    question_text: str
    context_rationale: Optional[str] = None
    expected_concepts: Optional[List[str]] = None
    candidate_answer: Optional[str] = None
    audio_answer_url: Optional[str] = None
    created_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: str
    resume_id: Optional[str] = None
    interview_type: Optional[str] = "resume"
    focus_topic: Optional[str] = None
    job_role: str
    experience_level: str
    interaction_mode: str
    status: str
    current_stage: str
    stages_config: List[Dict[str, Any]]
    planned_trajectory: Optional[InterviewTrajectory] = None
    current_turn_count: int
    avg_knowledge_score: float
    avg_comm_score: float
    created_at: datetime
    turns: List[InterviewTurnResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class InterviewSessionListItem(BaseModel):
    id: str
    resume_id: Optional[str] = None
    interview_type: Optional[str] = "resume"
    focus_topic: Optional[str] = None
    job_role: str
    experience_level: str
    interaction_mode: str
    status: str
    current_stage: str
    current_turn_count: int
    avg_knowledge_score: float
    avg_comm_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedQuestion(BaseModel):
    stage: str
    difficulty_level: str
    question_text: str
    context_rationale: str
    expected_concepts: List[str]
