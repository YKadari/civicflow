from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider
from app.api.schemas import (
    AnalyzeCaseRequest,
    ApprovalResponse,
    CaseAnalysisResponse,
    CaseContextResponse,
    CaseEventResponse,
    CaseResponse,
    CitizenRequestCreate,
    CitizenRequestResponse,
    CitizenResponse,
    DocumentResponse,
    PaymentCheckResponse,
    PaymentRecordResponse,
    PaymentResponse,
    PolicyEvidenceResponse,
)
from app.database.repository import (
    create_case_request,
    get_case,
    get_case_context,
    list_cases,
)
from app.policies.base import PolicyRetriever
from app.policies.factory import (
    get_policy_retriever,
)


router = APIRouter()


# ============================================================
# GET /cases
# ============================================================


@router.get(
    "/cases",
    response_model=list[CaseResponse],
)
def get_cases(
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
            citizen_id=case.citizen_id,
            program=case.program,
            status=case.status.value,
            created_at=case.created_at,
        )
        for case in cases
    ]


# ============================================================
# GET /cases/{case_id}
# ============================================================


@router.get(
    "/cases/{case_id}",
    response_model=CaseContextResponse,
)
def get_case_details(
    case_id: str,
):
    context = get_case_context(
        case_id
    )

    if context is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return CaseContextResponse(
        case=CaseResponse(
            case_id=context.case.case_id,
            citizen_id=context.case.citizen_id,
            program=context.case.program,
            status=context.case.status.value,
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
                scheduled_date=(
                    payment.scheduled_date
                ),
                paid_date=payment.paid_date,
                status=payment.status,
            )
            for payment in context.payments
        ],
        documents=[
            DocumentResponse(
                document_id=document.document_id,
                document_type=(
                    document.document_type
                ),
                file_name=document.file_name,
                uploaded_at=document.uploaded_at,
                review_status=(
                    document.review_status
                ),
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
                requested_at=(
                    approval.requested_at
                ),
                decided_at=approval.decided_at,
                reviewer=approval.reviewer,
            )
            for approval in context.approvals
        ],
    )


# ============================================================
# POST /cases/{case_id}/requests
# ============================================================


@router.post(
    "/cases/{case_id}/requests",
    response_model=CitizenRequestResponse,
    status_code=201,
)
def create_request(
    case_id: str,
    request: CitizenRequestCreate,
):
    case = get_case(
        case_id
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

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


# ============================================================
# POST /cases/{case_id}/analyze
# ============================================================


@router.post(
    "/cases/{case_id}/analyze",
    response_model=CaseAnalysisResponse,
)
def analyze_case(
    case_id: str,
    request: AnalyzeCaseRequest,
    ai_provider: AIProvider = Depends(
        get_ai_provider
    ),
    policy_retriever: PolicyRetriever = Depends(
        get_policy_retriever
    ),
):
    # --------------------------------------------------------
    # Build the CivicFlow LangGraph
    # --------------------------------------------------------

    graph = build_case_analysis_graph(
        ai_provider=ai_provider,
        policy_retriever=policy_retriever,
    )

    # --------------------------------------------------------
    # Execute the graph
    # --------------------------------------------------------

    result = graph.invoke(
        {
            "case_id": case_id,
            "event_id": request.event_id,
        }
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Handle graph errors BEFORE accessing fields such as
    # request_type, facts, policy evidence, etc.
    # --------------------------------------------------------

    error = result.get(
        "error"
    )

    if error == "Case not found":
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    if error == "Request not found":
        raise HTTPException(
            status_code=404,
            detail="Request not found",
        )

    if error:
        raise HTTPException(
            status_code=400,
            detail=error,
        )

    # --------------------------------------------------------
    # Tool result
    # --------------------------------------------------------

    payment_check = result.get(
        "payment_check_result"
    )

    # --------------------------------------------------------
    # Build API response
    # --------------------------------------------------------

    return CaseAnalysisResponse(
        case_id=result["case_id"],
        request_type=result["request_type"],
        facts=result.get(
            "facts",
            [],
        ),
        recommended_action=result.get(
            "recommended_action"
        ),
        classification_confidence=result.get(
            "classification_confidence"
        ),
        classification_source=result.get(
            "classification_source",
            "unknown",
        ),
        requires_human_review=result.get(
            "requires_human_review",
            True,
        ),

        # ----------------------------------------------------
        # RAG policy evidence
        # ----------------------------------------------------

        policy_evidence=[
            PolicyEvidenceResponse(
                chunk_id=evidence.chunk_id,
                policy_id=evidence.policy_id,
                version=evidence.version,
                section=evidence.section,
                content=evidence.content,
                similarity=evidence.similarity,
            )
            for evidence in result.get(
                "policy_evidence",
                [],
            )
        ],

        # ----------------------------------------------------
        # Grounded recommendation
        # ----------------------------------------------------

        recommendation_rationale=result.get(
            "recommendation_rationale"
        ),
        recommendation_confidence=result.get(
            "recommendation_confidence"
        ),
        cited_policy_chunks=result.get(
            "cited_policy_chunks",
            [],
        ),

        # ----------------------------------------------------
        # Deterministic policy engine
        # ----------------------------------------------------

        policy_check_allowed=result.get(
            "policy_check_allowed"
        ),
        policy_check_reasons=result.get(
            "policy_check_reasons",
            [],
        ),

        # ----------------------------------------------------
        # Tool registry metadata
        # ----------------------------------------------------

        tool_access_mode=result.get(
            "tool_access_mode"
        ),
        tool_requires_approval=result.get(
            "tool_requires_approval"
        ),

        # ----------------------------------------------------
        # Tool execution
        # ----------------------------------------------------

        executed_tool=result.get(
            "executed_tool"
        ),

        payment_check_result=(
            PaymentCheckResponse(
                success=payment_check.success,
                case_id=payment_check.case_id,
                payments=[
                    PaymentRecordResponse(
                        payment_id=(
                            payment.payment_id
                        ),
                        amount=payment.amount,
                        scheduled_date=(
                            payment.scheduled_date
                        ),
                        paid_date=(
                            payment.paid_date
                        ),
                        status=payment.status,
                    )
                    for payment
                    in payment_check.payments
                ],
                message=payment_check.message,
            )
            if payment_check is not None
            else None
        ),
    )