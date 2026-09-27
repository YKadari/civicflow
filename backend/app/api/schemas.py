from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CaseResponse(BaseModel):
    case_id: str
    program: str
    status: str
    citizen_id: str
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
    action_type: str
    status: str
    requested_at: datetime
    decided_at: datetime | None
    reviewer: str | None


class CaseContextResponse(BaseModel):
    case: CaseResponse
    citizen: CitizenResponse
    payments: list[PaymentResponse]
    documents: list[DocumentResponse]
    events: list[CaseEventResponse]
    approvals: list[ApprovalResponse]


class CitizenRequestCreate(BaseModel):
    description: str


class CitizenRequestResponse(BaseModel):
    event_id: str
    event_type: str
    description: str | None
    created_at: datetime

class AnalyzeCaseRequest(BaseModel):
    event_id: str


class CaseAnalysisResponse(BaseModel):
    case_id: str
    request_type: str
    facts: list[str]
    recommended_action: str | None