from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.models.report import SessionReport
from app.schemas.report import SessionReportResponse, SessionReportListItem
from app.agents.nodes.feedback_node import feedback_node

router = APIRouter()


@router.get("/history", response_model=List[SessionReportListItem])
def list_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all generated performance reports for the authenticated candidate."""
    reports = db.query(SessionReport).filter(
        SessionReport.user_id == current_user.id
    ).order_by(SessionReport.created_at.desc()).all()

    items = []
    for r in reports:
        session = r.session
        items.append(SessionReportListItem(
            id=r.id,
            session_id=r.session_id,
            job_role=session.job_role if session else "Software Engineer",
            experience_level=session.experience_level if session else "junior",
            overall_knowledge_score=r.overall_knowledge_score,
            overall_comm_score=r.overall_comm_score,
            gaps_count=len(r.knowledge_gaps or []),
            created_at=r.created_at,
        ))
    return items


@router.get("/{session_id}", response_model=SessionReportResponse)
def get_session_report(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve or synthesize comprehensive performance analytics, radar metrics,
    identified knowledge gaps, and personalized learning recommendations.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # 1. Check if report is already generated
    existing_report = db.query(SessionReport).filter(
        SessionReport.session_id == session.id
    ).first()

    if existing_report:
        return SessionReportResponse(
            id=existing_report.id,
            session_id=existing_report.session_id,
            user_id=existing_report.user_id,
            job_role=session.job_role,
            experience_level=session.experience_level,
            overall_knowledge_score=existing_report.overall_knowledge_score,
            overall_comm_score=existing_report.overall_comm_score,
            stage_breakdown=existing_report.stage_breakdown,
            radar_metrics=existing_report.radar_metrics,
            verified_skills=existing_report.verified_skills,
            knowledge_gaps=existing_report.knowledge_gaps,
            personalized_learning_plan=existing_report.personalized_learning_plan,
            executive_summary=existing_report.executive_summary,
            created_at=existing_report.created_at,
        )

    # 2. Collect turns & evaluations to synthesize report
    turns = session.turns or []
    evaluations = session.evaluations or []

    turns_dicts = [
        {
            "id": t.id,
            "turn_number": t.turn_number,
            "stage": t.stage,
            "difficulty_level": t.difficulty_level,
            "question_text": t.question_text,
            "candidate_answer": t.candidate_answer,
        }
        for t in turns
    ]

    eval_dicts = [
        {
            "id": e.id,
            "turn_id": e.turn_id,
            "knowledge_score": e.knowledge_score,
            "comm_score": e.comm_score,
            "technical_correctness": e.technical_correctness,
            "conceptual_depth": e.conceptual_depth,
            "practical_application": e.practical_application,
            "problem_solving": e.problem_solving,
            "clarity_score": e.clarity_score,
            "missing_concepts": e.missing_concepts or [],
            "knowledge_feedback": e.knowledge_feedback,
            "structure_feedback": e.structure_feedback,
            "knowledge_strengths": e.knowledge_strengths or [],
            "comm_strengths": e.comm_strengths or [],
        }
        for e in evaluations
    ]

    # 3. Execute Feedback Node Agent
    analytics = feedback_node.execute(
        job_role=session.job_role,
        experience_level=session.experience_level,
        turns=turns_dicts,
        evaluations=eval_dicts,
        resume_data=session.resume.parsed_data if session.resume else {},
        extracted_skills=session.resume.extracted_skills if session.resume else [],
    )

    overall_k = session.avg_knowledge_score or 70.0
    overall_c = session.avg_comm_score or 75.0

    # 4. Persist Report in Database
    new_report = SessionReport(
        session_id=session.id,
        user_id=current_user.id,
        overall_knowledge_score=overall_k,
        overall_comm_score=overall_c,
        stage_breakdown=analytics["stage_breakdown"],
        radar_metrics=analytics["radar_metrics"],
        verified_skills=analytics["verified_skills"],
        knowledge_gaps=analytics["knowledge_gaps"],
        personalized_learning_plan=analytics["personalized_learning_plan"],
        executive_summary=analytics["executive_summary"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return SessionReportResponse(
        id=new_report.id,
        session_id=new_report.session_id,
        user_id=new_report.user_id,
        job_role=session.job_role,
        experience_level=session.experience_level,
        overall_knowledge_score=new_report.overall_knowledge_score,
        overall_comm_score=new_report.overall_comm_score,
        stage_breakdown=new_report.stage_breakdown,
        radar_metrics=new_report.radar_metrics,
        verified_skills=new_report.verified_skills,
        knowledge_gaps=new_report.knowledge_gaps,
        personalized_learning_plan=new_report.personalized_learning_plan,
        executive_summary=new_report.executive_summary,
        created_at=new_report.created_at,
    )
