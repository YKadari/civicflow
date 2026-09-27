import pytest

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.models import (
    GroundedRecommendation,
    IntentClassification,
)
from app.domain.models import PolicyEvidence


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


class FakeAIProvider:
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
            rationale="Fake unsupported citation.",
            cited_chunk_ids=[
                "FAKE-POLICY-99"
            ],
            confidence=0.99,
        )


class FakePolicyRetriever:
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
                    "may be opened for a missing payment."
                ),
                similarity=0.90,
            )
        ]


def test_graph_generates_grounded_recommendation():
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

    assert (
        result["request_type"]
        == "payment_issue"
    )

    assert (
        result["classification_source"]
        == "ai"
    )

    assert (
        result["requires_human_review"]
        is False
    )

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

    assert (
        "Payment PAY-10001-SEP is marked missing"
        in result["facts"]
    )


def test_graph_rejects_fake_policy_citation():
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