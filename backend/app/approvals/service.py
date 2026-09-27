from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.approvals.models import ApprovalRequest
from app.database.connection import SessionLocal
from app.database.models import ApprovalModel


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
    Create a pending human approval request.

    This function does NOT execute the requested action.
    """

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

    with SessionLocal() as session:
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


def list_pending_approvals(
    case_id: str | None = None,
) -> list[ApprovalRequest]:

    statement = (
        select(ApprovalModel)
        .where(
            ApprovalModel.status == "pending"
        )
        .order_by(
            ApprovalModel.requested_at
        )
    )

    if case_id is not None:
        statement = statement.where(
            ApprovalModel.case_id == case_id
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