import os
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import decode_access_token
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.models.report import SessionReport
from app.models.optimization import ResumeOptimization
from app.schemas.optimization import (
    ResumeOptimizationResponse,
    OptimizationItem,
    JobRoleRecommendation,
    ApplyApprovalRequest,
)
from app.agents.nodes.resume_optimizer_node import resume_optimizer_node
from app.agents.nodes.career_recommend_node import career_recommend_node
from app.services.export_service import export_service

router = APIRouter()


@router.post("/generate/{session_id}", response_model=ResumeOptimizationResponse, status_code=status.HTTP_201_CREATED)
def generate_resume_optimization(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze interview performance against resume claims, generate
    KEEP, MODIFY, VERIFY, REMOVE recommendations, and predict top matched job roles.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    resume = session.resume
    if not resume:
        raise HTTPException(status_code=404, detail="Associated resume not found.")

    # 1. Gather turns and evaluations
    turns_dicts = [
        {"turn_number": t.turn_number, "stage": t.stage, "question_text": t.question_text, "candidate_answer": t.candidate_answer}
        for t in session.turns
    ]
    eval_dicts = [
        {"knowledge_score": e.knowledge_score, "comm_score": e.comm_score, "knowledge_strengths": e.knowledge_strengths}
        for e in session.evaluations
    ]

    resume_data = resume.parsed_data or {}
    skills = resume.extracted_skills or []

    # 2. Run Resume Optimizer Agent
    item_recommendations = resume_optimizer_node.execute(
        resume_data=resume_data,
        extracted_skills=skills,
        turns=turns_dicts,
        evaluations=eval_dicts,
        target_role=session.job_role,
    )

    # 3. Run Career Recommendation Agent
    verified_skills = []
    for e in session.evaluations:
        if e.knowledge_score >= 70.0 and e.knowledge_strengths:
            verified_skills.extend(e.knowledge_strengths)
    if not verified_skills:
        verified_skills = [s.get("name") for s in skills[:5]]

    job_recommendations = career_recommend_node.execute(
        verified_skills=verified_skills,
        radar_metrics=(session.report.radar_metrics if session.report else []),
        overall_knowledge_score=session.avg_knowledge_score or 75.0,
        target_role=session.job_role,
    )

    # 4. Check if optimization record already exists
    existing_opt = db.query(ResumeOptimization).filter(
        ResumeOptimization.session_id == session.id
    ).first()

    if existing_opt:
        existing_opt.item_recommendations = [i.model_dump() for i in item_recommendations]
        existing_opt.job_role_recommendations = [r.model_dump() for r in job_recommendations]
        existing_opt.target_role = session.job_role
        db.commit()
        db.refresh(existing_opt)
        opt_record = existing_opt
    else:
        opt_record = ResumeOptimization(
            session_id=session.id,
            resume_id=resume.id,
            user_id=current_user.id,
            target_role=session.job_role,
            item_recommendations=[i.model_dump() for i in item_recommendations],
            job_role_recommendations=[r.model_dump() for r in job_recommendations],
            status="draft",
        )
        db.add(opt_record)
        db.commit()
        db.refresh(opt_record)

    return ResumeOptimizationResponse(
        id=opt_record.id,
        session_id=opt_record.session_id,
        resume_id=opt_record.resume_id,
        target_role=opt_record.target_role,
        item_recommendations=item_recommendations,
        job_role_recommendations=job_recommendations,
        status=opt_record.status,
        optimized_content=opt_record.optimized_content,
        exported_pdf_url=f"/api/v1/optimization/{opt_record.id}/export/pdf" if opt_record.exported_pdf_path else None,
        exported_docx_url=f"/api/v1/optimization/{opt_record.id}/export/docx" if opt_record.exported_docx_path else None,
        created_at=opt_record.created_at,
    )


@router.get("/{session_id}", response_model=ResumeOptimizationResponse)
def get_resume_optimization(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve existing resume optimization and job role recommendations."""
    opt_record = db.query(ResumeOptimization).filter(
        ResumeOptimization.session_id == session_id,
        ResumeOptimization.user_id == current_user.id
    ).first()

    if not opt_record:
        # Generate automatically on the fly if not existing
        return generate_resume_optimization(session_id=session_id, db=db, current_user=current_user)

    items = [OptimizationItem(**i) for i in opt_record.item_recommendations]
    job_recs = [JobRoleRecommendation(**r) for r in opt_record.job_role_recommendations]

    return ResumeOptimizationResponse(
        id=opt_record.id,
        session_id=opt_record.session_id,
        resume_id=opt_record.resume_id,
        target_role=opt_record.target_role,
        item_recommendations=items,
        job_role_recommendations=job_recs,
        status=opt_record.status,
        optimized_content=opt_record.optimized_content,
        exported_pdf_url=f"/api/v1/optimization/{opt_record.id}/export/pdf" if opt_record.exported_pdf_path else None,
        exported_docx_url=f"/api/v1/optimization/{opt_record.id}/export/docx" if opt_record.exported_docx_path else None,
        created_at=opt_record.created_at,
    )


@router.post("/{optimization_id}/approve", response_model=ResumeOptimizationResponse)
def approve_and_compile_resume(
    optimization_id: str,
    approval_req: ApplyApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply candidate-approved recommendations and generate ATS-compliant PDF & DOCX exports."""
    opt_record = db.query(ResumeOptimization).filter(
        ResumeOptimization.id == optimization_id,
        ResumeOptimization.user_id == current_user.id
    ).first()

    if not opt_record:
        raise HTTPException(status_code=404, detail="Optimization record not found.")

    resume = opt_record.resume
    parsed_data = resume.parsed_data or {}

    # Compile optimized content from approved items
    approved_skills = []
    approved_projects = list(parsed_data.get("projects", []))
    final_summary = approval_req.custom_summary or parsed_data.get("executive_summary")

    for item in approval_req.items:
        if not item.approved:
            continue

        if item.section == "Summary" and item.suggested_text:
            final_summary = item.suggested_text
        elif item.section == "Skills":
            if item.recommended_action in ["KEEP", "MODIFY"]:
                approved_skills.append(item.original_text)
        elif item.section == "Projects" and item.suggested_text:
            for p in approved_projects:
                if p.get("title", "").lower() in item.original_text.lower():
                    p["description"] = item.suggested_text

    if not approved_skills:
        approved_skills = parsed_data.get("technical_skills", [])

    compiled_content = {
        "full_name": parsed_data.get("full_name") or current_user.full_name,
        "email": parsed_data.get("email") or current_user.email,
        "phone": parsed_data.get("phone", ""),
        "github": parsed_data.get("github", ""),
        "linkedin": parsed_data.get("linkedin", ""),
        "summary": final_summary,
        "skills": list(dict.fromkeys(approved_skills)),
        "projects": approved_projects,
        "experience": parsed_data.get("experience", []),
        "education": parsed_data.get("education", []),
    }

    # Generate DOCX and PDF
    docx_filename = f"ATS_Resume_{current_user.id[:8]}_{opt_record.id[:6]}.docx"
    pdf_filename = f"ATS_Resume_{current_user.id[:8]}_{opt_record.id[:6]}.pdf"

    docx_path = export_service.generate_docx(compiled_content, docx_filename)
    pdf_path = export_service.generate_pdf(compiled_content, pdf_filename)

    opt_record.status = "approved"
    opt_record.optimized_content = compiled_content
    opt_record.item_recommendations = [i.model_dump() for i in approval_req.items]
    opt_record.exported_docx_path = docx_path
    opt_record.exported_pdf_path = pdf_path
    db.commit()
    db.refresh(opt_record)

    items = [OptimizationItem(**i) for i in opt_record.item_recommendations]
    job_recs = [JobRoleRecommendation(**r) for r in opt_record.job_role_recommendations]

    return ResumeOptimizationResponse(
        id=opt_record.id,
        session_id=opt_record.session_id,
        resume_id=opt_record.resume_id,
        target_role=opt_record.target_role,
        item_recommendations=items,
        job_role_recommendations=job_recs,
        status=opt_record.status,
        optimized_content=opt_record.optimized_content,
        exported_pdf_url=f"/api/v1/optimization/{opt_record.id}/export/pdf",
        exported_docx_url=f"/api/v1/optimization/{opt_record.id}/export/docx",
        created_at=opt_record.created_at,
    )


oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"/{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


@router.get("/{optimization_id}/export/{file_format}")
def download_exported_resume(
    optimization_id: str,
    file_format: str,
    token: Optional[str] = None,
    auth_header_token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    """Download the finalized ATS-compliant PDF or DOCX resume.
    Supports both Authorization: Bearer <token> header and ?token=<jwt> query parameter.
    """
    effective_token = auth_header_token or token
    if not effective_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to download resume. Please provide Bearer token or ?token= query parameter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(effective_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token.")

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    opt_record = db.query(ResumeOptimization).filter(
        ResumeOptimization.id == optimization_id,
        ResumeOptimization.user_id == user.id
    ).first()

    if not opt_record:
        raise HTTPException(status_code=404, detail="Optimization record not found.")

    file_format = file_format.lower().replace(".", "")
    if file_format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: 'pdf', 'docx'")

    target_role_clean = (opt_record.target_role or "Software_Engineer").replace(' ', '_')
    if file_format == "docx":
        file_path = opt_record.exported_docx_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        download_name = f"ATS_Resume_{target_role_clean}.docx"
    else:
        file_path = opt_record.exported_pdf_path
        media_type = "application/pdf"
        download_name = f"ATS_Resume_{target_role_clean}.pdf"

    # If the file does not exist on disk, auto-compile it on the fly!
    if not file_path or not os.path.exists(file_path):
        content_to_export = opt_record.optimized_content
        if not content_to_export and opt_record.resume:
            parsed = opt_record.resume.parsed_data or {}
            content_to_export = {
                "full_name": parsed.get("full_name") or user.full_name,
                "email": parsed.get("email") or user.email,
                "phone": parsed.get("phone", ""),
                "github": parsed.get("github", ""),
                "linkedin": parsed.get("linkedin", ""),
                "summary": parsed.get("executive_summary") or "",
                "skills": parsed.get("technical_skills", []),
                "projects": parsed.get("projects", []),
                "experience": parsed.get("experience", []),
                "education": parsed.get("education", []),
            }
        if content_to_export:
            filename = f"ATS_Resume_{user.id[:8]}_{opt_record.id[:6]}.{file_format}"
            if file_format == "pdf":
                file_path = export_service.generate_pdf(content_to_export, filename)
                opt_record.exported_pdf_path = file_path
            else:
                file_path = export_service.generate_docx(content_to_export, filename)
                opt_record.exported_docx_path = file_path
            db.commit()
        else:
            raise HTTPException(
                status_code=404,
                detail="Resume content not available for export. Please approve recommendations first."
            )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_name,
    )
