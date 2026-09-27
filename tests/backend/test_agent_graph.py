import pytest

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.models import IntentClassification
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


def test_graph_retrieves_policy_and_facts():
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