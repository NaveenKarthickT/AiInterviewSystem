import re
from typing import List, Dict
from app.schemas.resume import SkillEntity, ResumeParsedData
from app.agents.llm_factory import llm_factory


class SkillAnalysisNode:
    """Analyzes extracted resume sections to profile candidate skills,
    categorize competencies, evaluate claimed proficiency, and attach evidence.
    """

    SKILL_TAXONOMY: Dict[str, str] = {
        # Languages
        "python": "Languages", "javascript": "Languages", "typescript": "Languages",
        "java": "Languages", "c++": "Languages", "c#": "Languages", "go": "Languages",
        "rust": "Languages", "sql": "Languages", "html": "Languages", "css": "Languages",
        
        # Frameworks & Libraries
        "react": "Frameworks", "vue": "Frameworks", "angular": "Frameworks",
        "fastapi": "Frameworks", "django": "Frameworks", "flask": "Frameworks",
        "spring boot": "Frameworks", "express": "Frameworks", "node.js": "Frameworks",
        "next.js": "Frameworks", "tailwind css": "Frameworks", "pytorch": "AI & Data",
        "tensorflow": "AI & Data", "pandas": "AI & Data", "numpy": "AI & Data",

        # Databases & Storage
        "postgresql": "Databases", "mysql": "Databases", "mongodb": "Databases",
        "redis": "Databases", "sqlite": "Databases", "cassandra": "Databases",

        # Cloud & DevOps
        "docker": "Cloud & DevOps", "kubernetes": "Cloud & DevOps", "aws": "Cloud & DevOps",
        "azure": "Cloud & DevOps", "gcp": "Cloud & DevOps", "linux": "Cloud & DevOps",
        "ci/cd": "Cloud & DevOps", "git": "Developer Tools", "github": "Developer Tools",
        "rest apis": "Developer Tools", "graphql": "Developer Tools", "kafka": "Cloud & DevOps",
    }

    @classmethod
    def execute(cls, parsed_data: ResumeParsedData, raw_text: str) -> List[SkillEntity]:
        """Analyze skills and produce structured SkillEntity items."""
        llm = llm_factory.get_llm(temperature=0.0)
        
        if llm:
            try:
                skills = cls._analyze_with_llm(llm, parsed_data)
                if skills:
                    return skills
            except Exception as e:
                print(f"[WARN] LLM skill analysis failed: {e}. Using deterministic skill analyzer.")

        return cls._deterministic_skill_analysis(parsed_data, raw_text)

    @classmethod
    def _analyze_with_llm(cls, llm, parsed_data: ResumeParsedData) -> List[SkillEntity]:
        # Formulate prompt for LLM
        prompt = f"""You are a senior engineering recruiter and technical interviewer.
Analyze the following parsed resume profile. Identify each skill, determine its category,
estimate the candidate's self-reported proficiency level ('Beginner', 'Intermediate', 'Advanced'),
and extract brief evidence from their projects or experience.

Parsed Profile:
Technical Skills: {parsed_data.technical_skills}
Tools & Frameworks: {parsed_data.tools_and_frameworks}
Projects: {[p.model_dump() for p in parsed_data.projects]}
Experience: {[e.model_dump() for e in parsed_data.experience]}

Return ONLY a JSON list of objects matching:
[
  {{
    "name": "Skill Name",
    "category": "Languages | Frameworks | Databases | Cloud & DevOps | Developer Tools | AI & Data | Soft Skills",
    "proficiency": "Beginner | Intermediate | Advanced",
    "evidence_summary": "1 sentence showing where/how candidate used this skill"
  }}
]
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        
        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)
        
        import json
        items = json.loads(clean_json)
        return [SkillEntity(**item) for item in items]

    @classmethod
    def _deterministic_skill_analysis(cls, parsed_data: ResumeParsedData, raw_text: str) -> List[SkillEntity]:
        """Deterministic skill analyzer that inspects mentions and project contexts."""
        all_skills = list(dict.fromkeys(
            parsed_data.technical_skills + 
            parsed_data.tools_and_frameworks + 
            parsed_data.soft_skills
        ))

        analyzed: List[SkillEntity] = []

        for skill in all_skills:
            skill_lower = skill.lower()
            category = cls.SKILL_TAXONOMY.get(skill_lower, "Developer Tools")

            # Check evidence in projects
            evidence = []
            for proj in parsed_data.projects:
                proj_text = f"{proj.title} {' '.join(proj.technologies)} {proj.description}"
                if skill_lower in proj_text.lower():
                    evidence.append(f"Applied in project '{proj.title}'")

            # Check evidence in work experience
            for exp in parsed_data.experience:
                exp_text = f"{exp.company} {exp.role} {' '.join(exp.highlights)}"
                if skill_lower in exp_text.lower():
                    evidence.append(f"Demonstrated during {exp.role} at {exp.company}")

            # Determine proficiency based on evidence depth
            if len(evidence) >= 2:
                proficiency = "Advanced"
                evidence_summary = f"Substantiated across multiple contexts: {'; '.join(evidence[:2])}."
            elif len(evidence) == 1:
                proficiency = "Intermediate"
                evidence_summary = f"Practical application demonstrated: {evidence[0]}."
            else:
                proficiency = "Beginner"
                evidence_summary = "Listed in resume skill claims; candidate should prepare fundamental conceptual defense."

            analyzed.append(SkillEntity(
                name=skill,
                category=category,
                proficiency=proficiency,
                evidence_summary=evidence_summary
            ))

        return analyzed


skill_analysis_node = SkillAnalysisNode()
