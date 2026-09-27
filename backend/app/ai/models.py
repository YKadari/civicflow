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


class GroundedRecommendation(BaseModel):
    recommended_action: Literal[
        "check_payment",
        "open_investigation",
        "request_document",
        "update_contact_info",
        "close_case",
        "none",
    ]

    rationale: str

    cited_chunk_ids: list[str]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


class DecisionChallengeResult(BaseModel):
    verdict: Literal[
        "pass",
        "challenge",
    ]

    reasons: list[str] = Field(
        default_factory=list
    )

    cited_chunk_ids: list[str] = Field(
        default_factory=list
    )

    missing_evidence: list[str] = Field(
        default_factory=list
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )