import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.models.optimization import ResumeOptimization
from app.schemas.user import UserCreate
from app.schemas.interview import InterviewCreateRequest
from app.schemas.evaluation import TurnSubmitRequest
from app.schemas.optimization import ApplyApprovalRequest, OptimizationItem
from app.api.v1.auth import register
from app.api.v1.interviews import create_interview_session, submit_candidate_answer
from app.api.v1.optimization import generate_resume_optimization, approve_and_compile_resume
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

Base.metadata.create_all(bind=engine)


def test_resume_optimization_and_export():
    db = SessionLocal()
    test_email = "optimizer_candidate@test.com"

    try:
        # 1. Candidate setup
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            token_res = register(UserCreate(email=test_email, password="Password123!", full_name="Casey Engineer"), db)
            user = db.query(User).filter(User.id == token_res.user.id).first()

        # 2. Resume setup
        sample_resume_text = """
        Casey Engineer
        casey@engineer.com | (555) 345-6789 | github.com/caseyeng
        
        Summary:
        Motivated hard worker and quick learner seeking software opportunities.
        
        Education:
        B.Tech in Computer Science, 2021 - 2025
        
        Skills:
        Languages: Go, Python, SQL
        Tools: Docker, Kubernetes, PostgreSQL, Redis, Team Player
        
        Projects:
        Distributed Event Streaming Broker
        - Built key-value broker in Go and Redis.
        - Handled high concurrent traffic.
        """
        parsed_resume = resume_parser_node.execute(sample_resume_text)
        skills = skill_analysis_node.execute(parsed_resume, sample_resume_text)

        resume = Resume(
            user_id=user.id,
            file_name="casey_resume.pdf",
            file_type="pdf",
            file_path="uploads/casey.pdf",
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
            job_role="Distributed Systems Engineer",
            experience_level="junior",
            interaction_mode="text"
        )
        session = create_interview_session(request=req, db=db, current_user=user)
        turn_1 = session.turns[0]

        submit_res = submit_candidate_answer(
            session_id=session.id,
            turn_id=turn_1.id,
            submission=TurnSubmitRequest(
                candidate_answer="I engineered an in-memory event stream broker in Go and Redis to handle 50,000 events/sec with sub-5ms latency and zero packet loss."
            ),
            db=db,
            current_user=user
        )

        # 4. Generate Resume Optimization & Role Recommendations
        opt_res = generate_resume_optimization(session_id=session.id, db=db, current_user=user)
        assert opt_res is not None
        assert opt_res.session_id == session.id
        assert len(opt_res.item_recommendations) >= 3
        assert len(opt_res.job_role_recommendations) == 3

        actions = {i.recommended_action for i in opt_res.item_recommendations}
        print(f"[SUCCESS] Generated {len(opt_res.item_recommendations)} recommendation items with actions: {actions}")
        for item in opt_res.item_recommendations[:3]:
            print(f"  • [{item.recommended_action}] {item.section}: {item.reason}")
            if item.suggested_text:
                print(f"    Suggested STAR replacement: {item.suggested_text}")

        print(f"\n[SUCCESS] Job-Role Recommendations ({len(opt_res.job_role_recommendations)}):")
        for r in opt_res.job_role_recommendations:
            print(f"  • {r.role_title}: {r.match_percentage}% Match ({r.justification})")

        # 5. Candidate Approves Recommendations and Triggers ATS Export
        approval_req = ApplyApprovalRequest(
            items=opt_res.item_recommendations,
            custom_summary="Distributed Systems Engineer with verified expertise in Go, Redis, and high-throughput streaming architectures."
        )

        approved_res = approve_and_compile_resume(
            optimization_id=opt_res.id,
            approval_req=approval_req,
            db=db,
            current_user=user
        )

        assert approved_res.status == "approved"
        assert approved_res.exported_pdf_url is not None
        assert approved_res.exported_docx_url is not None

        # Verify physical files exist on disk
        db_opt = db.query(ResumeOptimization).filter(ResumeOptimization.id == opt_res.id).first()
        assert os.path.exists(db_opt.exported_docx_path)
        assert os.path.exists(db_opt.exported_pdf_path)

        print(f"\n[SUCCESS] ATS-compliant Export Verified:")
        print(f"  • DOCX: {db_opt.exported_docx_path} ({os.path.getsize(db_opt.exported_docx_path)} bytes)")
        print(f"  • PDF: {db_opt.exported_pdf_path} ({os.path.getsize(db_opt.exported_pdf_path)} bytes)")

        print("\n=== ALL RESUME OPTIMIZATION & ATS EXPORT TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_resume_optimization_and_export()
