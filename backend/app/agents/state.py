from typing import TypedDict

from app.domain.models import (
    CaseContext,
    PolicyEvidence,
)
from app.tools.models import PaymentCheckResult


class CaseAnalysisState(TypedDict, total=False):
    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    case_id: str
    event_id: str

    # ---------------------------------------------------------
    # Loaded case data
    # ---------------------------------------------------------

    context: CaseContext
    description: str

    # ---------------------------------------------------------
    # Intent classification
    # ---------------------------------------------------------

    request_type: str
    classification_confidence: float
    classification_source: str

    # ---------------------------------------------------------
    # Case facts
    # ---------------------------------------------------------

    facts: list[str]

    # ---------------------------------------------------------
    # Policy RAG
    # ---------------------------------------------------------

    policy_evidence: list[PolicyEvidence]

    # ---------------------------------------------------------
    # AI recommendation
    # ---------------------------------------------------------

    recommended_action: str | None
    recommendation_rationale: str | None
    recommendation_confidence: float | None

    cited_policy_chunks: list[str]

    # ---------------------------------------------------------
    # Deterministic policy engine
    # ---------------------------------------------------------

    policy_check_allowed: bool | None
    policy_check_reasons: list[str]

    # ---------------------------------------------------------
    # Tool registry
    # ---------------------------------------------------------

    tool_access_mode: str | None
    tool_requires_approval: bool | None

    # ---------------------------------------------------------
    # Tool execution
    # ---------------------------------------------------------

    executed_tool: str | None
    payment_check_result: PaymentCheckResult | None

    # ---------------------------------------------------------
    # Routing / safety
    # ---------------------------------------------------------

    requires_human_review: bool

    # THIS FIELD IS CRITICAL.
    #
    # LangGraph state must explicitly know about "error"
    # so that:
    #
    # {"error": "Request not found"}
    #
    # survives after load_context_node returns it.
    error: str | None