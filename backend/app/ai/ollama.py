import json
import os

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from app.ai.exceptions import AIProviderError
from app.ai.models import (
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

Return JSON only using this format:

{{
  "request_type": "payment_issue",
  "confidence": 0.95
}}

Citizen request:

{description}
""".strip()

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

            content = response_data["message"]["content"]

            parsed = json.loads(content)

            return IntentClassification.model_validate(
                parsed
            )

        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            KeyError,
            ValidationError,
        ) as exc:

            raise AIProviderError(
                "Ollama failed to return a valid classification."
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
                f"Chunk ID: {item['chunk_id']}\n"
                f"Policy: {item['policy_id']}\n"
                f"Section: {item['section']}\n"
                f"Content: {item['content']}"
            )
            for item in policy_evidence
        )

        prompt = f"""
    You are assisting a public-service caseworker.

    You must recommend an action using ONLY the
    case facts and policy evidence provided below.

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
    3. Cite only chunk IDs shown in POLICY EVIDENCE.
    4. If the evidence is insufficient, choose "none".
    5. You are recommending an action only.
    You are not executing anything.

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
    "rationale": "Short explanation grounded in the supplied evidence.",
    "cited_chunk_ids": ["HA-PAY-V1-4_2"],
    "confidence": 0.90
    }}
    """.strip()

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

            content = response_data["message"]["content"]

            parsed = json.loads(content)

            return GroundedRecommendation.model_validate(
                parsed
            )

        except (
            httpx.HTTPError,
            json.JSONDecodeError,
            KeyError,
            ValidationError,
        ) as exc:
            raise AIProviderError(
                "Ollama failed to return a valid grounded recommendation."
            ) from exc