from typing import Literal

from pydantic import BaseModel, Field


class IntentClassification(BaseModel):
    request_type: Literal[
        "payment_issue",
        "document_issue",
        "contact_update",
        "general_inquiry",
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )