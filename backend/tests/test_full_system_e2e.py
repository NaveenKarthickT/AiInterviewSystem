import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import InterviewSession, InterviewTurn
from app.models.evaluation import DualEvaluation
from app.models.report import SessionReport
from app.models.optimization import ResumeOptimization
from app.schemas.user import UserCreate
from app.schemas.resume import ResumeParsedData, SkillEntity
from app.schemas.interview import InterviewCreateRequest
from app.schemas.optimization import ApplyApprovalRequest, OptimizationItem
from app.api.v1.auth import register
from app.api.v1.resumes import upload_resume
from app.api.v1.interviews import create_interview_session, submit_candidate_answer
from app.api.v1.optimization import generate_resume_optimization, approve_and_compile_resume

# Helper to simulate file upload
class DummyUploadFile:
    def __init__(self, filename, content_bytes):
        self.filename = filename
        self.file = content_bytes

    async def read(self):
        return self.file

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

def test_full_candidate_journey():
    db = SessionLocal()
    test_email = "e2e_full_journey@test.com"

    # 1. Register user
    token_res = register(UserCreate(email=test_email, password="Password123!", full_name="E2E Tester"), db)
    user = db.query(User).filter(User.id == token_res.user.id).first()
    assert user is not None

    # 2. Create a dummy resume (PDF content simulated as plain text)
    sample_text = """John Doe\njohn@example.com\nSummary: Experienced developer\nSkills: Python, FastAPI, React\nProjects:\n - AI Interview System\n"""
    dummy_file = DummyUploadFile("resume.txt", sample_text.encode('utf-8'))
    # Directly call the upload logic (bypass FastAPI request handling)
    # Save file manually to match upload_resume expectations
    # We'll mimic the function steps here for simplicity
    from app.services.document_parser import document_parser
    from app.agents.nodes.resume_parser_node import resume_parser_node
    from app.agents.nodes.skill_analysis_node import skill_analysis_node
    from app.core.config import settings
    import uuid, shutil

    # Save dummy file
    unique_filename = f"{uuid.uuid4().hex}_{dummy_file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(sample_text.encode('utf-8'))

    raw_text = document_parser.parse_document(file_path, os.path.splitext(dummy_file.filename)[1])
    parsed_data: ResumeParsedData = resume_parser_node.execute(raw_text)
    extracted_skills: list[SkillEntity] = skill_analysis_node.execute(parsed_data, raw_text)

    new_resume = Resume(
        user_id=user.id,
        file_name=dummy_file.filename,
        file_type="txt",
        file_path=file_path,
        raw_text=raw_text,
        parsed_data=parsed_data.model_dump(),
        extracted_skills=[s.model_dump() for s in extracted_skills],
        summary=parsed_data.executive_summary,
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    assert new_resume.id is not None

    # 3. Create interview session
    interview_req = InterviewCreateRequest(
        resume_id=new_resume.id,
        job_role="Software Engineer",
        experience_level="junior",
        interaction_mode="text",
        selected_stages=None,
    )
    session_resp = create_interview_session(interview_req, db, user)
    session_id = session_resp.id
    assert session_id is not None

    # 4. Submit three turns (simulate simple answers)
    for i in range(1, 4):
        turn = db.query(InterviewTurn).filter(
            InterviewTurn.session_id == session_id, InterviewTurn.turn_number == i
        ).first()
        assert turn is not None
        submit_resp = submit_candidate_answer(
            session_id=session_id,
            turn_id=turn.id,
            submission=type('obj', (), {'candidate_answer': f"Answer {i}", 'audio_answer_url': None})(),
            db=db,
            current_user=user,
        )
        # Ensure evaluation created
        eval_obj = db.query(DualEvaluation).filter(DualEvaluation.turn_id == turn.id).first()
        assert eval_obj is not None
        assert eval_obj.knowledge_score > 0
        assert eval_obj.comm_score > 0

    # 5. Generate performance report
    report = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
    if not report:
        # Trigger generation via API call
        from app.api.v1.reports import get_session_report
        report_resp = get_session_report(session_id, db, user)
        report = db.query(SessionReport).filter(SessionReport.session_id == session_id).first()
    assert report is not None
    assert report.radar_metrics
    assert report.knowledge_gaps is not None
    assert report.personalized_learning_plan is not None

    # 6. Generate resume optimization
    opt_resp = generate_resume_optimization(session_id, db, user)
    opt_id = opt_resp.id
    assert opt_id is not None
    # 7. Approve all KEEP items (simplified)
    approved_items = []
    for item in opt_resp.item_recommendations:
        approved_items.append(OptimizationItem(
            id=item.id,
            section=item.section,
            original_text=item.original_text,
            suggested_text=item.suggested_text,
            recommended_action=item.recommended_action,
            approved=True,
        ))
    approval_req = ApplyApprovalRequest(
        items=approved_items,
        custom_summary=None,
    )
    final_opt = approve_and_compile_resume(opt_id, approval_req, db, user)
    assert final_opt.status == "approved"
    # Verify exported files exist
    assert os.path.exists(final_opt.exported_pdf_url.split('/')[-1]) or os.path.exists(final_opt.exported_docx_url.split('/')[-1])

    print("END-TO-END TEST PASSED")

if __name__ == "__main__":
    test_full_candidate_journey()
