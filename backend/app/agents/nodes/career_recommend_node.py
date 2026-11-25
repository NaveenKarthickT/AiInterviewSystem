import json
import re
from typing import List, Dict, Any, Optional
from app.schemas.optimization import JobRoleRecommendation
from app.agents.llm_factory import llm_factory


class CareerRecommendNode:
    """Agent that analyzes demonstrated competencies, interview scores, and
    project evidence to recommend the top 3 best-fit engineering job roles.
    """

    ROLE_BENCHMARKS = [
        {
            "role": "Distributed Systems & Backend Engineer",
            "skills": ["Go", "Python", "SQL", "PostgreSQL", "Redis", "Docker", "REST APIs", "Kafka"],
            "justification": "Demonstrated high understanding of backend request lifecycles, database transactions, concurrency, and caching architectures.",
            "upskill": ["Raft consensus protocols", "Distributed tracing with OpenTelemetry"],
        },
        {
            "role": "Full Stack Software Engineer",
            "skills": ["React", "TypeScript", "FastAPI", "Node.js", "PostgreSQL", "Git", "REST APIs"],
            "justification": "Strong balance between client-side component state management and clean asynchronous backend API development.",
            "upskill": ["Next.js server-side rendering", "End-to-end Playwright testing"],
        },
        {
            "role": "DevOps & Cloud Infrastructure Engineer",
            "skills": ["Docker", "Kubernetes", "Linux", "CI/CD", "AWS", "Terraform", "Bash"],
            "justification": "Demonstrated solid grasp of automated deployment pipelines, containerization boundaries, and cluster health observability.",
            "upskill": ["Kubernetes Custom Resource Definitions (CRDs)", "GitOps with ArgoCD"],
        },
        {
            "role": "AI / Machine Learning Platform Engineer",
            "skills": ["Python", "PyTorch", "Pandas", "NumPy", "Docker", "FastAPI"],
            "justification": "Demonstrated competence in numerical processing, data serialization, and serving ML inference endpoints.",
            "upskill": ["vLLM and TensorRT model serving", "Vector indexing at scale (Milvus/Pinecone)"],
        },
    ]

    @classmethod
    def execute(
        cls,
        verified_skills: List[str],
        radar_metrics: List[Dict[str, Any]],
        overall_knowledge_score: float,
        target_role: str,
    ) -> List[JobRoleRecommendation]:
        """Recommend top 3 matched engineering specializations."""
        llm = llm_factory.get_llm(temperature=0.2)

        if llm:
            try:
                roles = cls._recommend_with_llm(
                    llm, verified_skills, radar_metrics, overall_knowledge_score, target_role
                )
                if roles:
                    return roles
            except Exception as e:
                print(f"[WARN] LLM career recommendation failed: {e}. Using deterministic benchmark matcher.")

        return cls._deterministic_recommend(
            verified_skills, radar_metrics, overall_knowledge_score, target_role
        )

    @classmethod
    def _recommend_with_llm(
        cls, llm, verified_skills: List[str], radar_metrics: List[Dict], overall_knowledge_score: float, target_role: str
    ) -> Optional[List[JobRoleRecommendation]]:
        prompt = f"""You are a Principal Engineering Career Advisor.
Based on the candidate's interview results, recommend the top 3 best-fit engineering job roles.

Target Role Evaluated: {target_role}
Verified Candidate Skills: {verified_skills}
Radar Scores: {radar_metrics}
Overall Technical Score: {overall_knowledge_score}%

Strictly output a JSON list of 3 objects matching:
[
  {{
    "role_title": "Role Name",
    "match_percentage": 88.0,
    "justification": "Why candidate matches based on interview-verified evidence",
    "key_strengths": ["Skill 1", "Skill 2"],
    "recommended_upskill": ["Next topic to master"]
  }}
]
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)
        return [JobRoleRecommendation(**r) for r in data]

    @classmethod
    def _deterministic_recommend(
        cls, verified_skills: List[str], radar_metrics: List[Dict], overall_knowledge_score: float, target_role: str
    ) -> List[JobRoleRecommendation]:
        verified_lower = {s.lower() for s in verified_skills}
        recommendations: List[JobRoleRecommendation] = []

        for b in cls.ROLE_BENCHMARKS:
            role_skills = b["skills"]
            matches = [s for s in role_skills if any(s.lower() in v for v in verified_lower)]
            match_ratio = len(matches) / len(role_skills)

            # Weight by overall knowledge score
            calculated_pct = round(min(match_ratio * 40.0 + (overall_knowledge_score * 0.6), 96.0), 1)

            recommendations.append(JobRoleRecommendation(
                role_title=b["role"],
                match_percentage=max(calculated_pct, 65.0),
                justification=b["justification"],
                key_strengths=matches or role_skills[:3],
                recommended_upskill=b["upskill"],
            ))

        # Sort by match percentage descending and return top 3
        recommendations.sort(key=lambda r: r.match_percentage, reverse=True)
        return recommendations[:3]


career_recommend_node = CareerRecommendNode()
