from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EducationEntity(BaseModel):
    degree: str = Field(..., description="Degree or program title (e.g. B.Tech in Computer Science)")
    institution: str = Field(..., description="University, college, or school name")
    year: Optional[str] = Field(None, description="Graduation year or date range (e.g. 2021 - 2025)")
    gpa_or_grade: Optional[str] = Field(None, description="CGPA or percentage if present")


class ProjectEntity(BaseModel):
    title: str = Field(..., description="Project title")
    technologies: List[str] = Field(default_factory=list, description="Technologies & tools utilized")
    role: Optional[str] = Field(None, description="Candidate's role in the project")
    description: str = Field(..., description="Concise description of the architecture and contribution")
    metrics_or_impact: Optional[str] = Field(None, description="Quantifiable metrics, benchmarks, or impact")


class ExperienceEntity(BaseModel):
    company: str = Field(..., description="Company or organization name")
    role: str = Field(..., description="Job or internship title")
    duration: Optional[str] = Field(None, description="Dates or duration of employment")
    highlights: List[str] = Field(default_factory=list, description="Key responsibilities and achievements")


class SkillEntity(BaseModel):
    name: str = Field(..., description="Skill or technology name (e.g. Python, Docker, PyTorch)")
    category: str = Field(
        ...,
        description="Category: 'Languages', 'Frameworks', 'Databases', 'Cloud & DevOps', 'Tools', 'Soft Skills'"
    )
    proficiency: str = Field(
        default="Intermediate",
        description="Assessed proficiency claim: 'Beginner', 'Intermediate', or 'Advanced'"
    )
    evidence_summary: Optional[str] = Field(
        None,
        description="Brief evidence from resume projects or work experience supporting this skill"
    )


class ResumeParsedData(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    education: List[EducationEntity] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    tools_and_frameworks: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    projects: List[ProjectEntity] = Field(default_factory=list)
    experience: List[ExperienceEntity] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    executive_summary: Optional[str] = None


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: str
    summary: Optional[str] = None
    parsed_data: Optional[ResumeParsedData] = None
    extracted_skills: List[SkillEntity] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeListItem(BaseModel):
    id: str
    file_name: str
    file_type: str
    summary: Optional[str] = None
    skills_count: int = 0
    projects_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True
