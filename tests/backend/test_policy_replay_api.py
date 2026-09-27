import pytest

from fastapi.testclient import (
    TestClient,
)

from app.main import app


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


client = TestClient(
    app
)


def test_policy_replay_api():
    response = client.post(
        "/policy-replay",
        json={
            "case_id": "CF-10001",
            "action": (
                "open_investigation"
            ),
            "baseline_version": 1,
            "candidate_version": 2,
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["case_id"]
        == "CF-10001"
    )

    assert (
        data["baseline"]["allowed"]
        is True
    )

    assert (
        data["candidate"]["allowed"]
        is False
    )

    assert (
        data["outcome_changed"]
        is True
    )

    assert (
        data["change_type"]
        == "newly_blocked"
    )


def test_policy_replay_batch_api():
    response = client.post(
        "/policy-replay/batch",
        json={
            "action": (
                "open_investigation"
            ),
            "baseline_version": 1,
            "candidate_version": 2,
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["total_cases"]
        >= 3
    )

    assert (
        data["changed_cases"]
        >= 1
    )

    assert (
        len(data["results"])
        == data["total_cases"]
    )


def test_policy_replay_case_not_found():
    response = client.post(
        "/policy-replay",
        json={
            "case_id": (
                "CF-DOES-NOT-EXIST"
            ),
            "action": (
                "open_investigation"
            ),
            "baseline_version": 1,
            "candidate_version": 2,
        },
    )

    assert (
        response.status_code
        == 404
    )