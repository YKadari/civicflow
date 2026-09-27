from typing import TypedDict

from app.domain.models import (
    CaseContext,
    PolicyEvidence,
)


class CaseAnalysisState(TypedDict, total=False):
    case_id: str
    event_id: str

    context: CaseContext
    description: str

    request_type: str
    classification_confidence: float
    classification_source: str

    facts: list[str]

    policy_evidence: list[PolicyEvidence]

    recommended_action: str | None
    recommendation_rationale: str | None
    recommendation_confidence: float | None

    cited_policy_chunks: list[str]

    policy_check_allowed: bool | None
    policy_check_reasons: list[str]

    requires_human_review: bool

    error: str | None