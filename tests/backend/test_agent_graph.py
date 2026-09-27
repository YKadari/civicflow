import pytest

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.models import (
    DecisionChallengeResult,
    GroundedRecommendation,
    IntentClassification,
)
from app.domain.models import (
    PolicyEvidence,
)


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
            recommended_action=(
                "check_payment"
            ),
            rationale=(
                "The payment is missing."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.92,
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        raise AssertionError(
            "Read-only actions should not "
            "run Decision Challenge."
        )


class OpenInvestigationAIProvider:
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
            recommended_action=(
                "open_investigation"
            ),
            rationale=(
                "The missing payment may "
                "require investigation."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.95,
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        return DecisionChallengeResult(
            verdict="pass",
            reasons=[
                (
                    "No material conflict "
                    "was identified."
                )
            ],
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            missing_evidence=[],
            confidence=0.90,
        )


class ChallengingAIProvider(
    OpenInvestigationAIProvider
):
    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        return DecisionChallengeResult(
            verdict="challenge",
            reasons=[
                (
                    "The policy requires a "
                    "timing condition that has "
                    "not been established."
                )
            ],
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            missing_evidence=[
                (
                    "Confirmation that five "
                    "business days have elapsed."
                )
            ],
            confidence=0.96,
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
            recommended_action=(
                "check_payment"
            ),
            rationale="Fake citation.",
            cited_chunk_ids=[
                "FAKE-POLICY-99"
            ],
            confidence=0.99,
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        raise AssertionError(
            "Challenge should not run."
        )


class LowConfidenceAIProvider:
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
            "Recommendation should not run."
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        raise AssertionError(
            "Challenge should not run."
        )


class CloseCaseAIProvider:
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
            rationale="Test closure.",
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.95,
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> DecisionChallengeResult:

        raise AssertionError(
            "Policy engine should block "
            "before challenge."
        )


class FakePolicyRetriever:
    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        return [
            PolicyEvidence(
                chunk_id=(
                    "HA-PAY-V1-4_2"
                ),
                policy_id="HA-PAY",
                version=1,
                section=(
                    "4.2 Missing Payments"
                ),
                content=(
                    "If a scheduled payment "
                    "has not been received "
                    "within five business days, "
                    "a payment-status "
                    "investigation may be opened."
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


def test_graph_generates_grounded_recommendation():
    graph = build_case_analysis_graph(
        ai_provider=FakeAIProvider(),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["recommended_action"]
        == "check_payment"
    )

    assert (
        result["policy_check_allowed"]
        is True
    )

    # Read-only tool bypasses challenge.
    assert (
        result.get(
            "decision_challenge_passed"
        )
        is None
    )

    assert (
        result["executed_tool"]
        == "check_payment"
    )

    assert (
        result["requires_human_review"]
        is False
    )


def test_state_changing_action_passes_challenge_and_creates_approval():
    graph = build_case_analysis_graph(
        ai_provider=(
            OpenInvestigationAIProvider()
        ),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result["policy_check_allowed"]
        is True
    )

    assert (
        result[
            "decision_challenge_passed"
        ]
        is True
    )

    assert (
        result["challenge_verdict"]
        == "pass"
    )

    approval = result[
        "approval_request"
    ]

    assert approval is not None

    assert (
        approval.action_type
        == "open_investigation"
    )

    assert (
        approval.status
        == "pending"
    )

    assert (
        result.get("executed_tool")
        is None
    )


def test_decision_challenge_blocks_action():
    graph = build_case_analysis_graph(
        ai_provider=(
            ChallengingAIProvider()
        ),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result[
            "decision_challenge_passed"
        ]
        is False
    )

    assert (
        result["challenge_verdict"]
        == "challenge"
    )

    assert (
        result["challenged_action"]
        == "open_investigation"
    )

    assert len(
        result[
            "challenge_missing_evidence"
        ]
    ) > 0

    assert (
        result["requires_human_review"]
        is True
    )

    # Challenge happens BEFORE approval.
    assert (
        result.get(
            "approval_request"
        )
        is None
    )

    assert (
        result.get("executed_tool")
        is None
    )


def test_graph_rejects_fake_policy_citation():
    graph = build_case_analysis_graph(
        ai_provider=(
            HallucinatingAIProvider()
        ),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result[
            "requires_human_review"
        ]
        is True
    )

    assert (
        result["recommended_action"]
        is None
    )


def test_low_confidence_routes_to_human_review():
    graph = build_case_analysis_graph(
        ai_provider=(
            LowConfidenceAIProvider()
        ),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result[
            "requires_human_review"
        ]
        is True
    )


def test_missing_policy_routes_to_human_review():
    graph = build_case_analysis_graph(
        ai_provider=FakeAIProvider(),
        policy_retriever=(
            EmptyPolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result[
            "requires_human_review"
        ]
        is True
    )


def test_unimplemented_action_is_blocked_before_challenge():
    graph = build_case_analysis_graph(
        ai_provider=(
            CloseCaseAIProvider()
        ),
        policy_retriever=(
            FakePolicyRetriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    assert (
        result[
            "policy_check_allowed"
        ]
        is False
    )

    assert (
        result[
            "requires_human_review"
        ]
        is True
    )

    assert (
        result.get(
            "decision_challenge_passed"
        )
        is None
    )