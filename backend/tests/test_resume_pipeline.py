import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.services.document_parser import document_parser
from app.agents.nodes.resume_parser_node import resume_parser_node
from app.agents.nodes.skill_analysis_node import skill_analysis_node
from app.schemas.resume import ResumeParsedData

# Ensure all tables exist
Base.metadata.create_all(bind=engine)


def create_sample_docx(file_path: str):
    """Helper to create a realistic mock candidate resume DOCX file."""
    import docx
    doc = docx.Document()
    doc.add_heading("Alex Rivera - Full Stack & Systems Engineer", 0)
    doc.add_paragraph("alex.rivera@example.com | (555) 019-2834 | github.com/alexrivera | San Francisco, CA")
    
    doc.add_heading("Education", level=1)
    doc.add_paragraph("B.Tech in Computer Science & Engineering | National Institute of Technology | 2021 - 2025")
    
    doc.add_heading("Technical Skills", level=1)
    doc.add_paragraph("Languages: Python, Go, TypeScript, SQL, C++")
    doc.add_paragraph("Frameworks & Tools: React, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, Git, Linux")
    
    doc.add_heading("Key Engineering Projects", level=1)
    doc.add_heading("High-Throughput Distributed Cache & Event Stream", level=2)
    doc.add_paragraph("Engineered an asynchronous in-memory key-value cache in Go and Redis with Raft consensus. Handled 45,000 requests/sec with p99 latency under 2ms.")
    
    doc.add_heading("AI Adaptive Knowledge Graph Platform", level=2)
    doc.add_paragraph("Architected a full-stack platform using FastAPI, React, and PostgreSQL. Integrated vector embeddings and automated real-time question generation.")
    
    doc.add_heading("Work Experience", level=1)
    doc.add_paragraph("Backend Engineering Intern | CloudTech Solutions | June 2024 - August 2024")
    doc.add_paragraph("- Optimized microservices database queries in PostgreSQL, reducing average endpoint response times by 35%.")
    doc.add_paragraph("- Automated Docker container build workflows with GitHub Actions CI/CD pipelines.")

    doc.save(file_path)


def test_resume_pipeline():
    test_docx_path = os.path.join(os.path.dirname(__file__), "sample_test_resume.docx")
    create_sample_docx(test_docx_path)
    
    print("[TEST] 1. Testing Document Extraction from DOCX...")
    raw_text = document_parser.parse_document(test_docx_path, "docx")
    assert raw_text is not None
    assert "Alex Rivera" in raw_text
    assert "FastAPI" in raw_text
    assert "PostgreSQL" in raw_text
    print(f"[SUCCESS] Extracted {len(raw_text)} characters from DOCX.")

    print("[TEST] 2. Testing AI Resume Parser Node...")
    parsed_data: ResumeParsedData = resume_parser_node.execute(raw_text)
    assert parsed_data.email is not None
    assert "alex.rivera@example.com" in parsed_data.email
    assert len(parsed_data.technical_skills) > 0
    assert len(parsed_data.projects) > 0
    print(f"[SUCCESS] Parsed Candidate: {parsed_data.full_name}, Email: {parsed_data.email}")
    print(f"[SUCCESS] Parsed Skills: {parsed_data.technical_skills}")
    print(f"[SUCCESS] Parsed Projects: {[p.title for p in parsed_data.projects]}")

    print("[TEST] 3. Testing Skill Analysis & Profiling Node...")
    skills = skill_analysis_node.execute(parsed_data, raw_text)
    assert len(skills) > 0
    categories = {s.category for s in skills}
    proficiencies = {s.proficiency for s in skills}
    print(f"[SUCCESS] Extracted {len(skills)} profiled skills across categories: {categories}")
    print(f"[SUCCESS] Found proficiency tiers: {proficiencies}")
    for s in skills[:3]:
        print(f"  • {s.name} ({s.category} - {s.proficiency}): {s.evidence_summary}")

    print("[TEST] 4. Testing Database Persistence...")
    db = SessionLocal()
    try:
        # Get or create test user
        user = db.query(User).filter(User.email == "resume_test_user@test.com").first()
        if not user:
            user = User(
                email="resume_test_user@test.com",
                hashed_password="dummyhashedpassword",
                full_name="Resume Test User"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        resume = Resume(
            user_id=user.id,
            file_name="sample_test_resume.docx",
            file_type="docx",
            file_path=test_docx_path,
            raw_text=raw_text,
            parsed_data=parsed_data.model_dump(),
            extracted_skills=[s.model_dump() for s in skills],
            summary=parsed_data.executive_summary
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        print(f"[SUCCESS] Resume record saved with ID: {resume.id}")

        # Fetch and verify
        saved_resume = db.query(Resume).filter(Resume.id == resume.id).first()
        assert saved_resume is not None
        assert saved_resume.parsed_data["full_name"] is not None
        assert len(saved_resume.extracted_skills) == len(skills)
        print("[SUCCESS] Resume JSON data accurately retrieved from DB.")
    finally:
        db.close()
        # Clean up test file
        if os.path.exists(test_docx_path):
            os.remove(test_docx_path)

    print("\n=== ALL RESUME EXTRACTION & SKILL PROFILING TESTS PASSED! ===")


if __name__ == "__main__":
    test_resume_pipeline()
