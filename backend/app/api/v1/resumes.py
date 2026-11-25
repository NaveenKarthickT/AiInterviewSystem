import os
import re
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume import ResumeResponse, ResumeListItem, ResumeParsedData, SkillEntity
from app.services.document_parser import document_parser
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

router = APIRouter()

MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # bytes

# Map extensions to expected magic bytes at the start of the file
_MAGIC_HEADERS = {
    ".pdf": b"%PDF",
    ".docx": b"PK",    # DOCX is a ZIP archive
    ".doc": b"\xd0\xcf",  # OLE2 Compound Document
}


def _sanitize_filename(raw: str) -> str:
    """Strip path separators, null bytes, and other dangerous chars from a filename."""
    # Take only the basename to prevent directory traversal
    name = os.path.basename(raw)
    # Remove null bytes and control characters
    name = re.sub(r'[\x00/\\]', '', name)
    return name or "upload"


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a candidate resume (PDF or DOCX), extract text, parse sections,
    and profile skills using the AI Resume & Skill Analysis Agent.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Please upload a PDF or DOCX resume.",
        )

    # Sanitize filename before constructing path
    safe_name = _sanitize_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Save uploaded file securely
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}",
        )

    # --- File size cap ---
    actual_size = os.path.getsize(file_path)
    if actual_size > MAX_UPLOAD_SIZE:
        os.remove(file_path)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({actual_size} bytes). Maximum allowed is {MAX_UPLOAD_SIZE} bytes.",
        )

    # --- MIME / magic-byte validation ---
    expected_header = _MAGIC_HEADERS.get(file_ext)
    if expected_header:
        with open(file_path, "rb") as f:
            header_bytes = f.read(len(expected_header))
        if not header_bytes.startswith(expected_header):
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File content does not match the expected '{file_ext}' format.",
            )

    # Extract text from document
    try:
        raw_text = document_parser.parse_document(file_path, file_ext)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing resume content: {str(e)}",
        )

    # Execute Multi-Agent Resume & Skill Extraction
    try:
        parsed_data: ResumeParsedData = resume_parser_node.execute(raw_text)
        extracted_skills: List[SkillEntity] = skill_analysis_node.execute(parsed_data, raw_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Agent parsing pipeline error: {str(e)}",
        )

    # Persist in Database
    new_resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_type=file_ext.lstrip("."),
        file_path=file_path,
        raw_text=raw_text,
        parsed_data=parsed_data.model_dump(),
        extracted_skills=[s.model_dump() for s in extracted_skills],
        summary=parsed_data.executive_summary,
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return ResumeResponse(
        id=new_resume.id,
        user_id=new_resume.user_id,
        file_name=new_resume.file_name,
        file_type=new_resume.file_type,
        summary=new_resume.summary,
        parsed_data=parsed_data,
        extracted_skills=extracted_skills,
        created_at=new_resume.created_at,
        updated_at=new_resume.updated_at,
    )


@router.get("/", response_model=List[ResumeListItem])
def list_user_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all resumes uploaded by the authenticated candidate."""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).all()
    
    items = []
    for r in resumes:
        skills = r.extracted_skills or []
        projects = (r.parsed_data or {}).get("projects", [])
        items.append(ResumeListItem(
            id=r.id,
            file_name=r.file_name,
            file_type=r.file_type,
            summary=r.summary,
            skills_count=len(skills),
            projects_count=len(projects),
            created_at=r.created_at,
        ))
    return items


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume_by_id(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific resume and its extracted profile."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    
    parsed_data = ResumeParsedData(**resume.parsed_data) if resume.parsed_data else None
    extracted_skills = [SkillEntity(**s) for s in (resume.extracted_skills or [])]

    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_name=resume.file_name,
        file_type=resume.file_type,
        summary=resume.summary,
        parsed_data=parsed_data,
        extracted_skills=extracted_skills,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a resume and its local storage file."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )

    # Delete physical file
    if resume.file_path and os.path.exists(resume.file_path):
        try:
            os.remove(resume.file_path)
        except Exception:
            pass

    db.delete(resume)
    db.commit()
    return None
