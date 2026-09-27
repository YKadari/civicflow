from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    case_id: str
    action_type: str
    status: str
    requested_at: datetime
    decided_at: datetime | None
    reviewer: str | None