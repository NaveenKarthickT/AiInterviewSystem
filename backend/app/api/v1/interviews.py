import os
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.schemas.resume import ResumeParsedData, SkillEntity
from app.schemas.interview import (
    InterviewCreateRequest,
    InterviewSessionResponse,
    InterviewSessionListItem,
    InterviewTurnResponse,
    InterviewTrajectory,
    GeneratedQuestion,
)
from app.schemas.evaluation import (
    TurnSubmitRequest,
    TurnSubmitResponse,
    DualEvaluationResponse,
    KnowledgeEvaluationResult,
    CommunicationEvaluationResult,
)
from app.agents.nodes.interview_planner_node import interview_planner_node
from app.agents.nodes.question_generator_node import question_generator_node
from app.agents.graphs.interview_graph import interview_workflow_app, InterviewGraphState

router = APIRouter()


@router.post("/", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def create_interview_session(
    request: InterviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initialize a personalized 7-stage adaptive interview session."""
    # Determine interview mode & resume requirements
    interview_type = request.interview_type or "resume"
    focus_topic = request.focus_topic

    resume = None
    if request.resume_id:
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id
        ).first()
        if not resume and interview_type == "resume":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified resume not found.",
            )
    elif interview_type == "resume":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A resume is required for resume-based interviews.",
        )

    if resume:
        parsed_resume = ResumeParsedData(**(resume.parsed_data or {}))
        extracted_skills = [SkillEntity(**s) for s in (resume.extracted_skills or [])]
    else:
        # Build topic or role specific synthetic profile
        primary_subject = focus_topic or request.job_role
        extracted_skills = [
            SkillEntity(name=primary_subject, category="Domain", confidence_score=1.0),
            SkillEntity(name=request.job_role, category="Role", confidence_score=1.0),
        ]
        parsed_resume = ResumeParsedData(
            full_name=current_user.full_name or "Engineering Candidate",
            summary=f"Technical candidate undergoing {interview_type}-focused interview for {request.job_role} ({primary_subject}).",
            skills=[s.name for s in extracted_skills],
            experience=[],
            projects=[],
            education=[],
        )

    # 1. Run Interview Planner Agent
    trajectory: InterviewTrajectory = interview_planner_node.execute(
        parsed_resume=parsed_resume,
        extracted_skills=extracted_skills,
        job_role=request.job_role,
        experience_level=request.experience_level,
        selected_stages=request.selected_stages,
        interview_type=interview_type,
        focus_topic=focus_topic,
    )

    first_stage = trajectory.stages[0].stage if trajectory.stages else "intro"

    # 2. Persist Session
    new_session = InterviewSession(
        user_id=current_user.id,
        resume_id=resume.id if resume else None,
        interview_type=interview_type,
        focus_topic=focus_topic,
        job_role=request.job_role,
        experience_level=request.experience_level,
        interaction_mode=request.interaction_mode,
        status="in_progress",
        current_stage=first_stage,
        stages_config=[s.model_dump() for s in trajectory.stages],
        planned_trajectory=trajectory.model_dump(),
        current_turn_count=1,
        started_at=datetime.now(timezone.utc),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # 3. Generate Turn #1 Question
    stage_plan = trajectory.stages[0] if trajectory.stages else None
    first_q: GeneratedQuestion = question_generator_node.execute(
        stage=first_stage,
        difficulty="intermediate",
        job_role=request.job_role,
        experience_level=request.experience_level,
        resume=parsed_resume,
        skills=extracted_skills,
        stage_plan=stage_plan,
        previous_turns=[],
        turn_number=1,
        interview_type=interview_type,
        focus_topic=focus_topic,
    )

    # 4. Persist Turn #1
    initial_turn = InterviewTurn(
        session_id=new_session.id,
        turn_number=1,
        stage=first_stage,
        difficulty_level=first_q.difficulty_level,
        question_text=first_q.question_text,
        context_rationale=first_q.context_rationale,
        expected_concepts=first_q.expected_concepts,
    )
    db.add(initial_turn)
    db.commit()
    db.refresh(initial_turn)

    return InterviewSessionResponse(
        id=new_session.id,
        user_id=new_session.user_id,
        resume_id=new_session.resume_id,
        interview_type=new_session.interview_type,
        focus_topic=new_session.focus_topic,
        job_role=new_session.job_role,
        experience_level=new_session.experience_level,
        interaction_mode=new_session.interaction_mode,
        status=new_session.status,
        current_stage=new_session.current_stage,
        stages_config=new_session.stages_config,
        planned_trajectory=trajectory,
        current_turn_count=new_session.current_turn_count,
        avg_knowledge_score=new_session.avg_knowledge_score,
        avg_comm_score=new_session.avg_comm_score,
        created_at=new_session.created_at,
        turns=[InterviewTurnResponse.model_validate(initial_turn)],
    )


@router.post("/{session_id}/turns/{turn_id}/submit", response_model=TurnSubmitResponse)
def submit_candidate_answer(
    session_id: str,
    turn_id: str,
    submission: TurnSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit candidate response for an active interview turn.
    
    1. Triggers LangGraph State Machine.
    2. Runs Knowledge Evaluation Agent (technical correctness & depth).
    3. Runs Communication Evaluation Agent (clarity & structure).
    4. Executes adaptive decision logic (difficulty adjustment & stage progression).
    5. Generates the subsequent adaptive question if session is ongoing.
    """
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    turn = db.query(InterviewTurn).filter(
        InterviewTurn.id == turn_id,
        InterviewTurn.session_id == session.id
    ).first()

    if not turn:
        raise HTTPException(status_code=404, detail="Interview turn not found.")

    if turn.candidate_answer:
        raise HTTPException(status_code=400, detail="This question has already been answered.")

    # 1. Update turn with candidate answer
    turn.candidate_answer = submission.candidate_answer.strip()
    turn.audio_answer_url = submission.audio_answer_url
    turn.answered_at = datetime.now(timezone.utc)
    db.commit()

    # 2. Prepare previous turns context
    previous_turns = []
    for t in session.turns:
        previous_turns.append({
            "turn_number": t.turn_number,
            "stage": t.stage,
            "difficulty": t.difficulty_level,
            "question_text": t.question_text,
            "candidate_answer": t.candidate_answer,
        })

    # 3. Invoke LangGraph Adaptive Workflow
    if session.resume and session.resume.parsed_data:
        resume_payload = session.resume.parsed_data
        skills_payload = session.resume.extracted_skills or []
    else:
        topic_or_role = session.focus_topic or session.job_role
        resume_payload = {
            "full_name": current_user.full_name or "Engineering Candidate",
            "summary": f"Technical candidate undergoing {session.interview_type or 'adaptive'} interview on {topic_or_role}.",
            "skills": [topic_or_role, session.job_role],
            "experience": [],
            "projects": [],
            "education": [],
        }
        skills_payload = [{"name": topic_or_role, "category": "Domain", "confidence_score": 1.0}]

    initial_graph_state: InterviewGraphState = {
        "session_id": session.id,
        "interview_type": getattr(session, "interview_type", "resume") or "resume",
        "focus_topic": getattr(session, "focus_topic", None),
        "job_role": session.job_role,
        "experience_level": session.experience_level,
        "resume_data": resume_payload,
        "skills": skills_payload,
        "current_stage": turn.stage,
        "current_difficulty": turn.difficulty_level,
        "turn_number": turn.turn_number,
        "question_text": turn.question_text,
        "expected_concepts": turn.expected_concepts or [],
        "candidate_answer": turn.candidate_answer,
        "stages_config": session.stages_config or [],
        "previous_turns": previous_turns,
    }

    graph_result = interview_workflow_app.invoke(initial_graph_state)

    know_data = graph_result.get("knowledge_result", {})
    comm_data = graph_result.get("comm_result", {})
    next_action = graph_result.get("next_action", "maintain")
    next_stage = graph_result.get("next_stage", turn.stage)
    next_diff = graph_result.get("next_difficulty", turn.difficulty_level)
    is_finished = graph_result.get("is_finished", False)
    next_q_data = graph_result.get("next_question")

    # 4. Save Dual Evaluation to DB
    dual_eval = DualEvaluation(
        turn_id=turn.id,
        session_id=session.id,
        knowledge_score=know_data.get("knowledge_score", 70.0),
        technical_correctness=know_data.get("technical_correctness", 20.0),
        conceptual_depth=know_data.get("conceptual_depth", 18.0),
        practical_application=know_data.get("practical_application", 18.0),
        problem_solving=know_data.get("problem_solving", 14.0),
        missing_concepts=know_data.get("missing_concepts", []),
        incorrect_concepts=know_data.get("incorrect_concepts", []),
        knowledge_feedback=know_data.get("knowledge_feedback", ""),
        knowledge_strengths=know_data.get("knowledge_strengths", []),
        knowledge_weaknesses=know_data.get("knowledge_weaknesses", []),
        comm_score=comm_data.get("comm_score", 75.0),
        clarity_score=comm_data.get("clarity_score", 22.0),
        conciseness_score=comm_data.get("conciseness_score", 18.0),
        professional_vocabulary=comm_data.get("professional_vocabulary", 18.0),
        grammar_and_coherence=comm_data.get("grammar_and_coherence", 17.0),
        structure_feedback=comm_data.get("structure_feedback", ""),
        comm_strengths=comm_data.get("comm_strengths", []),
        comm_weaknesses=comm_data.get("comm_weaknesses", []),
        synthesis_notes=f"Action: {next_action}. Difficulty: {next_diff}.",
        follow_up_recommended=(next_action == "follow_up"),
        recommended_difficulty_shift=next_diff,
    )
    db.add(dual_eval)

    # 5. Update Session Averages & Stage
    all_evals = db.query(DualEvaluation).filter(DualEvaluation.session_id == session.id).all()
    know_scores = [e.knowledge_score for e in all_evals] + [dual_eval.knowledge_score]
    comm_scores = [e.comm_score for e in all_evals] + [dual_eval.comm_score]

    session.avg_knowledge_score = round(sum(know_scores) / len(know_scores), 1)
    session.avg_comm_score = round(sum(comm_scores) / len(comm_scores), 1)
    session.current_stage = next_stage

    # 6. Generate Next Turn or Conclude Session
    next_turn_record: Optional[InterviewTurn] = None
    if is_finished:
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
    elif next_q_data:
        next_turn_number = turn.turn_number + 1
        next_turn_record = InterviewTurn(
            session_id=session.id,
            turn_number=next_turn_number,
            stage=next_stage,
            difficulty_level=next_diff,
            question_text=next_q_data.get("question_text", ""),
            context_rationale=next_q_data.get("context_rationale", ""),
            expected_concepts=next_q_data.get("expected_concepts", []),
        )
        db.add(next_turn_record)
        session.current_turn_count = next_turn_number

    db.commit()
    db.refresh(turn)
    db.refresh(dual_eval)
    if next_turn_record:
        db.refresh(next_turn_record)

    eval_response = DualEvaluationResponse(
        id=dual_eval.id,
        turn_id=dual_eval.turn_id,
        session_id=dual_eval.session_id,
        knowledge=KnowledgeEvaluationResult(
            knowledge_score=dual_eval.knowledge_score,
            technical_correctness=dual_eval.technical_correctness,
            conceptual_depth=dual_eval.conceptual_depth,
            practical_application=dual_eval.practical_application,
            problem_solving=dual_eval.problem_solving,
            missing_concepts=dual_eval.missing_concepts or [],
            incorrect_concepts=dual_eval.incorrect_concepts or [],
            knowledge_feedback=dual_eval.knowledge_feedback,
            knowledge_strengths=dual_eval.knowledge_strengths or [],
            knowledge_weaknesses=dual_eval.knowledge_weaknesses or [],
        ),
        communication=CommunicationEvaluationResult(
            comm_score=dual_eval.comm_score,
            clarity_score=dual_eval.clarity_score,
            conciseness_score=dual_eval.conciseness_score,
            professional_vocabulary=dual_eval.professional_vocabulary,
            grammar_and_coherence=dual_eval.grammar_and_coherence,
            structure_feedback=dual_eval.structure_feedback,
            comm_strengths=dual_eval.comm_strengths or [],
            comm_weaknesses=dual_eval.comm_weaknesses or [],
        ),
        synthesis_notes=dual_eval.synthesis_notes,
        follow_up_recommended=dual_eval.follow_up_recommended,
        recommended_difficulty_shift=dual_eval.recommended_difficulty_shift,
        created_at=dual_eval.created_at,
    )

    return TurnSubmitResponse(
        turn=InterviewTurnResponse.model_validate(turn),
        evaluation=eval_response,
        next_turn=InterviewTurnResponse.model_validate(next_turn_record) if next_turn_record else None,
        session_status=session.status,
        current_stage=session.current_stage,
        is_finished=is_finished,
    )


@router.get("/", response_model=List[InterviewSessionListItem])
def list_user_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all interview sessions for the authenticated candidate."""
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()

    return [InterviewSessionListItem.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve specific interview session details and full turn history."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )

    trajectory = InterviewTrajectory(**session.planned_trajectory) if session.planned_trajectory else None
    turns = [InterviewTurnResponse.model_validate(t) for t in session.turns]

    return InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        resume_id=session.resume_id,
        interview_type=session.interview_type,
        focus_topic=session.focus_topic,
        job_role=session.job_role,
        experience_level=session.experience_level,
        interaction_mode=session.interaction_mode,
        status=session.status,
        current_stage=session.current_stage,
        stages_config=session.stages_config,
        planned_trajectory=trajectory,
        current_turn_count=session.current_turn_count,
        avg_knowledge_score=session.avg_knowledge_score,
        avg_comm_score=session.avg_comm_score,
        created_at=session.created_at,
        turns=turns,
    )


@router.get("/{session_id}/current-turn", response_model=InterviewTurnResponse)
def get_current_turn(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the latest or pending question turn for an active interview."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )

    latest_turn = db.query(InterviewTurn).filter(
        InterviewTurn.session_id == session.id
    ).order_by(InterviewTurn.turn_number.desc()).first()

    if not latest_turn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No turns exist for this session.",
        )

    return InterviewTurnResponse.model_validate(latest_turn)


@router.get("/{session_id}/turns/{turn_id}/evaluation", response_model=DualEvaluationResponse)
def get_turn_evaluation(
    session_id: str,
    turn_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the dual knowledge and communication evaluation for a specific turn."""
    dual_eval = db.query(DualEvaluation).filter(
        DualEvaluation.turn_id == turn_id,
        DualEvaluation.session_id == session_id
    ).first()

    if not dual_eval:
        raise HTTPException(status_code=404, detail="Evaluation for this turn not found.")

    return DualEvaluationResponse(
        id=dual_eval.id,
        turn_id=dual_eval.turn_id,
        session_id=dual_eval.session_id,
        knowledge=KnowledgeEvaluationResult(
            knowledge_score=dual_eval.knowledge_score,
            technical_correctness=dual_eval.technical_correctness,
            conceptual_depth=dual_eval.conceptual_depth,
            practical_application=dual_eval.practical_application,
            problem_solving=dual_eval.problem_solving,
            missing_concepts=dual_eval.missing_concepts or [],
            incorrect_concepts=dual_eval.incorrect_concepts or [],
            knowledge_feedback=dual_eval.knowledge_feedback,
            knowledge_strengths=dual_eval.knowledge_strengths or [],
            knowledge_weaknesses=dual_eval.knowledge_weaknesses or [],
        ),
        communication=CommunicationEvaluationResult(
            comm_score=dual_eval.comm_score,
            clarity_score=dual_eval.clarity_score,
            conciseness_score=dual_eval.conciseness_score,
            professional_vocabulary=dual_eval.professional_vocabulary,
            grammar_and_coherence=dual_eval.grammar_and_coherence,
            structure_feedback=dual_eval.structure_feedback,
            comm_strengths=dual_eval.comm_strengths or [],
            comm_weaknesses=dual_eval.comm_weaknesses or [],
        ),
        synthesis_notes=dual_eval.synthesis_notes,
        follow_up_recommended=dual_eval.follow_up_recommended,
        recommended_difficulty_shift=dual_eval.recommended_difficulty_shift,
        created_at=dual_eval.created_at,
    )
