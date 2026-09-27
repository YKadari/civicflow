import pytest

from fastapi.testclient import TestClient

from app.approvals.service import (
    create_approval_request,
)
from app.main import app


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


client = TestClient(
    app
)


def test_list_approvals():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="open_investigation",
    )

    response = client.get(
        "/approvals",
        params={
            "case_id": "CF-10001",
            "status": "pending",
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert any(
        approval["approval_id"]
        == created.approval_id
        for approval in data
    )


def test_get_approval():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="open_investigation",
    )

    response = client.get(
        (
            f"/approvals/"
            f"{created.approval_id}"
        )
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["approval_id"]
        == created.approval_id
    )

    assert (
        data["status"]
        == "pending"
    )


def test_approve_approval():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="open_investigation",
    )

    response = client.post(
        (
            f"/approvals/"
            f"{created.approval_id}"
            "/approve"
        ),
        json={
            "reviewer": "Case Worker A"
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["status"]
        == "approved"
    )

    assert (
        data["reviewer"]
        == "Case Worker A"
    )

    assert (
        data["decided_at"]
        is not None
    )


def test_reject_approval():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="open_investigation",
    )

    response = client.post(
        (
            f"/approvals/"
            f"{created.approval_id}"
            "/reject"
        ),
        json={
            "reviewer": "Case Worker B"
        },
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["status"]
        == "rejected"
    )

    assert (
        data["reviewer"]
        == "Case Worker B"
    )


def test_cannot_decide_approval_twice():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="open_investigation",
    )

    first_response = client.post(
        (
            f"/approvals/"
            f"{created.approval_id}"
            "/approve"
        ),
        json={
            "reviewer": "Reviewer A"
        },
    )

    assert (
        first_response.status_code
        == 200
    )

    second_response = client.post(
        (
            f"/approvals/"
            f"{created.approval_id}"
            "/reject"
        ),
        json={
            "reviewer": "Reviewer B"
        },
    )

    assert (
        second_response.status_code
        == 409
    )


def test_approval_not_found():
    response = client.get(
        "/approvals/APR-DOES-NOT-EXIST"
    )

    assert (
        response.status_code
        == 404
    )