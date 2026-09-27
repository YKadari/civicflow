import pytest

from app.agents.graph import build_case_analysis_graph
from app.ai.models import (
    GroundedRecommendation,
    IntentClassification,
)
from app.domain.models import PolicyEvidence


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


# ============================================================
# Fake AI providers
# ============================================================


class FakeAIProvider:
    """
    Normal high-confidence AI provider.

    Used to test the successful CivicFlow path.
    """

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.95,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        return GroundedRecommendation(
            recommended_action="check_payment",
            rationale=(
                "The payment is missing and the "
                "retrieved payment policy applies."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.92,
        )


class HallucinatingAIProvider:
    """
    Deliberately cites a policy chunk that was
    never retrieved.
    """

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.95,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        return GroundedRecommendation(
            recommended_action="check_payment",
            rationale=(
                "This recommendation uses a fake "
                "policy citation."
            ),
            cited_chunk_ids=[
                "FAKE-POLICY-99"
            ],
            confidence=0.99,
        )


class LowConfidenceAIProvider:
    """
    Low-confidence classification should route
    directly to human review.

    recommend_action() should never be reached.
    """

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.30,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        raise AssertionError(
            "recommend_action should not be called "
            "for a low-confidence case"
        )


class CloseCaseAIProvider:
    """
    AI proposes CLOSE_CASE.

    It is a valid CivicFlow ActionType, but the
    deterministic policy engine does not yet allow
    it to proceed automatically.
    """

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.95,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        return GroundedRecommendation(
            recommended_action="close_case",
            rationale=(
                "Test recommendation to close "
                "the case."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.95,
        )


# ============================================================
# Fake policy retrievers
# ============================================================


class FakePolicyRetriever:
    """
    Returns valid payment policy evidence.
    """

    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        return [
            PolicyEvidence(
                chunk_id="HA-PAY-V1-4_2",
                policy_id="HA-PAY",
                version=1,
                section="4.2 Missing Payments",
                content=(
                    "A payment-status investigation "
                    "may be opened for a missing "
                    "payment."
                ),
                similarity=0.90,
            )
        ]


class EmptyPolicyRetriever:
    """
    Simulates RAG finding no sufficiently
    relevant policy evidence.
    """

    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        return []


# ============================================================
# Tests
# ============================================================


def test_graph_generates_grounded_recommendation():
    """
    Happy path:

    classification
        -> policy retrieval
        -> fact construction
        -> AI recommendation
        -> citation validation
        -> deterministic policy check
        -> tool registry
        -> tool execution
    """

    graph = build_case_analysis_graph(
        ai_provider=FakeAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    assert (
        result["request_type"]
        == "payment_issue"
    )

    assert (
        result["classification_source"]
        == "ai"
    )

    assert (
        result["classification_confidence"]
        == 0.95
    )

    assert (
        result["requires_human_review"]
        is False
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    assert (
        result["recommended_action"]
        == "check_payment"
    )

    assert (
        result["cited_policy_chunks"]
        == ["HA-PAY-V1-4_2"]
    )

    assert (
        result["recommendation_confidence"]
        == 0.92
    )

    assert (
        result["recommendation_rationale"]
        is not None
    )

    # --------------------------------------------------------
    # Policy retrieval + facts
    # --------------------------------------------------------

    assert len(
        result["policy_evidence"]
    ) == 1

    assert (
        result["policy_evidence"][0].policy_id
        == "HA-PAY"
    )

    assert (
        "Payment PAY-10001-SEP is marked missing"
        in result["facts"]
    )

    # --------------------------------------------------------
    # Deterministic policy engine
    # --------------------------------------------------------

    assert (
        result["policy_check_allowed"]
        is True
    )

    assert len(
        result["policy_check_reasons"]
    ) > 0

    # --------------------------------------------------------
    # Tool registry
    # --------------------------------------------------------

    assert (
        result["tool_access_mode"]
        == "read_only"
    )

    assert (
        result["tool_requires_approval"]
        is False
    )

    # --------------------------------------------------------
    # Tool execution
    # --------------------------------------------------------

    assert (
        result["executed_tool"]
        == "check_payment"
    )

    payment_result = result[
        "payment_check_result"
    ]

    assert (
        payment_result.success
        is True
    )

    assert (
        payment_result.case_id
        == "CF-10001"
    )

    assert any(
        payment.status == "missing"
        for payment
        in payment_result.payments
    )


def test_graph_rejects_fake_policy_citation():
    """
    The AI must not cite policy chunks that were
    not actually retrieved.
    """

    graph = build_case_analysis_graph(
        ai_provider=HallucinatingAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert (
        result["recommended_action"]
        is None
    )

    assert (
        result.get("executed_tool")
        is None
    )


def test_low_confidence_routes_to_human_review():
    """
    A low-confidence classification should stop
    automated processing before recommendation.
    """

    graph = build_case_analysis_graph(
        ai_provider=LowConfidenceAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert (
        result["recommended_action"]
        is None
    )

    assert (
        result.get("executed_tool")
        is None
    )


def test_missing_policy_routes_to_human_review():
    """
    CivicFlow should not continue to an automated
    action when no relevant policy is retrieved.
    """

    graph = build_case_analysis_graph(
        ai_provider=FakeAIProvider(),
        policy_retriever=EmptyPolicyRetriever(),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert (
        result["recommended_action"]
        is None
    )

    assert (
        result["policy_evidence"]
        == []
    )

    assert (
        result.get("executed_tool")
        is None
    )


def test_unimplemented_action_is_blocked_by_policy_engine():
    """
    CLOSE_CASE is a valid ActionType, but CivicFlow
    does not yet have a deterministic policy rule
    permitting automated case closure.

    It must therefore be blocked before tool
    execution.
    """

    graph = build_case_analysis_graph(
        ai_provider=CloseCaseAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["policy_check_allowed"]
        is False
    )

    assert (
        result["requires_human_review"]
        is True
    )

    assert (
        result["recommended_action"]
        is None
    )

    assert any(
        "No deterministic policy rule"
        in reason
        for reason in result[
            "policy_check_reasons"
        ]
    )

    # A blocked action must never reach
    # tool execution.
    assert (
        result.get("executed_tool")
        is None
    )