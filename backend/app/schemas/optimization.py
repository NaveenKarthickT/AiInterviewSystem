from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class OptimizationItem(BaseModel):
    id: str = Field(..., description="Unique item identifier")
    section: str = Field(..., description="Resume section ('Summary', 'Skills', 'Projects', 'Experience')")
    original_text: str = Field(..., description="Original claim or bullet text from resume")
    recommended_action: Literal["KEEP", "MODIFY", "VERIFY", "REMOVE"] = Field(
        ...,
        description="Actionable status: KEEP (supported), MODIFY (improve to STAR/XYZ), VERIFY (needs prep), REMOVE (unsubstantiated/outdated)"
    )
    reason: str = Field(..., description="Rationale cross-referencing interview performance and role goals")
    suggested_text: Optional[str] = Field(None, description="Improved, impact-driven replacement bullet")
    approved: bool = Field(default=True, description="Whether candidate has approved this recommendation")


class JobRoleRecommendation(BaseModel):
    role_title: str = Field(..., description="Recommended engineering job title")
    match_percentage: float = Field(..., ge=0, le=100, description="Estimated fit percentage based on verified skills")
    justification: str = Field(..., description="Why candidate fits this role based on interview evidence")
    key_strengths: List[str] = Field(default_factory=list, description="Demonstrated competencies supporting this role")
    recommended_upskill: List[str] = Field(default_factory=list, description="Targeted topics to increase hiring probability")


class ResumeOptimizationResponse(BaseModel):
    id: str
    session_id: str
    resume_id: str
    target_role: str
    item_recommendations: List[OptimizationItem]
    job_role_recommendations: List[JobRoleRecommendation]
    status: str
    optimized_content: Optional[Dict[str, Any]] = None
    exported_pdf_url: Optional[str] = None
    exported_docx_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplyApprovalRequest(BaseModel):
    items: List[OptimizationItem]
    custom_summary: Optional[str] = None
