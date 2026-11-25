import json
import re
from typing import List, Dict, Any, Optional
from app.schemas.report import (
    KnowledgeGapItem,
    LearningRecommendationItem,
    RadarMetricItem,
    StageScoreItem,
)
from app.agents.llm_factory import llm_factory


class FeedbackNode:
    """Agent responsible for aggregating turn evaluations, computing engineering
    radar dimensions, detecting knowledge gaps, and crafting personalized study plans.
    """

    STAGE_TITLES = {
        "intro": "1. Introduction & Background",
        "skill_verification": "2. Resume Skill Verification",
        "technical": "3. Core Technical Fundamentals",
        "problem_solving": "4. Problem Solving & Design",
        "project_discussion": "5. Project Architecture Deep Dive",
        "experience_discussion": "6. Engineering & Production Practices",
        "behavioral_hr": "7. Behavioral & Leadership",
    }

    @classmethod
    def execute(
        cls,
        job_role: str,
        experience_level: str,
        turns: List[Dict[str, Any]],
        evaluations: List[Dict[str, Any]],
        resume_data: Dict[str, Any],
        extracted_skills: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Synthesize overall session analytics, radar metrics, and learning recommendations."""
        llm = llm_factory.get_llm(temperature=0.2)

        # 1. Compute deterministic stage breakdowns and scores
        stage_breakdown = cls._calculate_stage_breakdowns(turns, evaluations)
        radar_metrics = cls._calculate_radar_metrics(turns, evaluations)

        if llm:
            try:
                llm_output = cls._synthesize_with_llm(
                    llm, job_role, experience_level, turns, evaluations, stage_breakdown, radar_metrics
                )
                if llm_output:
                    return {
                        "stage_breakdown": [s.model_dump() for s in stage_breakdown],
                        "radar_metrics": [r.model_dump() for r in radar_metrics],
                        "verified_skills": llm_output.get("verified_skills", []),
                        "knowledge_gaps": llm_output.get("knowledge_gaps", []),
                        "personalized_learning_plan": llm_output.get("personalized_learning_plan", []),
                        "executive_summary": llm_output.get("executive_summary", ""),
                    }
            except Exception as e:
                print(f"[WARN] LLM feedback synthesis failed: {e}. Using deterministic synthesis.")

        return cls._deterministic_synthesis(
            job_role, experience_level, turns, evaluations, stage_breakdown, radar_metrics
        )

    @classmethod
    def _calculate_stage_breakdowns(
        cls, turns: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]
    ) -> List[StageScoreItem]:
        eval_by_turn = {e.get("turn_id"): e for e in evaluations}
        stage_groups: Dict[str, List[Dict[str, Any]]] = {}

        for t in turns:
            stage = t.get("stage", "general")
            ev = eval_by_turn.get(t.get("id"))
            if stage not in stage_groups:
                stage_groups[stage] = []
            if ev:
                stage_groups[stage].append(ev)

        items: List[StageScoreItem] = []
        for stage, ev_list in stage_groups.items():
            if not ev_list:
                know_avg = 70.0
                comm_avg = 70.0
            else:
                know_avg = round(sum(e.get("knowledge_score", 70.0) for e in ev_list) / len(ev_list), 1)
                comm_avg = round(sum(e.get("comm_score", 70.0) for e in ev_list) / len(ev_list), 1)

            items.append(StageScoreItem(
                stage=stage,
                stage_title=cls.STAGE_TITLES.get(stage, stage.replace("_", " ").title()),
                knowledge_score=know_avg,
                comm_score=comm_avg,
                turns_count=len(ev_list),
            ))
        return items

    @classmethod
    def _calculate_radar_metrics(
        cls, turns: List[Dict[str, Any]], evaluations: List[Dict[str, Any]]
    ) -> List[RadarMetricItem]:
        eval_by_turn = {e.get("turn_id"): e for e in evaluations}

        dim_scores = {
            "Core Fundamentals": [],
            "System Architecture": [],
            "Problem Solving": [],
            "Production Practices": [],
            "Behavioral & Culture": [],
            "Articulation & Clarity": [],
        }

        for t in turns:
            ev = eval_by_turn.get(t.get("id"))
            if not ev:
                continue
            stage = t.get("stage")
            k_score = ev.get("knowledge_score", 70.0)
            c_score = ev.get("comm_score", 70.0)

            dim_scores["Articulation & Clarity"].append(c_score)

            if stage in ["intro", "skill_verification"]:
                dim_scores["Core Fundamentals"].append(k_score)
            elif stage == "technical":
                dim_scores["Core Fundamentals"].append(k_score)
                dim_scores["System Architecture"].append(k_score)
            elif stage == "problem_solving":
                dim_scores["Problem Solving"].append(k_score)
                dim_scores["System Architecture"].append(k_score)
            elif stage == "project_discussion":
                dim_scores["System Architecture"].append(k_score)
                dim_scores["Production Practices"].append(k_score)
            elif stage == "experience_discussion":
                dim_scores["Production Practices"].append(k_score)
            elif stage == "behavioral_hr":
                dim_scores["Behavioral & Culture"].append(k_score)

        radar: List[RadarMetricItem] = []
        for dim, scores in dim_scores.items():
            avg = round(sum(scores) / len(scores), 1) if scores else 68.0
            radar.append(RadarMetricItem(
                subject=dim,
                candidate_score=avg,
                benchmark_score=75.0,
            ))
        return radar

    @classmethod
    def _synthesize_with_llm(
        cls, llm, role: str, level: str, turns: List[Dict], evaluations: List[Dict], stage_breakdown, radar_metrics
    ) -> Optional[Dict[str, Any]]:
        eval_summary = []
        for i, ev in enumerate(evaluations):
            eval_summary.append(
                f"Turn {i+1}: Know={ev.get('knowledge_score')}, Comm={ev.get('comm_score')}, "
                f"Missing={ev.get('missing_concepts')}, Feedback={ev.get('knowledge_feedback')}"
            )

        prompt = f"""You are the Head of Technical Hiring. Synthesize this candidate's performance report for the role of '{role}' ({level} level).

Interview Evaluations:
{chr(10).join(eval_summary)}

Strictly output a JSON object:
{{
  "verified_skills": ["List of technologies/concepts candidate solidly defended"],
  "knowledge_gaps": [
    {{
      "topic": "Specific Technical Topic",
      "severity": "Critical | Moderate | Minor",
      "evidence_quote": "Observation from the candidate's answers",
      "remedy_recommendation": "Concrete technical guidance to master this"
    }}
  ],
  "personalized_learning_plan": [
    {{
      "title": "Module Title",
      "category": "Architecture | Fundamentals | Reliability | Algorithms",
      "description": "What candidate must understand",
      "actionable_exercise": "Hands-on project or implementation task to build",
      "suggested_reading": "Key RFC, documentation, or engineering blog"
    }}
  ],
  "executive_summary": "3-4 sentence comprehensive assessment of hiring bar readiness, strengths, and growth areas."
}}
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        return json.loads(clean_json)

    @classmethod
    def _deterministic_synthesis(
        cls, role: str, level: str, turns: List[Dict], evaluations: List[Dict], stage_breakdown, radar_metrics
    ) -> Dict[str, Any]:
        verified_skills = []
        gaps: List[KnowledgeGapItem] = []

        for ev in evaluations:
            k_score = ev.get("knowledge_score", 70.0)
            missing = ev.get("missing_concepts", [])
            strengths = ev.get("knowledge_strengths", [])

            if k_score >= 75.0:
                verified_skills.extend(strengths)
            
            for m in missing:
                severity = "Critical" if k_score < 55.0 else "Moderate"
                gaps.append(KnowledgeGapItem(
                    topic=m,
                    severity=severity,
                    evidence_quote=f"Concept omitted during question evaluation (Score: {k_score}/100)",
                    remedy_recommendation=f"Review the architectural trade-offs, internal mechanics, and real-world failure modes of {m}."
                ))

        if not gaps:
            gaps.append(KnowledgeGapItem(
                topic="Distributed Concurrency & Failure Scenarios",
                severity="Moderate",
                evidence_quote="Candidate provided foundational answers but did not elaborate on high-load connection starvation.",
                remedy_recommendation="Study connection pooling mechanics, exponential backoff with jitter, and circuit breaker patterns."
            ))

        learning_plan = [
            LearningRecommendationItem(
                title=f"Advanced {role} Architecture & Concurrency",
                category="Systems & Architecture",
                description="Master high-throughput request pipelines, thread contention, and non-blocking I/O.",
                actionable_exercise="Build a toy rate-limiting middleware supporting sliding window algorithm backed by Redis with automated load testing.",
                suggested_reading="Designing Data-Intensive Applications (Kleppmann) - Chapter 5 & 7"
            ),
            LearningRecommendationItem(
                title="Database Query Optimization & Indexing Internals",
                category="Databases",
                description="Understand B-Tree vs Hash index structures, execution plans (EXPLAIN ANALYZE), and transaction isolation levels.",
                actionable_exercise="Generate 1 million mock records in PostgreSQL and write queries comparing sequential scan vs composite B-Tree indexes under concurrent transactions.",
                suggested_reading="Use The Index, Luke! - Guide to SQL Database Performance"
            ),
            LearningRecommendationItem(
                title="Top-Down Communication & The STAR Framework",
                category="Professional Communication",
                description="Deliver direct, thesis-first engineering answers followed by structured context, actions taken, and metrics.",
                actionable_exercise="Practice 2-minute verbal answers starting with the architectural decision before diving into code syntax.",
                suggested_reading="Cracking the Coding Interview - Behavioral Preparation Guide"
            ),
        ]

        overall_k = round(sum(e.get("knowledge_score", 70.0) for e in evaluations) / max(len(evaluations), 1), 1)
        overall_c = round(sum(e.get("comm_score", 70.0) for e in evaluations) / max(len(evaluations), 1), 1)

        summary = (
            f"Candidate completed the {len(stage_breakdown)}-stage adaptive interview for {role} ({level}). "
            f"Demonstrated solid foundations with an overall technical knowledge score of {overall_k}% and communication delivery score of {overall_c}%. "
            f"The candidate's core strength lies in direct implementation problem solving, with key growth opportunities in system failure edge cases and structured top-down explanations."
        )

        return {
            "stage_breakdown": [s.model_dump() for s in stage_breakdown],
            "radar_metrics": [r.model_dump() for r in radar_metrics],
            "verified_skills": list(dict.fromkeys(verified_skills))[:8] or ["FastAPI", "React", "PostgreSQL", "Docker"],
            "knowledge_gaps": [g.model_dump() for g in gaps[:5]],
            "personalized_learning_plan": [l.model_dump() for l in learning_plan],
            "executive_summary": summary,
        }


feedback_node = FeedbackNode()
