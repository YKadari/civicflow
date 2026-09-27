import os

from dotenv import load_dotenv

from app.ai.base import AIProvider
from app.ai.exceptions import AIProviderError
from app.ai.models import IntentClassification
from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.domain.models import (
    ActionType,
    CaseAnalysis,
)
from app.policies.base import PolicyRetriever


load_dotenv()


AI_CONFIDENCE_THRESHOLD = float(
    os.getenv(
        "AI_CONFIDENCE_THRESHOLD",
        "0.70",
    )
)


def fallback_classify_intent(
    description: str,
) -> IntentClassification:
    """
    Deterministic backup classifier used when the AI provider
    is unavailable or fails.
    """

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
    policy_retriever: PolicyRetriever,
) -> CaseAnalysis | None:

    # ---------------------------------------------------------
    # 1. Load the complete case context
    # ---------------------------------------------------------

    context = get_case_context(case_id)

    if context is None:
        return None

    # ---------------------------------------------------------
    # 2. Load the citizen request
    # ---------------------------------------------------------

    request = get_case_request(
        case_id=case_id,
        event_id=event_id,
    )

    if request is None:
        return None

    description = request.description or ""

    # ---------------------------------------------------------
    # 3. Classify the citizen request
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 4. Decide whether classification itself requires review
    # ---------------------------------------------------------

    requires_human_review = (
        classification_source == "fallback"
        or classification.confidence
        < AI_CONFIDENCE_THRESHOLD
    )

    # ---------------------------------------------------------
    # 5. Retrieve relevant policy evidence
    # ---------------------------------------------------------

    policy_query = (
        f"Citizen request: {description}\n"
        f"Request type: {request_type}"
    )

    policy_evidence = policy_retriever.retrieve(
        query=policy_query,
        limit=3,
    )

    # We do not want CivicFlow recommending consequential
    # actions without supporting policy.
    if not policy_evidence:
        requires_human_review = True

    # ---------------------------------------------------------
    # 6. Build case facts
    # ---------------------------------------------------------

    facts = [
        f"Case status is {context.case.status.value}"
    ]

    if request_type == "payment_issue":
        for payment in context.payments:
            facts.append(
                f"Payment {payment.payment_id} "
                f"is marked {payment.status}"
            )

    elif request_type == "document_issue":
        for document in context.documents:
            facts.append(
                f"Document {document.document_type} "
                f"is {document.review_status}"
            )

    # Include document state because it can be important even
    # for payment and other requests.
    for document in context.documents:
        fact = (
            f"Document {document.document_type} "
            f"is {document.review_status}"
        )

        if fact not in facts:
            facts.append(fact)

    # ---------------------------------------------------------
    # 7. Prepare policy evidence for the LLM
    # ---------------------------------------------------------

    policy_payload = [
        {
            "chunk_id": evidence.chunk_id,
            "policy_id": evidence.policy_id,
            "section": evidence.section,
            "content": evidence.content,
        }
        for evidence in policy_evidence
    ]

    valid_chunk_ids = {
        evidence.chunk_id
        for evidence in policy_evidence
    }

    # ---------------------------------------------------------
    # 8. Initialize recommendation fields
    # ---------------------------------------------------------

    recommended_action = None
    recommendation_rationale = None
    recommendation_confidence = None
    cited_policy_chunks = []

    # ---------------------------------------------------------
    # 9. Ask AI for a grounded recommendation
    # ---------------------------------------------------------

    if policy_evidence and not requires_human_review:
        try:
            recommendation = ai_provider.recommend_action(
                case_id=case_id,
                request_description=description,
                facts=facts,
                policy_evidence=policy_payload,
            )

            recommendation_rationale = (
                recommendation.rationale
            )

            recommendation_confidence = (
                recommendation.confidence
            )

            cited_policy_chunks = list(
                recommendation.cited_chunk_ids
            )

            # -------------------------------------------------
            # 10. Verify the model did not invent citations
            # -------------------------------------------------

            invalid_citations = [
                chunk_id
                for chunk_id
                in recommendation.cited_chunk_ids
                if chunk_id not in valid_chunk_ids
            ]

            if invalid_citations:
                requires_human_review = True

            # -------------------------------------------------
            # 11. Convert the model's action into our ActionType
            # -------------------------------------------------

            if (
                recommendation.recommended_action
                != "none"
            ):
                try:
                    recommended_action = ActionType(
                        recommendation.recommended_action
                    )

                except ValueError:
                    requires_human_review = True

        except AIProviderError:
            requires_human_review = True

    # ---------------------------------------------------------
    # 12. Human review always overrides automated recommendation
    # ---------------------------------------------------------

    if requires_human_review:
        recommended_action = None

    # ---------------------------------------------------------
    # 13. Return the completed analysis
    # ---------------------------------------------------------

    return CaseAnalysis(
        case_id=case_id,
        request_type=request_type,
        facts=facts,
        recommended_action=recommended_action,
        classification_confidence=(
            classification.confidence
        ),
        classification_source=(
            classification_source
        ),
        requires_human_review=(
            requires_human_review
        ),
        policy_evidence=policy_evidence,
        recommendation_rationale=(
            recommendation_rationale
        ),
        recommendation_confidence=(
            recommendation_confidence
        ),
        cited_policy_chunks=(
            cited_policy_chunks
        ),
    )