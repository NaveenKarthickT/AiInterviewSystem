import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.models.report import SessionReport
from app.schemas.user import UserCreate
from app.schemas.interview import InterviewCreateRequest
from app.schemas.evaluation import TurnSubmitRequest
from app.api.v1.auth import register
from app.api.v1.interviews import create_interview_session, submit_candidate_answer
from app.api.v1.reports import get_session_report, list_user_reports
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

Base.metadata.create_all(bind=engine)


def test_performance_reporting_pipeline():
    db = SessionLocal()
    test_email = "reporting_candidate@test.com"

    try:
        # 1. Candidate setup
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            token_res = register(UserCreate(email=test_email, password="Password123!", full_name="Avery Analytics"), db)
            user = db.query(User).filter(User.id == token_res.user.id).first()

        # 2. Resume setup
        sample_resume_text = """
        Avery Analytics
        avery@test.com | github.com/averydev
        
        Education:
        B.Tech in Computer Science, 2021 - 2025
        
        Skills:
        Languages: Python, SQL, JavaScript
        Tools: FastAPI, React, PostgreSQL, Docker, Git
        
        Projects:
        Real-Time Metrics Monitoring Dashboard
        - Designed time-series telemetry aggregator in FastAPI and PostgreSQL.
        - Processed 10,000 metrics/min with interactive React Recharts dashboard.
        """
        parsed_resume = resume_parser_node.execute(sample_resume_text)
        skills = skill_analysis_node.execute(parsed_resume, sample_resume_text)

        resume = Resume(
            user_id=user.id,
            file_name="avery_resume.pdf",
            file_type="pdf",
            file_path="uploads/avery.pdf",
            raw_text=sample_resume_text,
            parsed_data=parsed_resume.model_dump(),
            extracted_skills=[s.model_dump() for s in skills],
            summary=parsed_resume.executive_summary
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # 3. Create Session & Answer Turn 1
        req = InterviewCreateRequest(
            resume_id=resume.id,
            job_role="Full Stack Performance Engineer",
            experience_level="junior",
            interaction_mode="text"
        )
        session = create_interview_session(request=req, db=db, current_user=user)
        turn_1 = session.turns[0]

        submit_req = TurnSubmitRequest(
            candidate_answer="I have built end-to-end telemetry pipelines connecting FastAPI backends to React frontend visualizations with PostgreSQL."
        )
        submit_res = submit_candidate_answer(
            session_id=session.id,
            turn_id=turn_1.id,
            submission=submit_req,
            db=db,
            current_user=user
        )

        # 4. Test Report Generation Endpoint
        report = get_session_report(session_id=session.id, db=db, current_user=user)
        assert report is not None
        assert report.session_id == session.id
        assert report.overall_knowledge_score > 0
        assert report.overall_comm_score > 0
        assert len(report.radar_metrics) == 6
        assert len(report.stage_breakdown) >= 1
        assert len(report.personalized_learning_plan) >= 1
        assert report.executive_summary is not None

        print(f"[SUCCESS] Generated Session Report:")
        print(f"  • Overall Tech Knowledge Score: {report.overall_knowledge_score}%")
        print(f"  • Overall Delivery Score: {report.overall_comm_score}%")
        print(f"  • Radar Dimensions ({len(report.radar_metrics)}):")
        for r in report.radar_metrics:
            print(f"    - {r.subject}: {r.candidate_score} (Benchmark: {r.benchmark_score})")
        print(f"  • Knowledge Gaps Identified: {len(report.knowledge_gaps)}")
        for g in report.knowledge_gaps[:2]:
            print(f"    - [{g.severity}] {g.topic}: {g.remedy_recommendation}")
        print(f"  • Personalized Learning Recommendations: {len(report.personalized_learning_plan)}")
        for l in report.personalized_learning_plan[:2]:
            print(f"    - {l.title} ({l.category}): {l.actionable_exercise}")

        # 5. Test List Reports History
        history = list_user_reports(db=db, current_user=user)
        assert len(history) >= 1
        print(f"[SUCCESS] Candidate report history returned {len(history)} record(s).")

        print("\n=== ALL PERFORMANCE REPORTING & GAP ANALYSIS TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_performance_reporting_pipeline()
