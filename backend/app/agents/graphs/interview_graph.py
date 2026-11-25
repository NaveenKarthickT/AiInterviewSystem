import json
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from app.agents.nodes.knowledge_eval_node import knowledge_evaluation_node
from app.agents.nodes.comm_eval_node import communication_evaluation_node
from app.agents.nodes.question_generator_node import question_generator_node
from app.schemas.resume import ResumeParsedData, SkillEntity
from app.schemas.interview import StagePlan


class InterviewGraphState(TypedDict, total=False):
    session_id: str
    interview_type: str
    focus_topic: Optional[str]
    job_role: str
    experience_level: str
    resume_data: Dict[str, Any]
    skills: List[Dict[str, Any]]
    current_stage: str
    current_difficulty: str
    turn_number: int
    question_text: str
    expected_concepts: List[str]
    candidate_answer: str
    
    # Dual evaluations
    knowledge_result: Dict[str, Any]
    comm_result: Dict[str, Any]

    # Adaptive state
    next_action: str  # "follow_up", "next_stage", "step_up", "step_down", "conclude"
    next_stage: str
    next_difficulty: str
    is_finished: bool
    next_question: Optional[Dict[str, Any]]
    
    stages_config: List[Dict[str, Any]]
    previous_turns: List[Dict[str, Any]]


def eval_knowledge_node(state: InterviewGraphState) -> Dict[str, Any]:
    """Execute independent technical knowledge evaluation."""
    res = knowledge_evaluation_node.execute(
        question_text=state.get("question_text", ""),
        expected_concepts=state.get("expected_concepts", []),
        candidate_answer=state.get("candidate_answer", ""),
        stage=state.get("current_stage", "intro"),
        difficulty=state.get("current_difficulty", "intermediate"),
        job_role=state.get("job_role", "Software Engineer"),
    )
    return {"knowledge_result": res.model_dump()}


def eval_comm_node(state: InterviewGraphState) -> Dict[str, Any]:
    """Execute independent communication & delivery evaluation."""
    res = communication_evaluation_node.execute(
        question_text=state.get("question_text", ""),
        candidate_answer=state.get("candidate_answer", ""),
        stage=state.get("current_stage", "intro"),
    )
    return {"comm_result": res.model_dump()}


def adaptive_decision_node(state: InterviewGraphState) -> Dict[str, Any]:
    """Analyze dual evaluations, adjust difficulty, and decide whether to
    probe, advance stage, or conclude interview.
    """
    know = state.get("knowledge_result", {})
    know_score = know.get("knowledge_score", 70.0)
    current_stage = state.get("current_stage", "intro")
    current_diff = state.get("current_difficulty", "intermediate")
    turn_number = state.get("turn_number", 1)
    stages_config = state.get("stages_config", [])
    prev_turns = state.get("previous_turns", [])

    # Count how many turns have been completed in the current stage
    stage_turns_count = sum(1 for t in prev_turns if t.get("stage") == current_stage) + 1

    # Stage sequence order
    sequence = [
        "intro",
        "skill_verification",
        "technical",
        "problem_solving",
        "project_discussion",
        "experience_discussion",
        "behavioral_hr",
    ]

    # Find configured max questions for this stage
    stage_target_q = 2
    for cfg in stages_config:
        if cfg.get("stage") == current_stage:
            stage_target_q = cfg.get("estimated_questions", 2)
            break

    # 1. Decide Difficulty Shift
    if know_score >= 82.0:
        next_diff = "advanced"
        diff_shift = "step_up"
    elif know_score < 50.0:
        next_diff = "basic"
        diff_shift = "step_down"
    else:
        next_diff = current_diff
        diff_shift = "maintain"

    # 2. Decide Stage Transition or Follow-Up
    try:
        curr_idx = sequence.index(current_stage)
    except ValueError:
        curr_idx = 0

    if stage_turns_count >= stage_target_q:
        # Stage target reached -> advance to next stage in sequence
        if curr_idx + 1 < len(sequence):
            next_stage = sequence[curr_idx + 1]
            next_action = "next_stage"
            is_finished = False
        else:
            # All 7 stages completed!
            next_stage = current_stage
            next_action = "conclude"
            is_finished = True
    else:
        # Check if incomplete answer requires follow-up
        missing = know.get("missing_concepts", [])
        if missing and len(missing) >= 2 and stage_turns_count == 1:
            next_action = "follow_up"
        else:
            next_action = "maintain"
        next_stage = current_stage
        is_finished = False

    return {
        "next_action": next_action,
        "next_stage": next_stage,
        "next_difficulty": next_diff,
        "is_finished": is_finished,
    }


def generate_next_question_node(state: InterviewGraphState) -> Dict[str, Any]:
    """Generate the next turn question based on adaptive state."""
    if state.get("is_finished", False):
        return {"next_question": None}

    resume = ResumeParsedData(**state.get("resume_data", {}))
    skills = [SkillEntity(**s) for s in state.get("skills", [])]
    
    stages_config = state.get("stages_config", [])
    target_plan = None
    for cfg in stages_config:
        if cfg.get("stage") == state.get("next_stage"):
            target_plan = StagePlan(**cfg)
            break

    next_q = question_generator_node.execute(
        stage=state.get("next_stage", "technical"),
        difficulty=state.get("next_difficulty", "intermediate"),
        job_role=state.get("job_role", "Software Engineer"),
        experience_level=state.get("experience_level", "junior"),
        resume=resume,
        skills=skills,
        stage_plan=target_plan,
        previous_turns=state.get("previous_turns", []),
        turn_number=state.get("turn_number", 1) + 1,
        interview_type=state.get("interview_type", "resume"),
        focus_topic=state.get("focus_topic"),
    )

    return {"next_question": next_q.model_dump()}


def build_interview_graph():
    """Build and compile the LangGraph adaptive interview StateGraph."""
    workflow = StateGraph(InterviewGraphState)

    workflow.add_node("eval_knowledge", eval_knowledge_node)
    workflow.add_node("eval_comm", eval_comm_node)
    workflow.add_node("adaptive_decision", adaptive_decision_node)
    workflow.add_node("generate_next_question", generate_next_question_node)

    # Fan out candidate answer to both independent evaluators
    workflow.set_entry_point("eval_knowledge")
    workflow.add_edge("eval_knowledge", "eval_comm")
    workflow.add_edge("eval_comm", "adaptive_decision")
    workflow.add_edge("adaptive_decision", "generate_next_question")
    workflow.add_edge("generate_next_question", END)

    return workflow.compile()


interview_workflow_app = build_interview_graph()
