import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.schemas.user import UserCreate
from app.schemas.interview import InterviewCreateRequest
from app.api.v1.auth import register
from app.api.v1.interviews import create_interview_session, list_user_interviews, get_interview_session, get_current_turn
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

Base.metadata.create_all(bind=engine)


def test_interview_planning_and_question_generation():
    db = SessionLocal()
    test_email = "planner_candidate@test.com"

    try:
        # 1. Setup user
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            token_res = register(UserCreate(email=test_email, password="Password123!", full_name="Taylor Swift-Dev"), db)
            user = db.query(User).filter(User.id == token_res.user.id).first()

        # 2. Setup resume
        sample_resume_text = """
        Taylor Swift-Dev
        taylor@test.com | github.com/taylordev
        
        Education:
        B.S. in Computer Science, Tech University, 2021 - 2025
        
        Skills:
        Languages: Go, Python, SQL, C++
        Tools: Docker, Kubernetes, PostgreSQL, Redis, Kafka, Linux
        
        Projects:
        Raft Consensus Key-Value Store
        - Implemented Raft consensus in Go from scratch.
        - Supported log replication, leader election, and high-availability failover.
        """
        parsed_resume = resume_parser_node.execute(sample_resume_text)
        skills = skill_analysis_node.execute(parsed_resume, sample_resume_text)

        resume = Resume(
            user_id=user.id,
            file_name="taylor_resume.pdf",
            file_type="pdf",
            file_path="uploads/taylor.pdf",
            raw_text=sample_resume_text,
            parsed_data=parsed_resume.model_dump(),
            extracted_skills=[s.model_dump() for s in skills],
            summary=parsed_resume.executive_summary
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # 3. Test Session Creation with Planner Agent
        req = InterviewCreateRequest(
            resume_id=resume.id,
            job_role="Distributed Backend Engineer",
            experience_level="junior",
            interaction_mode="text"
        )

        session_res = create_interview_session(request=req, db=db, current_user=user)
        assert session_res.id is not None
        assert session_res.job_role == "Distributed Backend Engineer"
        assert session_res.status == "in_progress"
        assert session_res.planned_trajectory is not None
        assert len(session_res.planned_trajectory.stages) == 7
        assert session_res.current_turn_count == 1
        assert len(session_res.turns) == 1

        first_turn = session_res.turns[0]
        assert first_turn.turn_number == 1
        assert first_turn.stage == "intro"
        assert "Distributed Backend Engineer" in first_turn.question_text or "engineering background" in first_turn.question_text
        print(f"[SUCCESS] Trajectory planned with {len(session_res.planned_trajectory.stages)} stages.")
        print(f"[SUCCESS] Turn #1 Question: {first_turn.question_text}")

        # 4. Test List sessions endpoint
        sessions_list = list_user_interviews(db=db, current_user=user)
        assert len(sessions_list) >= 1
        print(f"[SUCCESS] List interviews returned {len(sessions_list)} session(s).")

        # 5. Test Get session details
        fetched_session = get_interview_session(session_id=session_res.id, db=db, current_user=user)
        assert fetched_session.id == session_res.id
        assert fetched_session.planned_trajectory.session_summary is not None
        print(f"[SUCCESS] Fetched session with summary: {fetched_session.planned_trajectory.session_summary}")

        # 6. Test Get current turn
        curr_turn = get_current_turn(session_id=session_res.id, db=db, current_user=user)
        assert curr_turn.id == first_turn.id
        assert curr_turn.question_text == first_turn.question_text
        print(f"[SUCCESS] Current turn correctly retrieved: Turn #{curr_turn.turn_number} ({curr_turn.stage})")

        print("\n=== ALL INTERVIEW PLANNING & QUESTION GENERATION TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_interview_planning_and_question_generation()
