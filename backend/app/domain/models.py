from dataclasses import dataclass, field
from datetime import datetime
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