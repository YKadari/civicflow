from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.domain.models import (
    ActionType,
    CaseAnalysis,
)
from app.ai.base import AIProvider

import os
from app.ai.exceptions import AIProviderError
from app.ai.models import IntentClassification


AI_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "AI_CONFIDENCE_THRESHOLD",
        "0.70",
    )
)


def fallback_classify_intent(
    description: str,
) -> IntentClassification:

    text = description.lower()

    if (
        "payment" in text
        or "paid" in text
        or "money" in text
    ):
        request_type = "payment_issue"

    elif (
        "document" in text
        or "verification" in text
    ):
        request_type = "document_issue"

    elif (
        "address" in text
        or "phone" in text
        or "email" in text
    ):
        request_type = "contact_update"

    else:
        request_type = "general_inquiry"

    return IntentClassification(
        request_type=request_type,
        confidence=0.40,
    )
def analyze_case_request(
    case_id: str,
    event_id: str,
    ai_provider: AIProvider,
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

    description = request.description or ""

    try:
        classification = ai_provider.classify_intent(
            description
        )
        classification_source = "ai"

    except AIProviderError:
        classification = fallback_classify_intent(
            description
        )
        classification_source = "fallback"

    request_type = classification.request_type

    requires_human_review = (
        classification_source == "fallback"
        or classification.confidence
        < AI_CONFIDENCE_THRESHOLD
    )

    facts = [
        f"Case status is {context.case.status.value}"
    ]

    recommended_action = None

    if request_type == "payment_issue":
        for payment in context.payments:
            facts.append(
                f"Payment {payment.payment_id} "
                f"is marked {payment.status}"
            )

        recommended_action = ActionType.CHECK_PAYMENT

    elif request_type == "document_issue":
        for document in context.documents:
            facts.append(
                f"Document {document.document_type} "
                f"is {document.review_status}"
            )

        recommended_action = ActionType.REQUEST_DOCUMENT

    elif request_type == "contact_update":
        recommended_action = (
            ActionType.UPDATE_CONTACT_INFO
        )

    for document in context.documents:
        fact = (
            f"Document {document.document_type} "
            f"is {document.review_status}"
        )

        if fact not in facts:
            facts.append(fact)

    # IMPORTANT: this must happen AFTER action selection
    if requires_human_review:
        recommended_action = None

    return CaseAnalysis(
        case_id=case_id,
        request_type=request_type,
        facts=facts,
        recommended_action=recommended_action,
        classification_confidence=(
            classification.confidence
        ),
        classification_source=classification_source,
        requires_human_review=requires_human_review,
    )