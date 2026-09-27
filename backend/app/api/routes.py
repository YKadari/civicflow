from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.base import AIProvider
from app.ai.factory import (
    get_ai_provider,
)
from app.api.schemas import (
    AnalyzeCaseRequest,
    ApprovalDecisionRequest,
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
    PolicyReplayBatchRequest,
    PolicyReplayBatchResponse,
    PolicyReplayRequest,
    PolicyReplayResponse,
    ReplayPolicyOutcomeResponse,
)
from app.approvals.models import (
    ApprovalRequest,
)
from app.approvals.service import (
    approve_approval_request,
    get_approval_request,
    list_approval_requests,
    reject_approval_request,
)
from app.database.repository import (
    create_case_request,
    get_case,
    get_case_context,
    list_cases,
)
from app.policies.base import (
    PolicyRetriever,
)
from app.policies.factory import (
    get_policy_retriever,
)

from app.domain.models import (
    ActionType,
)

from app.replay.models import (
    PolicyReplayResult,
    ReplayPolicyOutcome,
)

from app.replay.service import (
    replay_all_cases,
    replay_case,
)

from app.evaluation.runner import (
    evaluation_report_to_dict,
    run_evaluation,
)

router = APIRouter()


def _approval_response(
    approval: ApprovalRequest,
) -> ApprovalResponse:

    return ApprovalResponse(
        approval_id=(
            approval.approval_id
        ),
        case_id=approval.case_id,
        action_type=(
            approval.action_type
        ),
        status=approval.status,
        requested_at=(
            approval.requested_at
        ),
        decided_at=(
            approval.decided_at
        ),
        reviewer=approval.reviewer,
    )

def _replay_outcome_response(
    outcome: ReplayPolicyOutcome,
) -> ReplayPolicyOutcomeResponse:

    return ReplayPolicyOutcomeResponse(
        policy_id=outcome.policy_id,
        version=outcome.version,
        allowed=outcome.allowed,
        requires_human_review=(
            outcome.requires_human_review
        ),
        reasons=outcome.reasons,
    )


def _policy_replay_response(
    replay: PolicyReplayResult,
) -> PolicyReplayResponse:

    return PolicyReplayResponse(
        case_id=replay.case_id,
        action=replay.action,
        policy_id=replay.policy_id,

        baseline=(
            _replay_outcome_response(
                replay.baseline
            )
        ),

        candidate=(
            _replay_outcome_response(
                replay.candidate
            )
        ),

        outcome_changed=(
            replay.outcome_changed
        ),

        change_type=(
            replay.change_type
        ),
    )
@router.get(
    "/cases",
    response_model=list[
        CaseResponse
    ],
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


@router.get(
    "/cases/{case_id}",
    response_model=(
        CaseContextResponse
    ),
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
            case_id=(
                context.case.case_id
            ),
            citizen_id=(
                context.case.citizen_id
            ),
            program=(
                context.case.program
            ),
            status=(
                context.case.status.value
            ),
            created_at=(
                context.case.created_at
            ),
        ),

        citizen=CitizenResponse(
            citizen_id=(
                context.citizen.citizen_id
            ),
            full_name=(
                context.citizen.full_name
            ),
            email=(
                context.citizen.email
            ),
            phone=(
                context.citizen.phone
            ),
        ),

        payments=[
            PaymentResponse(
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
            in context.payments
        ],

        documents=[
            DocumentResponse(
                document_id=(
                    document.document_id
                ),
                document_type=(
                    document.document_type
                ),
                file_name=(
                    document.file_name
                ),
                uploaded_at=(
                    document.uploaded_at
                ),
                review_status=(
                    document.review_status
                ),
            )
            for document
            in context.documents
        ],

        events=[
            CaseEventResponse(
                event_id=(
                    event.event_id
                ),
                event_type=(
                    event.event_type
                ),
                description=(
                    event.description
                ),
                created_at=(
                    event.created_at
                ),
            )
            for event
            in context.events
        ],

        approvals=[
            ApprovalResponse(
                approval_id=(
                    approval.approval_id
                ),
                case_id=(
                    context.case.case_id
                ),
                action_type=(
                    approval.action_type
                ),
                status=(
                    approval.status
                ),
                requested_at=(
                    approval.requested_at
                ),
                decided_at=(
                    approval.decided_at
                ),
                reviewer=(
                    approval.reviewer
                ),
            )
            for approval
            in context.approvals
        ],
    )


@router.post(
    "/cases/{case_id}/requests",
    response_model=(
        CitizenRequestResponse
    ),
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
        description=(
            request.description
        ),
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
    response_model=(
        CaseAnalysisResponse
    ),
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
    graph = build_case_analysis_graph(
        ai_provider=ai_provider,
        policy_retriever=(
            policy_retriever
        ),
    )

    result = graph.invoke(
        {
            "case_id": case_id,
            "event_id": (
                request.event_id
            ),
        }
    )

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

    payment_check = result.get(
        "payment_check_result"
    )

    approval = result.get(
        "approval_request"
    )

    return CaseAnalysisResponse(
        case_id=result["case_id"],

        request_type=result[
            "request_type"
        ],

        facts=result.get(
            "facts",
            [],
        ),

        recommended_action=result.get(
            "recommended_action"
        ),

        classification_confidence=(
            result.get(
                "classification_confidence"
            )
        ),

        classification_source=(
            result.get(
                "classification_source",
                "unknown",
            )
        ),

        requires_human_review=(
            result.get(
                "requires_human_review",
                True,
            )
        ),

        policy_evidence=[
            PolicyEvidenceResponse(
                chunk_id=(
                    evidence.chunk_id
                ),
                policy_id=(
                    evidence.policy_id
                ),
                version=(
                    evidence.version
                ),
                section=(
                    evidence.section
                ),
                content=(
                    evidence.content
                ),
                similarity=(
                    evidence.similarity
                ),
            )
            for evidence
            in result.get(
                "policy_evidence",
                [],
            )
        ],

        recommendation_rationale=(
            result.get(
                "recommendation_rationale"
            )
        ),

        recommendation_confidence=(
            result.get(
                "recommendation_confidence"
            )
        ),

        cited_policy_chunks=(
            result.get(
                "cited_policy_chunks",
                [],
            )
        ),

        policy_check_allowed=(
            result.get(
                "policy_check_allowed"
            )
        ),

        policy_check_reasons=(
            result.get(
                "policy_check_reasons",
                [],
            )
        ),

        decision_challenge_passed=(
            result.get(
                "decision_challenge_passed"
            )
        ),

        challenge_verdict=(
            result.get(
                "challenge_verdict"
            )
        ),

        challenge_reasons=(
            result.get(
                "challenge_reasons",
                [],
            )
        ),

        challenge_confidence=(
            result.get(
                "challenge_confidence"
            )
        ),

        challenge_cited_policy_chunks=(
            result.get(
                "challenge_cited_policy_chunks",
                [],
            )
        ),

        challenge_missing_evidence=(
            result.get(
                "challenge_missing_evidence",
                [],
            )
        ),

        challenged_action=(
            result.get(
                "challenged_action"
            )
        ),

        tool_access_mode=(
            result.get(
                "tool_access_mode"
            )
        ),

        tool_requires_approval=(
            result.get(
                "tool_requires_approval"
            )
        ),

        approval_request=(
            _approval_response(
                approval
            )
            if approval is not None
            else None
        ),

        executed_tool=result.get(
            "executed_tool"
        ),

        payment_check_result=(
            PaymentCheckResponse(
                success=(
                    payment_check.success
                ),
                case_id=(
                    payment_check.case_id
                ),
                payments=[
                    PaymentRecordResponse(
                        payment_id=(
                            payment.payment_id
                        ),
                        amount=(
                            payment.amount
                        ),
                        scheduled_date=(
                            payment.scheduled_date
                        ),
                        paid_date=(
                            payment.paid_date
                        ),
                        status=(
                            payment.status
                        ),
                    )
                    for payment
                    in payment_check.payments
                ],
                message=(
                    payment_check.message
                ),
            )
            if payment_check is not None
            else None
        ),
    )


@router.get(
    "/approvals",
    response_model=list[
        ApprovalResponse
    ],
)
def get_approvals(
    case_id: str | None = None,
    status: str | None = None,
):
    if (
        status is not None
        and status
        not in {
            "pending",
            "approved",
            "rejected",
        }
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid approval status"
            ),
        )

    approvals = (
        list_approval_requests(
            case_id=case_id,
            status=status,
        )
    )

    return [
        _approval_response(
            approval
        )
        for approval in approvals
    ]


@router.get(
    "/approvals/{approval_id}",
    response_model=ApprovalResponse,
)
def get_approval(
    approval_id: str,
):
    approval = (
        get_approval_request(
            approval_id
        )
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found",
        )

    return _approval_response(
        approval
    )


@router.post(
    "/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
)
def approve_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
):
    try:
        approval = (
            approve_approval_request(
                approval_id=approval_id,
                reviewer=request.reviewer,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found",
        )

    return _approval_response(
        approval
    )


@router.post(
    "/approvals/{approval_id}/reject",
    response_model=ApprovalResponse,
)
def reject_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
):
    try:
        approval = (
            reject_approval_request(
                approval_id=approval_id,
                reviewer=request.reviewer,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found",
        )

    return _approval_response(
        approval
    )

# ============================================================
# Policy Replay
# ============================================================


@router.post(
    "/policy-replay",
    response_model=PolicyReplayResponse,
)
def run_policy_replay(
    request: PolicyReplayRequest,
):
    try:
        result = replay_case(
            case_id=request.case_id,
            action=ActionType(
                request.action
            ),
            baseline_version=(
                request.baseline_version
            ),
            candidate_version=(
                request.candidate_version
            ),
        )

    except ValueError as exc:
        message = str(exc)

        if message == "Case not found":
            raise HTTPException(
                status_code=404,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=400,
            detail=message,
        ) from exc

    return _policy_replay_response(
        result
    )


@router.post(
    "/policy-replay/batch",
    response_model=(
        PolicyReplayBatchResponse
    ),
)
def run_policy_replay_batch(
    request: PolicyReplayBatchRequest,
):
    try:
        result = replay_all_cases(
            action=ActionType(
                request.action
            ),
            baseline_version=(
                request.baseline_version
            ),
            candidate_version=(
                request.candidate_version
            ),
            case_ids=request.case_ids,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return PolicyReplayBatchResponse(
        action=result.action,
        policy_id=result.policy_id,

        baseline_version=(
            result.baseline_version
        ),

        candidate_version=(
            result.candidate_version
        ),

        total_cases=(
            result.total_cases
        ),

        changed_cases=(
            result.changed_cases
        ),

        unchanged_cases=(
            result.unchanged_cases
        ),

        results=[
            _policy_replay_response(
                replay
            )
            for replay
            in result.results
        ],
    )

# ============================================================
# Evaluation
# ============================================================


@router.get(
    "/evaluation",
)
def get_evaluation():
    report = run_evaluation(
        seed_dataset=True
    )

    return evaluation_report_to_dict(
        report
    )