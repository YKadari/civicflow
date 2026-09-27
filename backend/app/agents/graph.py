from langgraph.graph import END, START, StateGraph

from app.agents.state import CaseAnalysisState
from app.ai.base import AIProvider
from app.ai.exceptions import AIProviderError
from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.domain.models import ActionType
from app.policies.base import PolicyRetriever
from app.services.analysis import (
    AI_CONFIDENCE_THRESHOLD,
    fallback_classify_intent,
)


def build_case_analysis_graph(
    ai_provider: AIProvider,
    policy_retriever: PolicyRetriever,
):
    graph = StateGraph(CaseAnalysisState)

    # ---------------------------------------------------------
    # Node 1: Load case + citizen request
    # ---------------------------------------------------------

    def load_context_node(
        state: CaseAnalysisState,
    ) -> dict:

        case_id = state["case_id"]
        event_id = state["event_id"]

        context = get_case_context(case_id)

        if context is None:
            return {
                "error": "Case not found",
                "requires_human_review": True,
            }

        request = get_case_request(
            case_id=case_id,
            event_id=event_id,
        )

        if request is None:
            return {
                "error": "Request not found",
                "requires_human_review": True,
            }

        return {
            "context": context,
            "description": request.description or "",
        }

    # ---------------------------------------------------------
    # Node 2: Classify intent
    # ---------------------------------------------------------

    def classify_intent_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        description = state["description"]

        try:
            classification = (
                ai_provider.classify_intent(
                    description
                )
            )

            source = "ai"

        except AIProviderError:
            classification = (
                fallback_classify_intent(
                    description
                )
            )

            source = "fallback"

        requires_review = (
            source == "fallback"
            or classification.confidence
            < AI_CONFIDENCE_THRESHOLD
        )

        return {
            "request_type": (
                classification.request_type
            ),
            "classification_confidence": (
                classification.confidence
            ),
            "classification_source": source,
            "requires_human_review": (
                requires_review
            ),
        }

    # ---------------------------------------------------------
    # Node 3: Retrieve relevant policy
    # ---------------------------------------------------------

    def retrieve_policy_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        description = state["description"]
        request_type = state["request_type"]

        policy_query = (
            f"Citizen request: {description}\n"
            f"Request type: {request_type}"
        )

        evidence = policy_retriever.retrieve(
            query=policy_query,
            limit=3,
        )

        result = {
            "policy_evidence": evidence,
        }

        if not evidence:
            result["requires_human_review"] = True

        return result

    # ---------------------------------------------------------
    # Node 4: Build structured case facts
    # ---------------------------------------------------------

    def build_facts_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        context = state["context"]
        request_type = state["request_type"]

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

        for document in context.documents:
            fact = (
                f"Document {document.document_type} "
                f"is {document.review_status}"
            )

            if fact not in facts:
                facts.append(fact)

        return {
            "facts": facts,
        }

    # ---------------------------------------------------------
    # Node 5: Ask AI for a grounded recommendation
    # ---------------------------------------------------------

    def recommend_action_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        # If an earlier step already decided that a human
        # must review the case, do not ask the AI to propose
        # an automated action.
        if state.get(
            "requires_human_review",
            False,
        ):
            return {
                "recommended_action": None,
            }

        policy_evidence = state.get(
            "policy_evidence",
            [],
        )

        if not policy_evidence:
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        policy_payload = [
            {
                "chunk_id": evidence.chunk_id,
                "policy_id": evidence.policy_id,
                "section": evidence.section,
                "content": evidence.content,
            }
            for evidence in policy_evidence
        ]

        try:
            recommendation = (
                ai_provider.recommend_action(
                    case_id=state["case_id"],
                    request_description=(
                        state["description"]
                    ),
                    facts=state["facts"],
                    policy_evidence=(
                        policy_payload
                    ),
                )
            )

        except AIProviderError:
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        return {
            "recommended_action": (
                recommendation.recommended_action
            ),
            "recommendation_rationale": (
                recommendation.rationale
            ),
            "recommendation_confidence": (
                recommendation.confidence
            ),
            "cited_policy_chunks": list(
                recommendation.cited_chunk_ids
            ),
        }

    # ---------------------------------------------------------
    # Node 6: Validate recommendation
    # ---------------------------------------------------------

    def validate_recommendation_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        if state.get(
            "requires_human_review",
            False,
        ):
            return {
                "recommended_action": None,
            }

        policy_evidence = state.get(
            "policy_evidence",
            [],
        )

        cited_chunks = state.get(
            "cited_policy_chunks",
            [],
        )

        valid_chunk_ids = {
            evidence.chunk_id
            for evidence in policy_evidence
        }

        # Check that every citation actually came from
        # the retrieved policy evidence.
        invalid_citations = [
            chunk_id
            for chunk_id in cited_chunks
            if chunk_id not in valid_chunk_ids
        ]

        if invalid_citations:
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        recommendation = state.get(
            "recommended_action"
        )

        if recommendation is None:
            return {
                "requires_human_review": True,
            }

        # "none" is a valid AI response meaning:
        # there is not enough evidence for an action.
        if recommendation == "none":
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        # Ensure the recommendation maps to an actual
        # CivicFlow ActionType.
        try:
            action = ActionType(
                recommendation
            )

        except ValueError:
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        return {
            "recommended_action": action.value,
        }

    # ---------------------------------------------------------
    # Register nodes
    # ---------------------------------------------------------

    graph.add_node(
        "load_context",
        load_context_node,
    )

    graph.add_node(
        "classify_intent",
        classify_intent_node,
    )

    graph.add_node(
        "retrieve_policy",
        retrieve_policy_node,
    )

    graph.add_node(
        "build_facts",
        build_facts_node,
    )

    graph.add_node(
        "recommend_action",
        recommend_action_node,
    )

    graph.add_node(
        "validate_recommendation",
        validate_recommendation_node,
    )

    # ---------------------------------------------------------
    # Connect graph
    # ---------------------------------------------------------

    graph.add_edge(
        START,
        "load_context",
    )

    graph.add_edge(
        "load_context",
        "classify_intent",
    )

    graph.add_edge(
        "classify_intent",
        "retrieve_policy",
    )

    graph.add_edge(
        "retrieve_policy",
        "build_facts",
    )

    graph.add_edge(
        "build_facts",
        "recommend_action",
    )

    graph.add_edge(
        "recommend_action",
        "validate_recommendation",
    )

    graph.add_edge(
        "validate_recommendation",
        END,
    )

    return graph.compile()