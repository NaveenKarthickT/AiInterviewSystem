import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.schemas.user import UserCreate
from app.api.v1.auth import register
from app.api.v1.resumes import list_user_resumes, get_resume_by_id, delete_resume
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node

Base.metadata.create_all(bind=engine)


def test_resume_api_flow():
    db = SessionLocal()
    test_email = "api_resume_candidate@test.com"
    
    try:
        # 1. Register candidate user
        existing = db.query(User).filter(User.email == test_email).first()
        if not existing:
            user_in = UserCreate(email=test_email, password="Password123!", full_name="Sam Morgan")
            token_res = register(user_in, db)
            user = db.query(User).filter(User.id == token_res.user.id).first()
        else:
            user = existing

        # 2. Simulate raw resume extracted text
        sample_text = """
        Sam Morgan
        sam.morgan@test.com | (555) 987-6543 | github.com/sammorgan
        
        Education:
        B.Tech in Computer Science, State Technical University, 2021 - 2025 (CGPA: 8.9/10)
        
        Skills:
        Languages: Python, Go, TypeScript, SQL
        Frameworks & Tools: FastAPI, React, Docker, Kubernetes, PostgreSQL, Redis, Git, Linux
        
        Projects:
        Distributed Event Streaming Broker
        - Designed in Go and Redis with Raft consensus algorithm.
        - Handled 50,000 events/sec with sub-5ms latency.
        
        Real-time Collaborative Whiteboard
        - Built with React, FastAPI, WebSocket, and PostgreSQL.
        - Scaled to 500 concurrent sessions using Docker and Kubernetes.
        """

        # 3. Test Agent extraction
        parsed_data = resume_parser_node.execute(sample_text)
        skills = skill_analysis_node.execute(parsed_data, sample_text)
        assert len(skills) > 0

        # 4. Save resume in DB
        resume = Resume(
            user_id=user.id,
            file_name="sam_morgan_resume.pdf",
            file_type="pdf",
            file_path="uploads/dummy_sam_morgan.pdf",
            raw_text=sample_text,
            parsed_data=parsed_data.model_dump(),
            extracted_skills=[s.model_dump() for s in skills],
            summary=parsed_data.executive_summary
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # 5. Test list endpoint
        resumes_list = list_user_resumes(db=db, current_user=user)
        assert len(resumes_list) >= 1
        assert any(r.id == resume.id for r in resumes_list)
        print(f"[SUCCESS] List user resumes returned {len(resumes_list)} item(s).")

        # 6. Test get by ID endpoint
        fetched = get_resume_by_id(resume_id=resume.id, db=db, current_user=user)
        assert fetched.id == resume.id
        assert fetched.parsed_data.full_name is not None
        assert len(fetched.extracted_skills) > 0
        print(f"[SUCCESS] Fetched resume {fetched.id} with {len(fetched.extracted_skills)} profiled skills.")

        # 7. Test delete endpoint
        delete_resume(resume_id=resume.id, db=db, current_user=user)
        deleted_check = db.query(Resume).filter(Resume.id == resume.id).first()
        assert deleted_check is None
        print("[SUCCESS] Resume successfully deleted.")

        print("\n=== ALL RESUME API ENDPOINT TESTS PASSED! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_resume_api_flow()
