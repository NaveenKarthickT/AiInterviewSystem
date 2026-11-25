import json
import re
from typing import List, Dict, Any, Optional
from app.schemas.interview import InterviewTrajectory, StagePlan
from app.schemas.resume import ResumeParsedData, SkillEntity
from app.agents.llm_factory import llm_factory


class InterviewPlannerNode:
    """Agent responsible for architecting the candidate's custom 7-stage
    recruitment interview trajectory based on resume competencies and target role.
    """

    STAGES_METADATA = [
        {
            "stage": "intro",
            "title": "Introduction & Career Orientation",
            "default_goal": "Understand engineering background, career goals, and alignment with target role.",
        },
        {
            "stage": "skill_verification",
            "title": "Resume Skill Verification",
            "default_goal": "Directly probe and verify accuracy of claimed skills and frameworks listed on resume.",
        },
        {
            "stage": "technical",
            "title": "Core Technical Knowledge",
            "default_goal": "Evaluate conceptual depth, internals, and theoretical foundations relevant to role.",
        },
        {
            "stage": "problem_solving",
            "title": "Problem-Solving & System Design",
            "default_goal": "Assess analytical breakdown, trade-off analysis, edge-case handling, and algorithmic reasoning.",
        },
        {
            "stage": "project_discussion",
            "title": "Project Architecture Deep Dive",
            "default_goal": "Probe candidate's personal architectural contributions, technical roadblocks, and metric validity.",
        },
        {
            "stage": "experience_discussion",
            "title": "Engineering Experience & Collaboration",
            "default_goal": "Investigate real-world software practices: CI/CD, testing, code reviews, and production troubleshooting.",
        },
        {
            "stage": "behavioral_hr",
            "title": "Behavioral & Situational Judgment",
            "default_goal": "Assess teamwork, conflict resolution, ownership, and learning mindset.",
        },
    ]

    @classmethod
    def execute(
        cls,
        parsed_resume: ResumeParsedData,
        extracted_skills: List[SkillEntity],
        job_role: str,
        experience_level: str = "junior",
        selected_stages: Optional[List[str]] = None,
        interview_type: str = "resume",
        focus_topic: Optional[str] = None,
    ) -> InterviewTrajectory:
        """Create structured interview trajectory matching candidate profile to role or topic."""
        llm = llm_factory.get_llm(temperature=0.2)

        if llm:
            try:
                trajectory = cls._plan_with_llm(
                    llm,
                    parsed_resume,
                    extracted_skills,
                    job_role,
                    experience_level,
                    selected_stages,
                    interview_type,
                    focus_topic,
                )
                if trajectory:
                    return trajectory
            except Exception as e:
                print(f"[WARN] LLM trajectory planning failed: {e}. Using deterministic planner.")

        return cls._deterministic_plan(
            parsed_resume,
            extracted_skills,
            job_role,
            experience_level,
            selected_stages,
            interview_type,
            focus_topic,
        )

    @classmethod
    def _plan_with_llm(
        cls,
        llm,
        resume: ResumeParsedData,
        skills: List[SkillEntity],
        role: str,
        level: str,
        selected_stages: Optional[List[str]],
        interview_type: str = "resume",
        focus_topic: Optional[str] = None,
    ) -> Optional[InterviewTrajectory]:
        stage_names = selected_stages or [s["stage"] for s in cls.STAGES_METADATA]

        if interview_type == "topic" and focus_topic:
            focus_directive = (
                f"MODE: TOPIC-BASED INTERVIEW.\n"
                f"The core subject of this entire interview is: '{focus_topic}'.\n"
                f"Every single stage must rigorously evaluate the candidate on '{focus_topic}', "
                f"ranging from foundational mechanics to distributed scale and failure modes."
            )
        elif interview_type == "role":
            focus_directive = (
                f"MODE: ROLE-BASED INTERVIEW.\n"
                f"The interview is built around the core competencies, systems, and day-to-day responsibilities "
                f"of a {level} '{role}'. Ensure each stage probes real-world responsibilities and domain depth."
            )
        else:
            focus_directive = (
                f"MODE: RESUME-BASED INTERVIEW.\n"
                f"Anchor the trajectory to the candidate's actual projects, claims, and verified skills."
            )

        prompt = f"""You are a Lead Principal Technical Recruiter and Staff Software Engineer.
Design a highly tailored, non-generic interview trajectory for this candidate targeting the role of '{role}' ({level} level).

{focus_directive}

Candidate Profile:
- Name: {resume.full_name}
- Focus / Extracted Skills: {[s.name for s in skills[:15]]}
- Key Projects: {[p.title + ': ' + ', '.join(p.technologies) for p in resume.projects[:3]] if resume.projects else ['Domain projects']}
- Work Experience: {[e.company + ' (' + e.role + ')' for e in resume.experience[:2]] if resume.experience else ['Relevant engineering experience']}

Required Stages to Plan: {stage_names}

Strictly output a valid JSON object matching:
{{
  "session_summary": "1-2 sentences outlining interview focus and strategy",
  "candidate_fit_notes": "Synthesis of candidate strengths vs target role/topic gaps to test",
  "stages": [
    {{
      "stage": "stage_id",
      "title": "Stage Display Title",
      "focus_goal": "Specific goal for this candidate",
      "target_skills_or_topics": ["Specific Tech 1", "Specific Topic 2"],
      "estimated_questions": 2
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)
        return InterviewTrajectory(**data)

    @classmethod
    def _deterministic_plan(
        cls,
        resume: ResumeParsedData,
        skills: List[SkillEntity],
        role: str,
        level: str,
        selected_stages: Optional[List[str]],
        interview_type: str = "resume",
        focus_topic: Optional[str] = None,
    ) -> InterviewTrajectory:
        active_stages = selected_stages or [s["stage"] for s in cls.STAGES_METADATA]
        top_skills = [s.name for s in skills[:6]] or ["Python", "FastAPI", "SQL", "Docker"]
        top_project = resume.projects[0].title if resume.projects else "Primary Engineering System"

        plans: List[StagePlan] = []
        for meta in cls.STAGES_METADATA:
            if meta["stage"] not in active_stages:
                continue

            stage = meta["stage"]
            if interview_type == "topic" and focus_topic:
                if stage == "intro":
                    topics = [f"{focus_topic} Foundations", "Production Usage", "Architecture Preferences"]
                    goal = f"Assess conceptual familiarity and real-world exposure to {focus_topic}."
                elif stage == "skill_verification":
                    topics = [f"{focus_topic} Core Mechanics", "API & Invariant Design", "State Guarantees"]
                    goal = f"Directly evaluate deep fundamental mechanics and mental models in {focus_topic}."
                elif stage == "technical":
                    topics = [f"{focus_topic} Internals", "Memory & Concurrency Model", "Algorithmic Complexity"]
                    goal = f"Probe low-level mechanics, data structures, and algorithmic invariants in {focus_topic}."
                elif stage == "problem_solving":
                    topics = [f"{focus_topic} Bottleneck Analysis", "High-Throughput Scenarios", "Failure Recovery"]
                    goal = f"Examine problem breakdown and algorithmic architecture applied to {focus_topic}."
                elif stage == "project_discussion":
                    topics = [f"{focus_topic} Production Architecture", "Benchmarking & Profiling", "Trade-offs"]
                    goal = f"Evaluate real-world system architecture, design decisions, and metrics involving {focus_topic}."
                elif stage == "experience_discussion":
                    topics = [f"Debugging {focus_topic} Outages", "Observability & Metrics", "Deployment Patterns"]
                    goal = f"Investigate production troubleshooting, monitoring, and live maintenance of {focus_topic} systems."
                elif stage == "behavioral_hr":
                    topics = ["Technical Disagreements", "Architectural Ownership", "Learning High-Velocity Technologies"]
                    goal = "Examine engineering mindset, ownership, and decision-making during high-stakes technical decisions."
                else:
                    topics = [focus_topic]
                    goal = meta["default_goal"]
            elif interview_type == "role":
                if stage == "intro":
                    topics = [f"{role} Orientation", f"Key Strengths for {role}", "Engineering Philosophy"]
                    goal = f"Evaluate communication, background, and alignment with {level} {role} responsibilities."
                elif stage == "skill_verification":
                    topics = [f"{role} Frameworks & Tooling", "Standard Production Libraries", "API Design"]
                    goal = f"Verify competence across critical tools and standards essential for {role}."
                elif stage == "technical":
                    topics = [f"{role} Deep Architecture", "Database & Concurrency Patterns", "Network Protocols"]
                    goal = f"Examine foundational technical depth, internal mechanics, and best practices for {role}."
                elif stage == "problem_solving":
                    topics = [f"{role} Scalability Scenarios", "Edge Cases & Fault Tolerance", "System Trade-offs"]
                    goal = f"Evaluate systematic problem-solving and architectural tradeoffs for {role} challenges."
                elif stage == "project_discussion":
                    topics = [f"{role} Flagship Project", "System Architecture", "Scalability Blockers"]
                    goal = f"Analyze architectural leadership, delivery impact, and engineering trade-offs in past projects."
                elif stage == "experience_discussion":
                    topics = ["CI/CD Automation", "Code Review Standards", "Production Incident Post-Mortems"]
                    goal = "Probe engineering rigour, deployment safety, and cross-functional team practices."
                elif stage == "behavioral_hr":
                    topics = ["Cross-Team Alignment", "Sprint Prioritization", "Mentorship & Engineering Culture"]
                    goal = "Evaluate collaboration, communication under stress, and ownership mindset."
                else:
                    topics = top_skills
                    goal = meta["default_goal"]
            else:
                # Default: Resume-based
                if stage == "intro":
                    topics = ["Candidate Journey", f"Motivation for {role}", "Key Technical Strengths"]
                    goal = f"Evaluate communication, engineering background, and genuine passion for the {role} position."
                elif stage == "skill_verification":
                    topics = top_skills[:3]
                    goal = f"Verify technical authenticity of claims in {', '.join(top_skills[:3])} listed on the resume."
                elif stage == "technical":
                    topics = [f"{role} Architecture", "Data Structures & Concurrency", "Database Query Optimization"]
                    goal = f"Assess core engineering fundamentals and system concepts required for {level} {role}."
                elif stage == "problem_solving":
                    topics = ["Scalability Trade-offs", "Edge Case Handling", "System Bottleneck Analysis"]
                    goal = "Evaluate step-by-step problem deconstruction, trade-off communication, and edge-case handling."
                elif stage == "project_discussion":
                    topics = [top_project, "Microservice Architecture", "Technical Trade-offs"]
                    goal = f"Conduct architectural deep-dive into '{top_project}', assessing individual contribution and metrics."
                elif stage == "experience_discussion":
                    topics = ["CI/CD Pipelines", "Code Reviews & Mentorship", "Production Bug Diagnostics"]
                    goal = "Investigate production readiness, collaborative coding practices, and deployment troubleshooting."
                elif stage == "behavioral_hr":
                    topics = ["Conflict Resolution", "Prioritization Under Deadlines", "Engineering Ownership"]
                    goal = "Examine situational judgment, professional collaboration, and adaptability in engineering teams."
                else:
                    topics = top_skills
                    goal = meta["default_goal"]

            plans.append(StagePlan(
                stage=stage,
                title=meta["title"],
                focus_goal=goal,
                target_skills_or_topics=topics,
                estimated_questions=2 if stage not in ["intro", "behavioral_hr"] else 1
            ))

        if interview_type == "topic" and focus_topic:
            summary = f"Custom {len(plans)}-stage topic-mastery interview specializing exclusively in {focus_topic} for {role} ({level})."
            fit_notes = f"Targeting end-to-end expertise in {focus_topic}, evaluating theoretical internals, production failure modes, and architectural trade-offs."
        elif interview_type == "role":
            summary = f"Comprehensive {len(plans)}-stage role-focused evaluation for {role} ({level})."
            fit_notes = f"Tailored to benchmark candidates against industry standard expectations for a {level} {role}."
        else:
            summary = f"Custom {len(plans)}-stage adaptive interview for {role} ({level}). Designed to probe {', '.join(top_skills[:4])} and verify evidence from '{top_project}'."
            fit_notes = f"Candidate claims foundational skills in {', '.join(top_skills[:5])}. The interview will challenge depth in systems architecture, concurrency, and real-world engineering trade-offs."

        return InterviewTrajectory(
            session_summary=summary,
            candidate_fit_notes=fit_notes,
            stages=plans
        )


interview_planner_node = InterviewPlannerNode()
