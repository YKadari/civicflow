import pytest

from app.ai.exceptions import AIProviderError
from app.ai.models import (
    GroundedRecommendation,
    IntentClassification,
)
from app.domain.models import (
    ActionType,
    PolicyEvidence,
)
from app.services.analysis import analyze_case_request


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
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
                    "If a scheduled payment has not "
                    "been received within five business "
                    "days, a payment-status investigation "
                    "may be opened."
                ),
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


class GoodAIProvider:
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
                "The case shows that the scheduled "
                "payment is missing and HA-PAY "
                "section 4.2 applies."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.92,
        )


class LowConfidenceProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.40,
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
            rationale="Test recommendation.",
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.90,
        )


class BrokenAIProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        raise AIProviderError(
            "AI unavailable"
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        raise AIProviderError(
            "AI unavailable"
        )


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

    assert (
        analysis.request_type
        == "payment_issue"
    )

    assert (
        analysis.requires_human_review
        is True
    )

    assert analysis.recommended_action is None


def test_missing_policy_requires_review():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=GoodAIProvider(),
        policy_retriever=EmptyPolicyRetriever(),
    )

    assert analysis is not None

    assert (
        analysis.requires_human_review
        is True
    )

    assert analysis.recommended_action is None

    assert analysis.policy_evidence == []


def test_grounded_recommendation():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=GoodAIProvider(),
        policy_retriever=FakePolicyRetriever(),
    )

    assert analysis is not None

    assert (
        analysis.request_type
        == "payment_issue"
    )

    assert (
        analysis.recommended_action
        == ActionType.CHECK_PAYMENT
    )

    assert (
        analysis.requires_human_review
        is False
    )

    assert (
        analysis.cited_policy_chunks
        == ["HA-PAY-V1-4_2"]
    )

    assert (
        analysis.recommendation_confidence
        == 0.92
    )

    assert (
        analysis.recommendation_rationale
        is not None
    )

    assert len(
        analysis.policy_evidence
    ) == 1

    assert (
        analysis.policy_evidence[0].policy_id
        == "HA-PAY"
    )