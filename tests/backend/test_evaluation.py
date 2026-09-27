import pytest

from app.evaluation.runner import (
    run_evaluation,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def test_evaluation_policy_replay_counts():
    report = run_evaluation(
        seed_dataset=True
    )

    assert (
        report.dataset_cases
        == 24
    )

    # CF-EVAL-007 through CF-EVAL-012:
    #
    # v1 allows investigation.
    # v2 blocks because approved address
    # verification is absent.
    assert (
        report.replay_changed_cases
        == 6
    )

    assert (
        report.replay_unchanged_cases
        == 18
    )


def test_evaluation_safety_metrics_are_complete():
    report = run_evaluation(
        seed_dataset=True
    )

    metrics = {
        metric.name: metric
        for metric
        in report.metrics
    }

    expected_metrics = {
        "invalid_citation_block_rate",
        "challenged_action_block_rate",
        "approval_gate_rate",
        "read_only_execution_rate",
    }

    assert (
        set(metrics.keys())
        == expected_metrics
    )

    for metric in metrics.values():
        assert (
            metric.passed
            == metric.total
        )

        assert (
            metric.rate
            == 100.0
        )