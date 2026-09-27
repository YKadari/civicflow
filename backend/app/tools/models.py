from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class PaymentRecord:
    payment_id: str
    amount: Decimal
    scheduled_date: date
    paid_date: date | None
    status: str


@dataclass(frozen=True)
class PaymentCheckResult:
    success: bool
    case_id: str
    payments: list[PaymentRecord] = field(
        default_factory=list
    )
    message: str = ""