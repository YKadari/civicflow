from app.database.repository import (
    get_case_context,
)
from app.tools.models import (
    PaymentCheckResult,
    PaymentRecord,
)


def check_payment(
    case_id: str,
) -> PaymentCheckResult:
    """
    Read-only CivicFlow tool.

    Retrieves payment information for a case.
    This function does not modify any database state.
    """

    context = get_case_context(
        case_id
    )

    if context is None:
        return PaymentCheckResult(
            success=False,
            case_id=case_id,
            payments=[],
            message="Case not found.",
        )

    payments = [
        PaymentRecord(
            payment_id=payment.payment_id,
            amount=payment.amount,
            scheduled_date=(
                payment.scheduled_date
            ),
            paid_date=payment.paid_date,
            status=payment.status,
        )
        for payment in context.payments
    ]

    if not payments:
        return PaymentCheckResult(
            success=True,
            case_id=case_id,
            payments=[],
            message=(
                "No payment records were found "
                "for this case."
            ),
        )

    return PaymentCheckResult(
        success=True,
        case_id=case_id,
        payments=payments,
        message=(
            f"Found {len(payments)} "
            "payment record(s)."
        ),
    )