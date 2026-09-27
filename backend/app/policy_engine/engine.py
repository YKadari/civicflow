from app.domain.models import (
    ActionType,
    CaseContext,
    CaseStatus,
    PolicyEvidence,
)
from app.policy_engine.models import (
    PolicyCheckResult,
)


def evaluate_action(
    action: ActionType,
    context: CaseContext,
    policy_evidence: list[PolicyEvidence],
) -> PolicyCheckResult:
    """
    Deterministically determine whether CivicFlow
    is allowed to proceed with a proposed action.

    The AI does not make this decision.
    """

    if action == ActionType.CHECK_PAYMENT:
        return _evaluate_check_payment(
            context=context,
            policy_evidence=policy_evidence,
        )

    # Conservative default:
    #
    # Until we explicitly implement deterministic
    # rules for an action, CivicFlow will not
    # automatically permit it.
    return PolicyCheckResult(
        allowed=False,
        requires_human_review=True,
        reasons=[
            (
                "No deterministic policy rule is "
                f"implemented for {action.value}."
            )
        ],
    )


def _evaluate_check_payment(
    context: CaseContext,
    policy_evidence: list[PolicyEvidence],
) -> PolicyCheckResult:

    reasons: list[str] = []

    case_is_active = (
        context.case.status
        == CaseStatus.ACTIVE
    )

    relevant_payments = [
        payment
        for payment in context.payments
        if payment.status.lower()
        in {
            "missing",
            "held",
        }
    ]

    has_payment_policy = any(
        evidence.policy_id == "HA-PAY"
        for evidence in policy_evidence
    )

    if not case_is_active:
        reasons.append(
            "The case is not active."
        )

    if not relevant_payments:
        reasons.append(
            (
                "The case has no missing or held "
                "payment requiring a payment check."
            )
        )

    if not has_payment_policy:
        reasons.append(
            (
                "No relevant HA-PAY policy evidence "
                "was retrieved."
            )
        )

    if reasons:
        return PolicyCheckResult(
            allowed=False,
            requires_human_review=True,
            reasons=reasons,
        )

    return PolicyCheckResult(
        allowed=True,
        requires_human_review=False,
        reasons=[
            "The case is active.",
            (
                "The case contains a missing or "
                "held payment."
            ),
            (
                "Relevant HA-PAY policy evidence "
                "was retrieved."
            ),
        ],
    )