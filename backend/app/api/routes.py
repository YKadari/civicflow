from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ApprovalResponse,
    CaseContextResponse,
    CaseEventResponse,
    CaseResponse,
    CitizenResponse,
    DocumentResponse,
    PaymentResponse,
    CitizenRequestCreate,
    CitizenRequestResponse,
    AnalyzeCaseRequest,
    CaseAnalysisResponse,
)
from app.database.repository import (
    create_case_request,
    get_case_context,
    list_cases,
)

from app.services.analysis import analyze_case_request

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

@router.get(
    "/cases",
    response_model=list[CaseResponse],
)
def read_cases(
    status: str | None = None,
    program: str | None = None,
):
    cases = list_cases(
        status=status,
        program=program,
    )

    return [
        CaseResponse(
            case_id=case.case_id,
            program=case.program,
            status=case.status.value,
            citizen_id=case.citizen_id,
            created_at=case.created_at,
        )
        for case in cases
    ]

@router.post(
    "/cases/{case_id}/requests",
    response_model=CitizenRequestResponse,
    status_code=201,
)
def create_request(
    case_id: str,
    request: CitizenRequestCreate,
):
    event = create_case_request(
        case_id=case_id,
        description=request.description,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return CitizenRequestResponse(
        event_id=event.event_id,
        event_type=event.event_type,
        description=event.description,
        created_at=event.created_at,
    )

@router.post(
    "/cases/{case_id}/analyze",
    response_model=CaseAnalysisResponse,
)
def analyze_request(
    case_id: str,
    request: AnalyzeCaseRequest,
):
    analysis = analyze_case_request(
        case_id=case_id,
        event_id=request.event_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Case or request not found",
        )

    return CaseAnalysisResponse(
        case_id=analysis.case_id,
        request_type=analysis.request_type,
        facts=analysis.facts,
        recommended_action=(
            analysis.recommended_action.value
            if analysis.recommended_action
            else None
        ),
    )