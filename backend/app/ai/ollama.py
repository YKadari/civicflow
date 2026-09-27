import json
import os
from typing import Literal

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)


class IntentClassification(BaseModel):
    request_type: Literal[
        "payment_issue",
        "document_issue",
        "contact_update",
        "general_inquiry",
    ]

    confidence: float


def classify_intent(
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

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
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

    return IntentClassification.model_validate(parsed)