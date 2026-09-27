from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ApprovalResponse,
    CaseContextResponse,
    CaseEventResponse,
    CaseResponse,
    CitizenResponse,
    DocumentResponse,
    PaymentResponse,
)
from app.database.repository import get_case_context


router = APIRouter()


@router.get(
    "/cases/{case_id}",
    response_model=CaseContextResponse,
)
def read_case(case_id: str):
    context = get_case_context(case_id)

    if context is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return CaseContextResponse(
        case=CaseResponse(
            case_id=context.case.case_id,
            program=context.case.program,
            status=context.case.status.value,
            citizen_id=context.case.citizen_id,
            created_at=context.case.created_at,
        ),
        citizen=CitizenResponse(
            citizen_id=context.citizen.citizen_id,
            full_name=context.citizen.full_name,
            email=context.citizen.email,
            phone=context.citizen.phone,
        ),
        payments=[
            PaymentResponse(
                payment_id=payment.payment_id,
                amount=payment.amount,
                scheduled_date=payment.scheduled_date,
                paid_date=payment.paid_date,
                status=payment.status,
            )
            for payment in context.payments
        ],
        documents=[
            DocumentResponse(
                document_id=document.document_id,
                document_type=document.document_type,
                file_name=document.file_name,
                uploaded_at=document.uploaded_at,
                review_status=document.review_status,
            )
            for document in context.documents
        ],
        events=[
            CaseEventResponse(
                event_id=event.event_id,
                event_type=event.event_type,
                description=event.description,
                created_at=event.created_at,
            )
            for event in context.events
        ],
        approvals=[
            ApprovalResponse(
                approval_id=approval.approval_id,
                action_type=approval.action_type,
                status=approval.status,
                requested_at=approval.requested_at,
                decided_at=approval.decided_at,
                reviewer=approval.reviewer,
            )
            for approval in context.approvals
        ],
    )