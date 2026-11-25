import os
import uuid
from typing import Dict, Any, Optional
from app.core.config import settings


class ExportService:
    """Service generating standardized, ATS-compliant single-column PDF and DOCX resumes."""

    @staticmethod
    def generate_docx(resume_content: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """Generate ATS-friendly DOCX resume using python-docx."""
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if not output_filename:
            output_filename = f"resume_{uuid.uuid4().hex}.docx"

        output_path = os.path.abspath(os.path.join(settings.EXPORT_DIR, output_filename))
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)

        doc = docx.Document()

        # Page Margins (0.75 in for standard ATS)
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

        # 1. Header (Name & Contact)
        name = resume_content.get("full_name") or "Candidate"
        p_name = doc.add_paragraph()
        run_name = p_name.add_run(name)
        run_name.font.size = Pt(20)
        run_name.font.bold = True
        run_name.font.color.rgb = RGBColor(15, 23, 42)
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER

        contacts = []
        if resume_content.get("email"):
            contacts.append(resume_content["email"])
        if resume_content.get("phone"):
            contacts.append(resume_content["phone"])
        if resume_content.get("github"):
            contacts.append(resume_content["github"])
        if resume_content.get("linkedin"):
            contacts.append(resume_content["linkedin"])

        if contacts:
            p_contact = doc.add_paragraph(" | ".join(contacts))
            p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p_contact.runs:
                p_contact.runs[0].font.size = Pt(9.5)
                p_contact.runs[0].font.color.rgb = RGBColor(71, 85, 105)

        def add_section_header(title: str):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(title.upper())
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor(30, 41, 59)

        # 2. Executive Summary
        if resume_content.get("summary"):
            add_section_header("Professional Summary")
            p_sum = doc.add_paragraph(resume_content["summary"])
            if p_sum.runs:
                p_sum.runs[0].font.size = Pt(10)

        # 3. Technical Skills
        skills = resume_content.get("skills", [])
        if skills:
            add_section_header("Technical Competencies")
            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            p_sk = doc.add_paragraph()
            r_sk = p_sk.add_run(skills_str)
            r_sk.font.size = Pt(9.5)

        # 4. Projects
        projects = resume_content.get("projects", [])
        if projects:
            add_section_header("Engineering Projects")
            for proj in projects:
                p_proj = doc.add_paragraph()
                p_proj.paragraph_format.space_before = Pt(4)
                p_proj.paragraph_format.space_after = Pt(1)

                title_run = p_proj.add_run(proj.get("title") or "Project")
                title_run.bold = True
                title_run.font.size = Pt(10)

                techs = proj.get("technologies", [])
                if techs:
                    tech_str = ", ".join(techs) if isinstance(techs, list) else str(techs)
                    t_run = p_proj.add_run(f" | {tech_str}")
                    t_run.italic = True
                    t_run.font.size = Pt(9)
                    t_run.font.color.rgb = RGBColor(71, 85, 105)

                desc = proj.get("description", "")
                if desc:
                    p_desc = doc.add_paragraph(f"- {desc}")
                    if p_desc.runs:
                        p_desc.runs[0].font.size = Pt(9.5)

        # 5. Experience
        experience = resume_content.get("experience", [])
        if experience:
            add_section_header("Experience & Internships")
            for exp in experience:
                p_exp = doc.add_paragraph()
                r_title = p_exp.add_run(f"{exp.get('role', 'Engineer')} - {exp.get('company', 'Company')}")
                r_title.bold = True
                r_title.font.size = Pt(10)

                if exp.get("duration"):
                    r_dur = p_exp.add_run(f" ({exp['duration']})")
                    r_dur.italic = True
                    r_dur.font.size = Pt(9)

                for hl in exp.get("highlights", []):
                    p_hl = doc.add_paragraph(f"- {hl}")
                    if p_hl.runs:
                        p_hl.runs[0].font.size = Pt(9.5)

        # 6. Education
        education = resume_content.get("education", [])
        if education:
            add_section_header("Education")
            for edu in education:
                p_edu = doc.add_paragraph()
                r_deg = p_edu.add_run(f"{edu.get('degree', 'Degree')} - {edu.get('institution', 'University')}")
                r_deg.font.size = Pt(9.5)
                if edu.get("year"):
                    r_yr = p_edu.add_run(f" ({edu['year']})")
                    r_yr.italic = True
                    r_yr.font.size = Pt(9)

        doc.save(output_path)
        return output_path

    @staticmethod
    def generate_pdf(resume_content: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """Generate ATS-friendly PDF resume using PyMuPDF (fitz)."""
        import fitz  # PyMuPDF

        if not output_filename:
            output_filename = f"resume_{uuid.uuid4().hex}.pdf"

        output_path = os.path.abspath(os.path.join(settings.EXPORT_DIR, output_filename))
        os.makedirs(settings.EXPORT_DIR, exist_ok=True)

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # Standard A4 (points)

        margin_left = 50
        margin_right = 545
        margin_top = 45
        max_y = 780
        y = margin_top

        def check_page_overflow(required_space: float = 30):
            nonlocal page, y
            if y + required_space > max_y:
                page = doc.new_page(width=595, height=842)
                y = margin_top

        # 1. Header Name
        name = resume_content.get("full_name") or "Candidate Name"
        page.insert_text(fitz.Point(margin_left, y), str(name), fontsize=18, fontname="helv", color=(0.06, 0.09, 0.16))
        y += 22

        # 2. Contact details
        contacts = []
        if resume_content.get("email"): contacts.append(str(resume_content["email"]))
        if resume_content.get("phone"): contacts.append(str(resume_content["phone"]))
        if resume_content.get("github"): contacts.append(str(resume_content["github"]))
        if resume_content.get("linkedin"): contacts.append(str(resume_content["linkedin"]))
        if contacts:
            page.insert_text(fitz.Point(margin_left, y), " | ".join(contacts), fontsize=9, fontname="helv", color=(0.28, 0.33, 0.41))
            y += 20

        def draw_divider(curr_y):
            page.draw_line(fitz.Point(margin_left, curr_y), fitz.Point(margin_right, curr_y), color=(0.7, 0.7, 0.8), width=0.5)
            return curr_y + 14

        # 3. Summary
        if resume_content.get("summary"):
            check_page_overflow(60)
            page.insert_text(fitz.Point(margin_left, y), "PROFESSIONAL SUMMARY", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.3))
            y = draw_divider(y + 4)
            sum_text = str(resume_content["summary"])
            rect = fitz.Rect(margin_left, y, margin_right, y + 45)
            page.insert_textbox(rect, sum_text, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
            y += 50

        # 4. Verified Skills
        skills = resume_content.get("skills", [])
        if skills:
            check_page_overflow(50)
            page.insert_text(fitz.Point(margin_left, y), "TECHNICAL COMPETENCIES", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.3))
            y = draw_divider(y + 4)
            sk_text = ", ".join(skills) if isinstance(skills, list) else str(skills)
            rect = fitz.Rect(margin_left, y, margin_right, y + 35)
            page.insert_textbox(rect, sk_text, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
            y += 40

        # 5. Projects
        projects = resume_content.get("projects", [])
        if projects:
            check_page_overflow(60)
            page.insert_text(fitz.Point(margin_left, y), "ENGINEERING PROJECTS", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.3))
            y = draw_divider(y + 4)
            for proj in projects[:4]:
                check_page_overflow(45)
                title = proj.get("title") or "Project"
                techs = ", ".join(proj.get("technologies", [])) if isinstance(proj.get("technologies"), list) else str(proj.get("technologies") or "")
                header_text = f"{title} ({techs})" if techs else title
                page.insert_text(fitz.Point(margin_left, y), header_text, fontsize=10, fontname="helv", color=(0.1, 0.2, 0.4))
                y += 14

                desc = proj.get("description", "")
                if desc:
                    rect = fitz.Rect(margin_left + 10, y, margin_right, y + 32)
                    page.insert_textbox(rect, f"- {desc}", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
                    y += 34

        # 6. Education
        education = resume_content.get("education", [])
        if education:
            check_page_overflow(40)
            page.insert_text(fitz.Point(margin_left, y), "EDUCATION", fontsize=11, fontname="helv", color=(0.1, 0.1, 0.3))
            y = draw_divider(y + 4)
            for edu in education:
                check_page_overflow(20)
                deg = edu.get("degree") or "Degree"
                inst = edu.get("institution") or "University"
                yr = f" ({edu['year']})" if edu.get("year") else ""
                page.insert_text(fitz.Point(margin_left, y), f"{deg} - {inst}{yr}", fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
                y += 18

        doc.save(output_path)
        doc.close()
        return output_path


export_service = ExportService()
