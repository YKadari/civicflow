import json
import os

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from app.ai.exceptions import AIProviderError
from app.ai.models import IntentClassification


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