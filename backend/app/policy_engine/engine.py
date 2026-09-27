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
    Deterministically determine whether an action
    satisfies the implemented policy rules.

    Passing this check does NOT mean a state-changing
    action can automatically execute.

    Tool permissions and human approval are handled
    separately.
    """

    if action == ActionType.CHECK_PAYMENT:
        return _evaluate_check_payment(
            context=context,
            policy_evidence=policy_evidence,
        )

    if action == ActionType.OPEN_INVESTIGATION:
        return _evaluate_open_investigation(
            context=context,
            policy_evidence=policy_evidence,
        )

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


def _evaluate_open_investigation(
    context: CaseContext,
    policy_evidence: list[PolicyEvidence],
) -> PolicyCheckResult:
    """
    Determine whether the case is eligible to be
    routed to a human for consideration of a payment
    investigation.

    This does NOT authorize automatic execution.
    """

    reasons: list[str] = []

    case_is_active = (
        context.case.status
        == CaseStatus.ACTIVE
    )

    has_missing_payment = any(
        payment.status.lower() == "missing"
        for payment in context.payments
    )

    has_missing_payment_policy = any(
        evidence.policy_id == "HA-PAY"
        and "4.2" in evidence.section
        for evidence in policy_evidence
    )

    if not case_is_active:
        reasons.append(
            "The case is not active."
        )

    if not has_missing_payment:
        reasons.append(
            (
                "The case does not contain a "
                "missing payment."
            )
        )

    if not has_missing_payment_policy:
        reasons.append(
            (
                "HA-PAY section 4.2 was not "
                "included in the retrieved "
                "policy evidence."
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
            "The case contains a missing payment.",
            (
                "HA-PAY section 4.2 makes the case "
                "eligible for human consideration "
                "of a payment investigation."
            ),
        ],
    )