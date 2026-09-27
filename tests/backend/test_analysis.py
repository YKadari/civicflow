import pytest

from app.ai.exceptions import AIProviderError
from app.ai.models import IntentClassification
from app.domain.models import PolicyEvidence
from app.services.analysis import analyze_case_request


pytestmark = pytest.mark.usefixtures("seeded_database")


class LowConfidenceProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.40,
        )


class BrokenAIProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        raise AIProviderError(
            "AI unavailable"
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
                content="Synthetic payment policy.",
                similarity=0.90,
            )
        ]


class EmptyPolicyRetriever:
    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        return []


def test_ai_failure_uses_fallback():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=BrokenAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    assert analysis is not None

    assert (
        analysis.classification_source
        == "fallback"
    )

    assert analysis.requires_human_review is True

    assert analysis.recommended_action is None


def test_low_confidence_requires_review():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=LowConfidenceProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    assert analysis is not None

    assert analysis.request_type == "payment_issue"

    assert analysis.requires_human_review is True

    assert analysis.recommended_action is None


def test_missing_policy_requires_review():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=LowConfidenceProvider(),
        policy_retriever=EmptyPolicyRetriever(),
    )

    assert analysis is not None

    assert analysis.requires_human_review is True

    assert analysis.recommended_action is None