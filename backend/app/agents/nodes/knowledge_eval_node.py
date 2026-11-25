import json
import re
from typing import List, Dict, Any, Optional
from app.schemas.evaluation import KnowledgeEvaluationResult
from app.agents.llm_factory import llm_factory


class KnowledgeEvaluationNode:
    """Independent AI Evaluator assessing Technical Knowledge only.
    
    IMPORTANT:
    Never penalizes technical knowledge scores for grammatical errors,
    accent, limited English vocabulary, or communication difficulties.
    """

    @classmethod
    def execute(
        cls,
        question_text: str,
        expected_concepts: List[str],
        candidate_answer: str,
        stage: str,
        difficulty: str,
        job_role: str,
    ) -> KnowledgeEvaluationResult:
        """Run independent knowledge evaluation."""
        llm = llm_factory.get_llm(temperature=0.1)

        if llm:
            try:
                result = cls._evaluate_with_llm(
                    llm, question_text, expected_concepts, candidate_answer, stage, difficulty, job_role
                )
                if result:
                    return result
            except Exception as e:
                print(f"[WARN] LLM knowledge evaluation failed: {e}. Falling back to deterministic rubric.")

        return cls._deterministic_evaluation(
            question_text, expected_concepts, candidate_answer, stage, difficulty
        )

    @classmethod
    def _evaluate_with_llm(
        cls,
        llm,
        question_text: str,
        expected_concepts: List[str],
        candidate_answer: str,
        stage: str,
        difficulty: str,
        job_role: str,
    ) -> Optional[KnowledgeEvaluationResult]:
        prompt = f"""You are a Senior Principal Systems Engineer conducting a strict technical knowledge assessment.

STRICT EVALUATION RULE:
NEVER reduce technical knowledge scores because of grammatical mistakes, accent, limited English vocabulary, pauses, or colloquial phrasing. A candidate can have high technical knowledge and low communication proficiency. Judge SOLELY based on technical correctness, conceptual depth, trade-off understanding, and problem-solving methodology.

INTERVIEW CONTEXT:
Job Role: {job_role}
Stage: {stage}
Target Difficulty: {difficulty}
Question Asked: {question_text}
Expected Concepts / Rubric: {expected_concepts}

CANDIDATE ANSWER:
\"\"\"{candidate_answer}\"\"\"

SCORING CRITERIA (0 to 100 total):
1. Technical Correctness (0 to 30): Are the technical facts, mechanics, and syntax accurate?
2. Conceptual Depth (0 to 25): Does the candidate understand underlying internals, protocols, or memory models?
3. Practical Application & Trade-offs (0 to 25): Did they articulate engineering trade-offs, real-world constraints, or edge cases?
4. Problem Solving Methodology (0 to 20): Was the technical reasoning sound, systematic, and logical?

Strictly output a JSON object matching this schema:
{{
  "knowledge_score": 85.0,
  "technical_correctness": 26.0,
  "conceptual_depth": 22.0,
  "practical_application": 21.0,
  "problem_solving": 16.0,
  "missing_concepts": ["Concepts omitted or under-explained"],
  "incorrect_concepts": ["Any factual inaccuracies mentioned"],
  "knowledge_feedback": "Constructive technical explanation addressing what was right, what was missing, and the deeper concept",
  "knowledge_strengths": ["Demonstrated technical competencies"],
  "knowledge_weaknesses": ["Specific technical areas to review"]
}}
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)
        return KnowledgeEvaluationResult(**data)

    @classmethod
    def _deterministic_evaluation(
        cls,
        question_text: str,
        expected_concepts: List[str],
        candidate_answer: str,
        stage: str,
        difficulty: str,
    ) -> KnowledgeEvaluationResult:
        """Deterministic technical evaluation rubric."""
        answer_lower = candidate_answer.lower()
        words = len(candidate_answer.split())

        # Check concept matches
        matched_concepts = []
        missing_concepts = []
        for concept in (expected_concepts or []):
            keywords = [w.lower() for w in concept.split() if len(w) > 3]
            if any(k in answer_lower for k in keywords):
                matched_concepts.append(concept)
            else:
                missing_concepts.append(concept)

        ratio = len(matched_concepts) / max(len(expected_concepts or [1]), 1)

        # Baseline scores grounded in answer substance
        if words < 10:
            tc = 8.0
            cd = 5.0
            pa = 5.0
            ps = 4.0
            feedback = "The answer was very brief. To demonstrate depth in technical rounds, provide detailed mechanics, architecture choices, and trade-offs."
        elif ratio >= 0.7:
            tc = 27.0
            cd = 22.0
            pa = 21.0
            ps = 18.0
            feedback = "Strong technical answer. You accurately identified the key mechanics and trade-offs expected for this architecture."
        elif ratio >= 0.4:
            tc = 22.0
            cd = 17.0
            pa = 16.0
            ps = 14.0
            feedback = "Solid foundational answer. You captured the main concept but could go deeper into failure modes and system trade-offs."
        else:
            tc = 16.0
            cd = 12.0
            pa = 11.0
            ps = 11.0
            feedback = "Good attempt, but key architectural principles were omitted. Consider reviewing the underlying mechanics and trade-offs."

        total = min(tc + cd + pa + ps, 100.0)

        strengths = [f"Addressed {c}" for c in matched_concepts] or ["Attempted answer structure"]
        weaknesses = [f"Review {c}" for c in missing_concepts[:3]] or ["Explore edge case behavior"]

        return KnowledgeEvaluationResult(
            knowledge_score=round(total, 1),
            technical_correctness=round(tc, 1),
            conceptual_depth=round(cd, 1),
            practical_application=round(pa, 1),
            problem_solving=round(ps, 1),
            missing_concepts=missing_concepts,
            incorrect_concepts=[],
            knowledge_feedback=feedback,
            knowledge_strengths=strengths,
            knowledge_weaknesses=weaknesses,
        )


knowledge_evaluation_node = KnowledgeEvaluationNode()
