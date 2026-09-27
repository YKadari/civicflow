from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class CaseResponse(BaseModel):
    case_id: str
    citizen_id: str
    program: str
    status: str
    created_at: datetime


class CitizenResponse(BaseModel):
    citizen_id: str
    full_name: str
    email: str | None
    phone: str | None


class PaymentResponse(BaseModel):
    payment_id: str
    amount: Decimal
    scheduled_date: date
    paid_date: date | None
    status: str


class DocumentResponse(BaseModel):
    document_id: str
    document_type: str
    file_name: str
    uploaded_at: datetime
    review_status: str


class CaseEventResponse(BaseModel):
    event_id: str
    event_type: str
    description: str | None
    created_at: datetime


class ApprovalResponse(BaseModel):
    approval_id: str
    case_id: str
    action_type: str
    status: str
    requested_at: datetime
    decided_at: datetime | None
    reviewer: str | None


class ApprovalDecisionRequest(
    BaseModel
):
    reviewer: str = Field(
        min_length=1
    )


class CaseContextResponse(BaseModel):
    case: CaseResponse
    citizen: CitizenResponse
    payments: list[PaymentResponse]
    documents: list[DocumentResponse]
    events: list[CaseEventResponse]
    approvals: list[ApprovalResponse]


class CitizenRequestCreate(
    BaseModel
):
    description: str


class CitizenRequestResponse(
    BaseModel
):
    event_id: str
    event_type: str
    description: str | None
    created_at: datetime


class AnalyzeCaseRequest(BaseModel):
    event_id: str


class PolicyEvidenceResponse(
    BaseModel
):
    chunk_id: str
    policy_id: str
    version: int
    section: str
    content: str
    similarity: float


class PaymentRecordResponse(
    BaseModel
):
    payment_id: str
    amount: Decimal
    scheduled_date: date
    paid_date: date | None
    status: str


class PaymentCheckResponse(
    BaseModel
):
    success: bool
    case_id: str
    payments: list[
        PaymentRecordResponse
    ]
    message: str


class CaseAnalysisResponse(
    BaseModel
):
    case_id: str
    request_type: str

    facts: list[str]

    recommended_action: str | None

    classification_confidence: (
        float | None
    ) = None

    classification_source: str

    requires_human_review: bool

    policy_evidence: list[
        PolicyEvidenceResponse
    ]

    recommendation_rationale: (
        str | None
    ) = None

    recommendation_confidence: (
        float | None
    ) = None

    cited_policy_chunks: list[str] = Field(
        default_factory=list
    )

    policy_check_allowed: (
        bool | None
    ) = None

    policy_check_reasons: list[str] = Field(
        default_factory=list
    )

    decision_challenge_passed: (
        bool | None
    ) = None

    challenge_verdict: (
        str | None
    ) = None

    challenge_reasons: list[str] = Field(
        default_factory=list
    )

    challenge_confidence: (
        float | None
    ) = None

    challenge_cited_policy_chunks: list[
        str
    ] = Field(
        default_factory=list
    )

    challenge_missing_evidence: list[
        str
    ] = Field(
        default_factory=list
    )

    challenged_action: (
        str | None
    ) = None

    tool_access_mode: (
        str | None
    ) = None

    tool_requires_approval: (
        bool | None
    ) = None

    approval_request: (
        ApprovalResponse | None
    ) = None

    executed_tool: (
        str | None
    ) = None

    payment_check_result: (
        PaymentCheckResponse | None
    ) = None


# ============================================================
# Policy Replay
# ============================================================


ReplayAction = Literal[
    "check_payment",
    "open_investigation",
]


class PolicyReplayRequest(
    BaseModel
):
    case_id: str

    action: ReplayAction

    baseline_version: int = Field(
        default=1,
        ge=1,
    )

    candidate_version: int = Field(
        default=2,
        ge=1,
    )


class PolicyReplayBatchRequest(
    BaseModel
):
    action: ReplayAction

    baseline_version: int = Field(
        default=1,
        ge=1,
    )

    candidate_version: int = Field(
        default=2,
        ge=1,
    )

    case_ids: list[str] | None = None


class ReplayPolicyOutcomeResponse(
    BaseModel
):
    policy_id: str
    version: int

    allowed: bool

    requires_human_review: bool

    reasons: list[str] = Field(
        default_factory=list
    )


class PolicyReplayResponse(
    BaseModel
):
    case_id: str
    action: str
    policy_id: str

    baseline: (
        ReplayPolicyOutcomeResponse
    )

    candidate: (
        ReplayPolicyOutcomeResponse
    )

    outcome_changed: bool

    change_type: str


class PolicyReplayBatchResponse(
    BaseModel
):
    action: str
    policy_id: str

    baseline_version: int
    candidate_version: int

    total_cases: int
    changed_cases: int
    unchanged_cases: int

    results: list[
        PolicyReplayResponse
    ]