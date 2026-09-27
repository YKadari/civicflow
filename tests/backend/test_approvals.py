import pytest

from app.approvals.service import (
    approve_approval_request,
    create_approval_request,
    get_approval_request,
    list_pending_approvals,
    reject_approval_request,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def test_create_pending_approval():
    approval = create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    assert (
        approval.case_id
        == "CF-10001"
    )

    assert (
        approval.action_type
        == "request_document"
    )

    assert (
        approval.status
        == "pending"
    )

    assert (
        approval.reviewer
        is None
    )

    assert (
        approval.decided_at
        is None
    )


def test_get_approval_request():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    approval = get_approval_request(
        created.approval_id
    )

    assert approval is not None

    assert (
        approval.approval_id
        == created.approval_id
    )

    assert (
        approval.status
        == "pending"
    )


def test_list_pending_approvals():
    create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    approvals = list_pending_approvals(
        case_id="CF-10001"
    )

    assert len(
        approvals
    ) >= 1

    assert any(
        approval.action_type
        == "request_document"
        for approval in approvals
    )


def test_approve_pending_approval():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    approved = approve_approval_request(
        approval_id=created.approval_id,
        reviewer="Case Worker A",
    )

    assert approved is not None

    assert (
        approved.status
        == "approved"
    )

    assert (
        approved.reviewer
        == "Case Worker A"
    )

    assert (
        approved.decided_at
        is not None
    )


def test_reject_pending_approval():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    rejected = reject_approval_request(
        approval_id=created.approval_id,
        reviewer="Case Worker B",
    )

    assert rejected is not None

    assert (
        rejected.status
        == "rejected"
    )

    assert (
        rejected.reviewer
        == "Case Worker B"
    )


def test_cannot_decide_approval_twice():
    created = create_approval_request(
        case_id="CF-10001",
        action_type="request_document",
    )

    approve_approval_request(
        approval_id=created.approval_id,
        reviewer="Reviewer A",
    )

    with pytest.raises(
        ValueError
    ):
        reject_approval_request(
            approval_id=(
                created.approval_id
            ),
            reviewer="Reviewer B",
        )