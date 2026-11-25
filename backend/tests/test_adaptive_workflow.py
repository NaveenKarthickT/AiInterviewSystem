import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.schemas.user import UserCreate
from app.schemas.interview import InterviewCreateRequest
from app.schemas.evaluation import TurnSubmitRequest
from app.api.v1.auth import register
from app.api.v1.interviews import create_interview_session, submit_candidate_answer
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

Base.metadata.create_all(bind=engine)


def test_adaptive_interview_workflow_and_dual_evaluation():
    db = SessionLocal()
    test_email = "workflow_candidate@test.com"

    try:
        # 1. Candidate setup
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            token_res = register(UserCreate(email=test_email, password="Password123!", full_name="Morgan DevOps"), db)
            user = db.query(User).filter(User.id == token_res.user.id).first()

        # 2. Candidate resume setup
        sample_resume_text = """
        Morgan DevOps
        morgan@devops.com | github.com/morgandevops
        
        Education:
        B.Tech in Computer Science & Engineering, 2021 - 2025
        
        Skills:
        Languages: Go, Python, SQL, Bash
        DevOps & Cloud: Docker, Kubernetes, AWS, Terraform, CI/CD, Prometheus, Linux
        
        Projects:
        Kubernetes Multi-Cluster GitOps Engine
        - Automated declarative deployment across 5 staging clusters using ArgoCD and Helm.
        - Reduced deployment downtime to zero with automated canary rollouts and health probes.
        """
        parsed_resume = resume_parser_node.execute(sample_resume_text)
        skills = skill_analysis_node.execute(parsed_resume, sample_resume_text)

        resume = Resume(
            user_id=user.id,
            file_name="morgan_resume.pdf",
            file_type="pdf",
            file_path="uploads/morgan.pdf",
            raw_text=sample_resume_text,
            parsed_data=parsed_resume.model_dump(),
            extracted_skills=[s.model_dump() for s in skills],
            summary=parsed_resume.executive_summary
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # 3. Create Interview Session
        req = InterviewCreateRequest(
            resume_id=resume.id,
            job_role="Site Reliability / Cloud Engineer",
            experience_level="junior",
            interaction_mode="text"
        )
        session = create_interview_session(request=req, db=db, current_user=user)
        turn_1 = session.turns[0]
        print(f"[SUCCESS] Interview session initialized: {session.id}")
        print(f"[SUCCESS] Turn 1 Question ({turn_1.stage}): {turn_1.question_text}")

        # 4. Submit Answer for Turn 1 (Intro)
        # We simulate a candidate who has good technical passion, but short informal grammar
        candidate_answer = (
            "Hi, I've been doing cloud infrastructure and Linux scripting for around 3 years during college. "
            "I built an automated GitOps deployment cluster using ArgoCD and Kubernetes because manual deployments "
            "kept breaking configs. I'm really excited about Site Reliability Engineering because I love diagnosing "
            "distributed failures, optimizing observability pipelines, and preventing customer downtime."
        )

        submit_req = TurnSubmitRequest(candidate_answer=candidate_answer)
        res = submit_candidate_answer(
            session_id=session.id,
            turn_id=turn_1.id,
            submission=submit_req,
            db=db,
            current_user=user
        )

        # 5. Verify Dual Evaluation Independence
        eval_data = res.evaluation
        assert eval_data is not None
        assert 0.0 <= eval_data.knowledge.knowledge_score <= 100.0
        assert 0.0 <= eval_data.communication.comm_score <= 100.0
        assert eval_data.knowledge.knowledge_feedback != ""
        assert eval_data.communication.structure_feedback != ""

        print(f"\n[DUAL EVALUATION RESULTS]")
        print(f"  • Knowledge Score: {eval_data.knowledge.knowledge_score}/100")
        print(f"    - Correctness: {eval_data.knowledge.technical_correctness}/30")
        print(f"    - Depth: {eval_data.knowledge.conceptual_depth}/25")
        print(f"    - Feedback: {eval_data.knowledge.knowledge_feedback}")
        print(f"  • Communication Score: {eval_data.communication.comm_score}/100")
        print(f"    - Clarity: {eval_data.communication.clarity_score}/30")
        print(f"    - Structure Feedback: {eval_data.communication.structure_feedback}")

        # 6. Verify Adaptive Progression to Turn 2
        assert res.next_turn is not None
        assert res.next_turn.turn_number == 2
        print(f"\n[ADAPTIVE PROGRESSION]")
        print(f"  • Next Turn Generated: #{res.next_turn.turn_number} (Stage: {res.next_turn.stage}, Difficulty: {res.next_turn.difficulty_level})")
        print(f"  • Next Question: {res.next_turn.question_text}")

        # 7. Verify Database Persistence of Evaluation
        db_eval = db.query(DualEvaluation).filter(DualEvaluation.turn_id == turn_1.id).first()
        assert db_eval is not None
        assert db_eval.knowledge_score == eval_data.knowledge.knowledge_score
        assert db_eval.comm_score == eval_data.communication.comm_score

        # Verify Session Running Averages Updated
        db_session = db.query(InterviewSession).filter(InterviewSession.id == session.id).first()
        assert db_session.avg_knowledge_score > 0
        assert db_session.avg_comm_score > 0
        print(f"[SUCCESS] Database session running averages: Know={db_session.avg_knowledge_score}, Comm={db_session.avg_comm_score}")

        print("\n=== ALL LANGGRAPH WORKFLOW & DUAL EVALUATION TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_adaptive_interview_workflow_and_dual_evaluation()
