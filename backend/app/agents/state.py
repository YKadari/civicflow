from typing import TypedDict

from app.approvals.models import (
    ApprovalRequest,
)
from app.domain.models import (
    CaseContext,
    PolicyEvidence,
)
from app.tools.models import (
    PaymentCheckResult,
)


class CaseAnalysisState(
    TypedDict,
    total=False,
):
    case_id: str
    event_id: str

    context: CaseContext
    description: str

    request_type: str
    classification_confidence: float
    classification_source: str

    facts: list[str]

    policy_evidence: list[
        PolicyEvidence
    ]

    recommended_action: str | None
    recommendation_rationale: (
        str | None
    )
    recommendation_confidence: (
        float | None
    )

    cited_policy_chunks: list[str]

    policy_check_allowed: (
        bool | None
    )

    policy_check_reasons: list[str]

    # -----------------------------------------
    # Decision Challenge
    # -----------------------------------------

    decision_challenge_passed: (
        bool | None
    )

    challenge_verdict: str | None

    challenge_reasons: list[str]

    challenge_confidence: (
        float | None
    )

    challenge_cited_policy_chunks: (
        list[str]
    )

    challenge_missing_evidence: (
        list[str]
    )

    challenged_action: str | None

    # -----------------------------------------
    # Tool / HITL
    # -----------------------------------------

    tool_access_mode: str | None

    tool_requires_approval: (
        bool | None
    )

    approval_request: (
        ApprovalRequest | None
    )

    executed_tool: str | None

    payment_check_result: (
        PaymentCheckResult | None
    )

    requires_human_review: bool

    error: str | None