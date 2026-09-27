import json
import os

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from app.ai.exceptions import AIProviderError
from app.ai.models import (
    DecisionChallengeResult,
    GroundedRecommendation,
    IntentClassification,
)


load_dotenv()


class OllamaProvider:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            )
        )

        self.model = (
            model
            or os.getenv(
                "OLLAMA_MODEL",
                "qwen2.5:3b",
            )
        )

    def _request_json(
        self,
        prompt: str,
        error_message: str,
    ) -> dict:

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0,
                    },
                },
                timeout=60.0,
            )

            response.raise_for_status()

            response_data = response.json()

            content = (
                response_data[
                    "message"
                ][
                    "content"
                ]
            )

            return json.loads(
                content
            )

        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            KeyError,
        ) as exc:
            raise AIProviderError(
                error_message
            ) from exc

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        prompt = f"""
You classify citizen requests for a public-service
case-management system.

Choose exactly one request type:

- payment_issue
- document_issue
- contact_update
- general_inquiry

Return JSON only:

{{
  "request_type": "payment_issue",
  "confidence": 0.95
}}

Citizen request:

{description}
""".strip()

        try:
            result = self._request_json(
                prompt=prompt,
                error_message=(
                    "Ollama failed to return a "
                    "valid classification."
                ),
            )

            return (
                IntentClassification
                .model_validate(
                    result
                )
            )

        except ValidationError as exc:
            raise AIProviderError(
                "Ollama returned an invalid classification."
            ) from exc

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        facts_text = "\n".join(
            f"- {fact}"
            for fact in facts
        )

        policy_text = "\n\n".join(
            (
                f"Chunk ID: "
                f"{item['chunk_id']}\n"
                f"Policy: "
                f"{item['policy_id']}\n"
                f"Section: "
                f"{item['section']}\n"
                f"Content: "
                f"{item['content']}"
            )
            for item
            in policy_evidence
        )

        prompt = f"""
You are assisting a public-service caseworker.

Recommend an action using ONLY the supplied
case facts and policy evidence.

Allowed actions:

- check_payment
- open_investigation
- request_document
- update_contact_info
- close_case
- none

Rules:

1. Do not invent policy.
2. Do not invent case facts.
3. Cite only policy chunk IDs supplied below.
4. If evidence is insufficient, choose "none".
5. You are recommending an action only.
6. Pay attention to words such as "may", "should",
   and "must". Do not strengthen policy language.

CASE ID:
{case_id}

CITIZEN REQUEST:
{request_description}

CASE FACTS:
{facts_text}

POLICY EVIDENCE:
{policy_text}

Return JSON only:

{{
  "recommended_action": "check_payment",
  "rationale": "Short grounded explanation.",
  "cited_chunk_ids": ["HA-PAY-V1-4_2"],
  "confidence": 0.90
}}
""".strip()

        try:
            result = self._request_json(
                prompt=prompt,
                error_message=(
                    "Ollama failed to return a "
                    "valid grounded recommendation."
                ),
            )

            return (
                GroundedRecommendation
                .model_validate(
                    result
                )
            )

        except ValidationError as exc:
            raise AIProviderError(
                "Ollama returned an invalid recommendation."
            ) from exc

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:
        """
        Independently challenge a consequential
        recommendation.

        The original recommendation rationale is
        intentionally NOT supplied.
        """

        facts_text = "\n".join(
            f"- {fact}"
            for fact in facts
        )

        policy_text = "\n\n".join(
            (
                f"Chunk ID: "
                f"{item['chunk_id']}\n"
                f"Policy: "
                f"{item['policy_id']}\n"
                f"Section: "
                f"{item['section']}\n"
                f"Content: "
                f"{item['content']}"
            )
            for item
            in policy_evidence
        )

        prompt = f"""
You are an independent skeptical reviewer in a
public-service case-management system.

A separate decision process proposed the action:

{proposed_action}

Your job is NOT to justify the action.

Your job is to actively try to invalidate it.

Use ONLY the case facts and policy evidence supplied
below.

Look specifically for:

- missing facts required by policy
- timing requirements that are not established
- policy contradictions
- eligibility or verification problems
- unsupported assumptions
- differences between "may", "should", and "must"
- evidence that the proposed action is premature
- evidence that human review is necessary

Rules:

1. Do not invent case facts.
2. Do not invent policy.
3. Cite only supplied policy chunk IDs.
4. If a material required fact is missing, verdict
   should be "challenge".
5. "pass" means you could not identify a material
   reason to block or question the action.
6. The fact that another model proposed the action
   is not evidence that it is correct.

CASE ID:
{case_id}

PROPOSED ACTION:
{proposed_action}

CASE FACTS:
{facts_text}

POLICY EVIDENCE:
{policy_text}

Return JSON only:

{{
  "verdict": "challenge",
  "reasons": [
    "A required timing fact is not established."
  ],
  "cited_chunk_ids": [
    "HA-PAY-V1-4_2"
  ],
  "missing_evidence": [
    "Whether five business days have elapsed."
  ],
  "confidence": 0.90
}}
""".strip()

        try:
            result = self._request_json(
                prompt=prompt,
                error_message=(
                    "Ollama failed to perform "
                    "Decision Challenge."
                ),
            )

            return (
                DecisionChallengeResult
                .model_validate(
                    result
                )
            )

        except ValidationError as exc:
            raise AIProviderError(
                "Ollama returned an invalid Decision Challenge."
            ) from exc