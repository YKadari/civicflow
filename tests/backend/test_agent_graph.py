import pytest

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.models import IntentClassification


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


def test_graph_classifies_request():
    graph = build_case_analysis_graph(
        ai_provider=FakeAIProvider(),
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