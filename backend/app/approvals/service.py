from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.approvals.models import ApprovalRequest
from app.database.connection import SessionLocal
from app.database.models import ApprovalModel


VALID_APPROVAL_STATUSES = {
    "pending",
    "approved",
    "rejected",
}


def _to_approval_request(
    model: ApprovalModel,
) -> ApprovalRequest:

    return ApprovalRequest(
        approval_id=model.approval_id,
        case_id=model.case_id,
        action_type=model.action_type,
        status=model.status,
        requested_at=model.requested_at,
        decided_at=model.decided_at,
        reviewer=model.reviewer,
    )


def create_approval_request(
    case_id: str,
    action_type: str,
) -> ApprovalRequest:
    """
    Create a pending approval request.

    If the same case/action already has a pending
    approval, reuse it instead of creating duplicates.

    This function does NOT execute the action.
    """

    with SessionLocal() as session:
        statement = (
            select(ApprovalModel)
            .where(
                ApprovalModel.case_id == case_id,
                ApprovalModel.action_type == action_type,
                ApprovalModel.status == "pending",
            )
        )

        existing = (
            session.execute(statement)
            .scalars()
            .first()
        )

        if existing is not None:
            return _to_approval_request(
                existing
            )

        approval = ApprovalModel(
            approval_id=(
                f"APR-{uuid4().hex[:12].upper()}"
            ),
            case_id=case_id,
            action_type=action_type,
            status="pending",
            requested_at=datetime.now(
                timezone.utc
            ),
            decided_at=None,
            reviewer=None,
        )

        session.add(approval)
        session.commit()
        session.refresh(approval)

        return _to_approval_request(
            approval
        )


def get_approval_request(
    approval_id: str,
) -> ApprovalRequest | None:

    with SessionLocal() as session:
        approval = session.get(
            ApprovalModel,
            approval_id,
        )

        if approval is None:
            return None

        return _to_approval_request(
            approval
        )


def list_approval_requests(
    case_id: str | None = None,
    status: str | None = None,
) -> list[ApprovalRequest]:

    statement = select(
        ApprovalModel
    )

    if case_id is not None:
        statement = statement.where(
            ApprovalModel.case_id == case_id
        )

    if status is not None:
        statement = statement.where(
            ApprovalModel.status == status
        )

    statement = statement.order_by(
        ApprovalModel.requested_at
    )

    with SessionLocal() as session:
        approvals = (
            session.execute(statement)
            .scalars()
            .all()
        )

        return [
            _to_approval_request(
                approval
            )
            for approval in approvals
        ]


def list_pending_approvals(
    case_id: str | None = None,
) -> list[ApprovalRequest]:

    return list_approval_requests(
        case_id=case_id,
        status="pending",
    )


def decide_approval_request(
    approval_id: str,
    decision: str,
    reviewer: str,
) -> ApprovalRequest | None:
    """
    Approve or reject a pending approval.

    The decision is persisted, but the underlying
    state-changing action is NOT executed here.
    """

    if decision not in {
        "approved",
        "rejected",
    }:
        raise ValueError(
            "Decision must be approved or rejected."
        )

    reviewer = reviewer.strip()

    if not reviewer:
        raise ValueError(
            "Reviewer is required."
        )

    with SessionLocal() as session:
        approval = session.get(
            ApprovalModel,
            approval_id,
        )

        if approval is None:
            return None

        if approval.status != "pending":
            raise ValueError(
                "Approval has already been decided."
            )

        approval.status = decision
        approval.reviewer = reviewer
        approval.decided_at = datetime.now(
            timezone.utc
        )

        session.commit()
        session.refresh(approval)

        return _to_approval_request(
            approval
        )


def approve_approval_request(
    approval_id: str,
    reviewer: str,
) -> ApprovalRequest | None:

    return decide_approval_request(
        approval_id=approval_id,
        decision="approved",
        reviewer=reviewer,
    )


def reject_approval_request(
    approval_id: str,
    reviewer: str,
) -> ApprovalRequest | None:

    return decide_approval_request(
        approval_id=approval_id,
        decision="rejected",
        reviewer=reviewer,
    )