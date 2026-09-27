from app.database.repository import (
    get_case_context,
    list_cases,
)
from app.domain.models import (
    ActionType,
    CaseContext,
    CaseStatus,
)
from app.replay.models import (
    PolicyReplayBatchResult,
    PolicyReplayResult,
    ReplayPolicyOutcome,
)
from app.replay.policy_versions import (
    get_policy_version,
)


SUPPORTED_REPLAY_ACTIONS = {
    ActionType.CHECK_PAYMENT,
    ActionType.OPEN_INVESTIGATION,
}


def _has_missing_payment(
    context: CaseContext,
) -> bool:

    return any(
        payment.status.lower()
        == "missing"
        for payment
        in context.payments
    )


def _has_missing_or_held_payment(
    context: CaseContext,
) -> bool:

    return any(
        payment.status.lower()
        in {
            "missing",
            "held",
        }
        for payment
        in context.payments
    )


def _has_approved_address_verification(
    context: CaseContext,
) -> bool:

    return any(
        document.document_type.lower()
        == "address_verification"
        and document.review_status.lower()
        == "approved"
        for document
        in context.documents
    )


def _evaluate_check_payment(
    context: CaseContext,
    version: int,
) -> ReplayPolicyOutcome:

    reasons: list[str] = []

    case_is_active = (
        context.case.status
        == CaseStatus.ACTIVE
    )

    has_payment_issue = (
        _has_missing_or_held_payment(
            context
        )
    )

    if not case_is_active:
        reasons.append(
            "The case is not active."
        )

    if not has_payment_issue:
        reasons.append(
            (
                "The case does not contain "
                "a missing or held payment."
            )
        )

    if reasons:
        return ReplayPolicyOutcome(
            policy_id="HA-PAY",
            version=version,
            allowed=False,
            requires_human_review=True,
            reasons=reasons,
        )

    return ReplayPolicyOutcome(
        policy_id="HA-PAY",
        version=version,
        allowed=True,
        requires_human_review=False,
        reasons=[
            "The case is active.",
            (
                "The case contains a missing "
                "or held payment."
            ),
            (
                "The payment may be checked "
                "under this policy version."
            ),
        ],
    )


def _evaluate_open_investigation_v1(
    context: CaseContext,
) -> ReplayPolicyOutcome:

    reasons: list[str] = []

    case_is_active = (
        context.case.status
        == CaseStatus.ACTIVE
    )

    has_missing_payment = (
        _has_missing_payment(
            context
        )
    )

    if not case_is_active:
        reasons.append(
            "The case is not active."
        )

    if not has_missing_payment:
        reasons.append(
            (
                "The case does not contain "
                "a missing payment."
            )
        )

    if reasons:
        return ReplayPolicyOutcome(
            policy_id="HA-PAY",
            version=1,
            allowed=False,
            requires_human_review=True,
            reasons=reasons,
        )

    return ReplayPolicyOutcome(
        policy_id="HA-PAY",
        version=1,
        allowed=True,
        requires_human_review=False,
        reasons=[
            "The case is active.",
            (
                "The case contains a missing "
                "payment."
            ),
            (
                "HA-PAY v1 permits the case "
                "to be considered for a "
                "payment-status investigation."
            ),
        ],
    )


def _evaluate_open_investigation_v2(
    context: CaseContext,
) -> ReplayPolicyOutcome:

    reasons: list[str] = []

    case_is_active = (
        context.case.status
        == CaseStatus.ACTIVE
    )

    has_missing_payment = (
        _has_missing_payment(
            context
        )
    )

    has_approved_address = (
        _has_approved_address_verification(
            context
        )
    )

    if not case_is_active:
        reasons.append(
            "The case is not active."
        )

    if not has_missing_payment:
        reasons.append(
            (
                "The case does not contain "
                "a missing payment."
            )
        )

    if not has_approved_address:
        reasons.append(
            (
                "HA-PAY v2 requires approved "
                "address verification before "
                "a payment-status investigation "
                "may be considered."
            )
        )

    if reasons:
        return ReplayPolicyOutcome(
            policy_id="HA-PAY",
            version=2,
            allowed=False,
            requires_human_review=True,
            reasons=reasons,
        )

    return ReplayPolicyOutcome(
        policy_id="HA-PAY",
        version=2,
        allowed=True,
        requires_human_review=False,
        reasons=[
            "The case is active.",
            (
                "The case contains a missing "
                "payment."
            ),
            (
                "Approved address verification "
                "is present."
            ),
            (
                "HA-PAY v2 permits the case "
                "to be considered for a "
                "payment-status investigation."
            ),
        ],
    )


def evaluate_policy_version(
    context: CaseContext,
    action: ActionType,
    version: int,
) -> ReplayPolicyOutcome:

    policy = get_policy_version(
        policy_id="HA-PAY",
        version=version,
    )

    if policy is None:
        raise ValueError(
            (
                "Unsupported HA-PAY policy "
                f"version: {version}"
            )
        )

    if action not in SUPPORTED_REPLAY_ACTIONS:
        raise ValueError(
            (
                "Policy Replay currently supports "
                "check_payment and "
                "open_investigation."
            )
        )

    if action == ActionType.CHECK_PAYMENT:
        return _evaluate_check_payment(
            context=context,
            version=version,
        )

    if (
        action
        == ActionType.OPEN_INVESTIGATION
    ):
        if version == 1:
            return (
                _evaluate_open_investigation_v1(
                    context
                )
            )

        if version == 2:
            return (
                _evaluate_open_investigation_v2(
                    context
                )
            )

    raise ValueError(
        "Unsupported replay configuration."
    )


def _determine_change_type(
    baseline: ReplayPolicyOutcome,
    candidate: ReplayPolicyOutcome,
) -> str:

    if (
        baseline.allowed
        == candidate.allowed
    ):
        return "unchanged"

    if (
        baseline.allowed
        and not candidate.allowed
    ):
        return "newly_blocked"

    if (
        not baseline.allowed
        and candidate.allowed
    ):
        return "newly_allowed"

    return "changed"


def replay_case(
    case_id: str,
    action: ActionType,
    baseline_version: int,
    candidate_version: int,
) -> PolicyReplayResult:

    context = get_case_context(
        case_id
    )

    if context is None:
        raise ValueError(
            "Case not found"
        )

    baseline = evaluate_policy_version(
        context=context,
        action=action,
        version=baseline_version,
    )

    candidate = evaluate_policy_version(
        context=context,
        action=action,
        version=candidate_version,
    )

    outcome_changed = (
        baseline.allowed
        != candidate.allowed
    )

    return PolicyReplayResult(
        case_id=case_id,
        action=action.value,
        policy_id="HA-PAY",
        baseline=baseline,
        candidate=candidate,
        outcome_changed=(
            outcome_changed
        ),
        change_type=(
            _determine_change_type(
                baseline=baseline,
                candidate=candidate,
            )
        ),
    )


def replay_all_cases(
    action: ActionType,
    baseline_version: int,
    candidate_version: int,
    case_ids: list[str] | None = None,
) -> PolicyReplayBatchResult:

    if case_ids is None:
        cases = list_cases()

        replay_case_ids = [
            case.case_id
            for case in cases
        ]

    else:
        replay_case_ids = case_ids

    results = [
        replay_case(
            case_id=case_id,
            action=action,
            baseline_version=(
                baseline_version
            ),
            candidate_version=(
                candidate_version
            ),
        )
        for case_id
        in replay_case_ids
    ]

    changed_cases = sum(
        1
        for result in results
        if result.outcome_changed
    )

    return PolicyReplayBatchResult(
        action=action.value,
        policy_id="HA-PAY",
        baseline_version=(
            baseline_version
        ),
        candidate_version=(
            candidate_version
        ),
        total_cases=len(results),
        changed_cases=changed_cases,
        unchanged_cases=(
            len(results)
            - changed_cases
        ),
        results=results,
    )