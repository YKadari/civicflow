import pytest

from app.database.repository import (
    get_case_context,
)
from app.domain.models import (
    ActionType,
    PolicyEvidence,
)
from app.policy_engine.engine import (
    evaluate_action,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def payment_policy_evidence():
    return [
        PolicyEvidence(
            chunk_id="HA-PAY-V1-4_2",
            policy_id="HA-PAY",
            version=1,
            section="4.2 Missing Payments",
            content=(
                "A payment-status investigation "
                "may be opened when a scheduled "
                "payment is missing."
            ),
            similarity=0.90,
        )
    ]


def test_check_payment_is_allowed():
    context = get_case_context(
        "CF-10001"
    )

    assert context is not None

    result = evaluate_action(
        action=ActionType.CHECK_PAYMENT,
        context=context,
        policy_evidence=(
            payment_policy_evidence()
        ),
    )

    assert result.allowed is True

    assert (
        result.requires_human_review
        is False
    )


def test_check_payment_without_policy_is_blocked():
    context = get_case_context(
        "CF-10001"
    )

    assert context is not None

    result = evaluate_action(
        action=ActionType.CHECK_PAYMENT,
        context=context,
        policy_evidence=[],
    )

    assert result.allowed is False

    assert (
        result.requires_human_review
        is True
    )

    assert (
        "No relevant HA-PAY policy evidence "
        "was retrieved."
        in result.reasons
    )


def test_unimplemented_action_requires_review():
    context = get_case_context(
        "CF-10001"
    )

    assert context is not None

    result = evaluate_action(
        action=ActionType.CLOSE_CASE,
        context=context,
        policy_evidence=(
            payment_policy_evidence()
        ),
    )

    assert result.allowed is False

    assert (
        result.requires_human_review
        is True
    )