import json
import re
from typing import List, Dict, Any, Optional
from app.schemas.evaluation import CommunicationEvaluationResult
from app.agents.llm_factory import llm_factory


class CommunicationEvaluationNode:
    """Independent AI Evaluator assessing Communication & Delivery only.
    
    IMPORTANT:
    Evaluates clarity, sentence formation, grammar, vocabulary, and explanation organization.
    Never reduces or increases scores based on technical correctness.
    """

    @classmethod
    def execute(
        cls,
        question_text: str,
        candidate_answer: str,
        stage: str,
    ) -> CommunicationEvaluationResult:
        """Run independent communication evaluation."""
        llm = llm_factory.get_llm(temperature=0.1)

        if llm:
            try:
                result = cls._evaluate_with_llm(llm, question_text, candidate_answer, stage)
                if result:
                    return result
            except Exception as e:
                print(f"[WARN] LLM communication evaluation failed: {e}. Falling back to deterministic rubric.")

        return cls._deterministic_evaluation(question_text, candidate_answer, stage)

    @classmethod
    def _evaluate_with_llm(
        cls,
        llm,
        question_text: str,
        candidate_answer: str,
        stage: str,
    ) -> Optional[CommunicationEvaluationResult]:
        prompt = f"""You are a Lead Executive Communication Coach and Technical Interview Assessor.

STRICT EVALUATION RULE:
NEVER penalize or reward the candidate for the technical or factual correctness of their answer. Your SOLE objective is evaluating delivery, clarity, structure, conciseness, understandability, and professional grammar.

INTERVIEW QUESTION:
{question_text}

CANDIDATE RESPONSE:
\"\"\"{candidate_answer}\"\"\"

SCORING CRITERIA (0 to 100 total):
1. Clarity & Understandability (0 to 30): Is the thought process logically structured and immediately understandable?
2. Conciseness & Directness (0 to 25): Did they answer directly without excessive rambling, tangents, or excessive filler words?
3. Professional Engineering Vocabulary (0 to 25): Did they articulate themselves with professional diction and clear terminology?
4. Grammar & Cohesion (0 to 20): Are sentences well-formed, connected smoothly, and grammatically coherent?

Strictly output a JSON object matching this schema:
{{
  "comm_score": 82.0,
  "clarity_score": 25.0,
  "conciseness_score": 21.0,
  "professional_vocabulary": 20.0,
  "grammar_and_coherence": 16.0,
  "structure_feedback": "Actionable feedback on how the candidate can structure their delivery better (e.g. STAR method, top-down explanation)",
  "comm_strengths": ["Clear delivery strengths"],
  "comm_weaknesses": ["Delivery areas to improve"]
}}
"""
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        clean_json = re.sub(r"^```json\s*", "", content.strip())
        clean_json = re.sub(r"^```\s*", "", clean_json)
        clean_json = re.sub(r"\s*```$", "", clean_json)

        data = json.loads(clean_json)
        return CommunicationEvaluationResult(**data)

    @classmethod
    def _deterministic_evaluation(
        cls,
        question_text: str,
        candidate_answer: str,
        stage: str,
    ) -> CommunicationEvaluationResult:
        """Deterministic communication evaluation rubric."""
        words = len(candidate_answer.split())
        sentences = [s.strip() for s in candidate_answer.split(".") if s.strip()]

        if words < 10:
            clarity = 12.0
            concise = 15.0
            vocab = 10.0
            grammar = 12.0
            feedback = "The answer was extremely short. In technical interviews, provide a structured paragraph starting with a direct thesis, followed by context and an example."
            strengths = ["Directness"]
            weaknesses = ["Under-elaborated delivery", "Lack of narrative structure"]
        elif words > 250:
            clarity = 22.0
            concise = 14.0
            vocab = 22.0
            grammar = 17.0
            feedback = "You provided a detailed response, but it bordered on rambling. Try summarizing the core conclusion upfront before diving into implementation details."
            strengths = ["Rich vocabulary", "Detailed explanations"]
            weaknesses = ["Conciseness", "Top-down executive summary"]
        else:
            clarity = 26.0
            concise = 22.0
            vocab = 21.0
            grammar = 17.0
            feedback = "Clear, articulate delivery. You maintained good structural pacing between the direct answer and the supporting justification."
            strengths = ["Well-paced delivery", "Coherent sentence formation", "Clear logical flow"]
            weaknesses = ["Practice using STAR (Situation-Task-Action-Result) format for narrative questions"]

        total = min(clarity + concise + vocab + grammar, 100.0)

        return CommunicationEvaluationResult(
            comm_score=round(total, 1),
            clarity_score=round(clarity, 1),
            conciseness_score=round(concise, 1),
            professional_vocabulary=round(vocab, 1),
            grammar_and_coherence=round(grammar, 1),
            structure_feedback=feedback,
            comm_strengths=strengths,
            comm_weaknesses=weaknesses,
        )


communication_evaluation_node = CommunicationEvaluationNode()
