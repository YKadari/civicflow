from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.domain.models import (
    ActionType,
    CaseAnalysis,
)


def analyze_case_request(
    case_id: str,
    event_id: str,
) -> CaseAnalysis | None:

    context = get_case_context(case_id)

    if context is None:
        return None

    request = get_case_request(
        case_id=case_id,
        event_id=event_id,
    )

    if request is None:
        return None

    description = (request.description or "").lower()

    facts = [
        f"Case status is {context.case.status.value}"
    ]

    request_type = "general_inquiry"
    recommended_action = None

    if (
        "payment" in description
        or "paid" in description
        or "money" in description
    ):
        request_type = "payment_issue"

        for payment in context.payments:
            facts.append(
                f"Payment {payment.payment_id} "
                f"is marked {payment.status}"
            )

        recommended_action = ActionType.CHECK_PAYMENT

    elif (
        "document" in description
        or "verification" in description
    ):
        request_type = "document_issue"

        for document in context.documents:
            facts.append(
                f"Document {document.document_type} "
                f"is {document.review_status}"
            )

        recommended_action = ActionType.REQUEST_DOCUMENT

    elif (
        "address" in description
        or "phone" in description
        or "email" in description
    ):
        request_type = "contact_update"

        recommended_action = ActionType.UPDATE_CONTACT_INFO

    for document in context.documents:
        fact = (
            f"Document {document.document_type} "
            f"is {document.review_status}"
        )

        if fact not in facts:
            facts.append(fact)

    return CaseAnalysis(
        case_id=case_id,
        request_type=request_type,
        facts=facts,
        recommended_action=recommended_action,
    )