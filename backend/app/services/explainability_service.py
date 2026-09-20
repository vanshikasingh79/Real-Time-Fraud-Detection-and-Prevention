"""Asynchronous AI explanation generation with responsible fallback behavior."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.core.config import Settings, settings as default_settings
from app.core.guardrails import AIGuardrailService
from app.models.schemas import AIExplanation, LoanApplicationRequest


class ExplainabilityEngine:
    """Generate grounded fraud explanations through a configured LLM provider."""

    def __init__(
        self,
        settings: Settings = default_settings,
        guardrail_service: AIGuardrailService | None = None,
    ) -> None:
        """Initialize the engine with configuration and guardrail dependencies."""
        self.settings = settings
        self.guardrail_service = guardrail_service or AIGuardrailService()

    async def generate_explanation(
        self,
        application: LoanApplicationRequest,
        risk_score: float,
        risk_level: str,
        risk_factors: list[str],
        similar_cases: list[dict] | None = None,
    ) -> AIExplanation:
        """Generate a grounded explanation, falling back to deterministic output.

        External provider failures, invalid responses, and guardrail failures are
        contained here so callers always receive a valid ``AIExplanation``.
        """
        try:
            sanitized_context = self.guardrail_service.sanitize_payload(application)
        except Exception:
            sanitized_context = {}

        prompt = self._build_prompt(
            sanitized_context,
            risk_score,
            risk_level,
            risk_factors,
            similar_cases,
        )

        try:
            grounding_factors = list(risk_factors)
            historical_point = self._historical_context(similar_cases)
            if historical_point:
                grounding_factors.append(historical_point)
            provider = self.settings.LLM_PROVIDER.lower()
            if provider == "openai":
                response_data = await self._generate_openai(prompt)
            elif provider == "bedrock":
                response_data = await self._generate_bedrock(prompt)
            else:
                return self._grounded_mock(
                    risk_score, risk_level, risk_factors, similar_cases
                )

            explanation = AIExplanation.model_validate(response_data)
            return self._with_grounding(explanation, grounding_factors)
        except Exception:
            return self._grounded_mock(risk_score, risk_level, risk_factors, similar_cases)

    def _build_prompt(
        self,
        sanitized_context: dict[str, Any],
        risk_score: float,
        risk_level: str,
        risk_factors: list[str],
        similar_cases: list[dict] | None,
    ) -> str:
        """Build the strict JSON-only prompt sent to an external provider."""
        schema = {
            "plain_english_summary": "string",
            "risk_justification_points": ["string"],
            "recommended_next_steps": ["string"],
            "confidence_score": "number between 0.0 and 1.0",
        }
        assessment_context = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "application": sanitized_context,
            "historical_context": self._historical_context(similar_cases),
        }
        return (
            "You are a fraud risk explainability assistant for compliance officers. "
            "Use only the supplied assessment data. Do not infer credit history, "
            "identity facts, or other unobserved signals. Output ONLY valid JSON, "
            "with no markdown or extra text, matching this structure: "
            f"{json.dumps(schema)}. "
            f"Assessment context: {json.dumps(assessment_context)}"
        )

    async def _generate_openai(self, prompt: str) -> dict[str, Any]:
        """Request a JSON explanation from OpenAI."""
        from openai import AsyncOpenAI

        if not self.settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        client = AsyncOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            timeout=10.0,
        )
        response = await client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=self.settings.MAX_EXPLANATION_TOKENS,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty explanation.")
        return json.loads(content)

    async def _generate_bedrock(self, prompt: str) -> dict[str, Any]:
        """Request a JSON explanation from AWS Bedrock without blocking asyncio."""
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.settings.AWS_REGION)
        response = await asyncio.to_thread(
            client.converse,
            modelId=self.settings.AWS_BEDROCK_MODEL_ID,
            system=[{"text": prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": "Return the required JSON explanation."}],
                }
            ],
            inferenceConfig={"maxTokens": self.settings.MAX_EXPLANATION_TOKENS},
        )
        content = response["output"]["message"]["content"][0]["text"]
        return json.loads(content)

    def _verify_grounding(
        self,
        explanation: AIExplanation,
        risk_factors: list[str],
    ) -> bool:
        """Run grounding verification while failing closed on guardrail errors."""
        try:
            return self.guardrail_service.verify_grounding(
                explanation.risk_justification_points,
                risk_factors,
            )
        except Exception:
            return False

    def _with_grounding(
        self,
        explanation: AIExplanation,
        risk_factors: list[str],
    ) -> AIExplanation:
        """Return an explanation with its grounding flag computed by guardrails."""
        grounded = self._verify_grounding(explanation, risk_factors)
        return explanation.model_copy(update={"is_grounded": grounded})

    def _grounded_mock(
        self,
        risk_score: float,
        risk_level: str,
        risk_factors: list[str],
        similar_cases: list[dict] | None = None,
    ) -> AIExplanation:
        """Create and ground a deterministic fallback explanation."""
        return self._with_grounding(
            self._mock_explanation(
                risk_score,
                risk_level,
                risk_factors,
                similar_cases,
            ),
            self._grounding_factors(risk_factors, similar_cases),
        )

    @staticmethod
    def _historical_context(similar_cases: list[dict] | None) -> str | None:
        """Build the historical pattern point for prompts and explanations."""
        if not similar_cases:
            return None
        max_similarity = max(case["similarity_score"] for case in similar_cases)
        case_ids = ", ".join(str(case["application_id"]) for case in similar_cases)
        return (
            f"Pattern Match: This application shares an {max_similarity:.0%} feature "
            f"similarity with past flagged case(s): {case_ids}."
        )

    @classmethod
    def _grounding_factors(
        cls,
        risk_factors: list[str],
        similar_cases: list[dict] | None,
    ) -> list[str]:
        """Add historical context to the factors used by grounding checks."""
        historical_point = cls._historical_context(similar_cases)
        return risk_factors + ([historical_point] if historical_point else [])

    @staticmethod
    def _mock_explanation(
        risk_score: float,
        risk_level: str,
        risk_factors: list[str],
        similar_cases: list[dict] | None = None,
    ) -> AIExplanation:
        """Create a deterministic explanation without external network calls."""
        factors = list(risk_factors) or ["No specific anomaly was identified"]
        historical_point = ExplainabilityEngine._historical_context(similar_cases)
        if historical_point:
            factors.append(historical_point)
        next_steps = (
            ["Approve the application under standard controls"]
            if risk_level.upper() == "LOW"
            else ["Review the listed risk factors", "Verify applicant identity before approval"]
        )
        return AIExplanation(
            plain_english_summary=(
                f"The application received a {risk_level.upper()} fraud risk assessment "
                f"with a score of {risk_score:.2f}."
            ),
            risk_justification_points=factors,
            recommended_next_steps=next_steps,
            confidence_score=1.0,
            is_grounded=False,
        )
