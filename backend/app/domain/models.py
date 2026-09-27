from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class CaseStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"


class ActionType(str, Enum):
    CHECK_PAYMENT = "check_payment"
    OPEN_INVESTIGATION = "open_investigation"
    REQUEST_DOCUMENT = "request_document"
    UPDATE_CONTACT_INFO = "update_contact_info"
    CLOSE_CASE = "close_case"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Case:
    case_id: str
    program: str
    status: CaseStatus
    citizen_id: str
    created_at: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class ProposedAction:
    action_type: ActionType
    case_id: str
    reason: str
    risk_level: RiskLevel
    requires_human_approval: bool


@dataclass
class PolicyVersion:
    policy_id: str
    title: str
    version: int
    effective_date: datetime
    content: str


@dataclass
class AuditEvent:
    event_type: str
    case_id: str
    timestamp: datetime
    details: dict = field(default_factory=dict)


@dataclass
class Citizen:
    citizen_id: str
    full_name: str
    email: str | None
    phone: str | None


@dataclass
class Payment:
    payment_id: str
    amount: Decimal
    scheduled_date: date
    paid_date: date | None
    status: str


@dataclass
class Document:
    document_id: str
    document_type: str
    file_name: str
    uploaded_at: datetime
    review_status: str


@dataclass
class CaseEvent:
    event_id: str
    event_type: str
    description: str | None
    created_at: datetime


@dataclass
class Approval:
    approval_id: str
    action_type: str
    status: str
    requested_at: datetime
    decided_at: datetime | None
    reviewer: str | None


@dataclass
class CaseContext:
    case: Case
    citizen: Citizen
    payments: list[Payment]
    documents: list[Document]
    events: list[CaseEvent]
    approvals: list[Approval]

@dataclass
class CaseAnalysis:
    case_id: str
    request_type: str
    facts: list[str]
    recommended_action: ActionType | None