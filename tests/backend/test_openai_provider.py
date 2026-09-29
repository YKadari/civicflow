from types import SimpleNamespace

from app.ai.models import (
    DecisionChallengeResult,
    GroundedRecommendation,
    IntentClassification,
)
from app.ai.openai_provider import OpenAIProvider


class FakeResponses:
    def parse(
        self,
        *,
        model,
        input,
        text_format,
    ):
        if text_format is IntentClassification:
            result = IntentClassification(
                request_type="payment_issue",
                confidence=0.95,
            )

        elif text_format is GroundedRecommendation:
            result = GroundedRecommendation(
                recommended_action="check_payment",
                rationale=(
                    "The payment policy supports "
                    "checking payment status."
                ),
                cited_chunk_ids=[
                    "HA-PAY-V1-4_2",
                ],
                confidence=0.92,
            )

        elif text_format is DecisionChallengeResult:
            result = DecisionChallengeResult(
                verdict="challenge",
                reasons=[
                    (
                        "Required timing evidence "
                        "is missing."
                    )
                ],
                cited_chunk_ids=[
                    "HA-PAY-V1-4_2",
                ],
                missing_evidence=[
                    (
                        "Verified elapsed "
                        "business days."
                    )
                ],
                confidence=0.94,
            )

        else:
            raise AssertionError(
                "Unexpected response model."
            )

        return SimpleNamespace(
            output_parsed=result,
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_classification():
    provider = OpenAIProvider(
        model="fake-model",
        client=FakeClient(),
    )

    result = provider.classify_intent(
        "My housing payment is missing."
    )

    assert (
        result.request_type
        == "payment_issue"
    )

    assert result.confidence == 0.95


def test_openai_recommendation():
    provider = OpenAIProvider(
        model="fake-model",
        client=FakeClient(),
    )

    result = provider.recommend_action(
        case_id="CF-10001",
        request_description=(
            "My housing payment is missing."
        ),
        facts=[
            "The payment status is missing.",
        ],
        policy_evidence=[
            {
                "chunk_id": "HA-PAY-V1-4_2",
                "policy_id": "HA-PAY",
                "version": 1,
                "section": "4.2",
                "content": (
                    "Payment status may be "
                    "investigated."
                ),
            }
        ],
    )

    assert (
        result.recommended_action
        == "check_payment"
    )

    assert (
        result.cited_chunk_ids
        == ["HA-PAY-V1-4_2"]
    )


def test_openai_decision_challenge():
    provider = OpenAIProvider(
        model="fake-model",
        client=FakeClient(),
    )

    result = provider.challenge_decision(
        case_id="CF-10001",
        proposed_action=(
            "open_investigation"
        ),
        facts=[
            "The payment status is missing.",
        ],
        policy_evidence=[
            {
                "chunk_id": "HA-PAY-V1-4_2",
                "policy_id": "HA-PAY",
                "version": 1,
                "section": "4.2",
                "content": (
                    "An investigation may be "
                    "opened after the required "
                    "waiting period."
                ),
            }
        ],
    )

    assert result.verdict == "challenge"

    assert len(
        result.missing_evidence
    ) == 1