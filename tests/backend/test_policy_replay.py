import pytest

from app.domain.models import (
    ActionType,
)
from app.replay.service import (
    replay_all_cases,
    replay_case,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def test_policy_replay_detects_newly_blocked_case():
    result = replay_case(
        case_id="CF-10001",
        action=(
            ActionType.OPEN_INVESTIGATION
        ),
        baseline_version=1,
        candidate_version=2,
    )

    assert (
        result.baseline.allowed
        is True
    )

    assert (
        result.candidate.allowed
        is False
    )

    assert (
        result.outcome_changed
        is True
    )

    assert (
        result.change_type
        == "newly_blocked"
    )


def test_check_payment_is_unchanged():
    result = replay_case(
        case_id="CF-10001",
        action=(
            ActionType.CHECK_PAYMENT
        ),
        baseline_version=1,
        candidate_version=2,
    )

    assert (
        result.baseline.allowed
        is True
    )

    assert (
        result.candidate.allowed
        is True
    )

    assert (
        result.outcome_changed
        is False
    )

    assert (
        result.change_type
        == "unchanged"
    )


def test_replay_rejects_unknown_policy_version():
    with pytest.raises(
        ValueError
    ):
        replay_case(
            case_id="CF-10001",
            action=(
                ActionType.OPEN_INVESTIGATION
            ),
            baseline_version=1,
            candidate_version=99,
        )


def test_batch_replay_runs_seeded_cases():
    result = replay_all_cases(
        action=(
            ActionType.OPEN_INVESTIGATION
        ),
        baseline_version=1,
        candidate_version=2,
    )

    assert (
        result.total_cases
        >= 3
    )

    assert (
        len(result.results)
        == result.total_cases
    )

    assert (
        result.changed_cases
        >= 1
    )

    assert any(
        replay.case_id
        == "CF-10001"
        and replay.outcome_changed
        for replay
        in result.results
    )