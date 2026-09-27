from langgraph.graph import END, START, StateGraph

from app.agents.state import CaseAnalysisState
from app.ai.base import AIProvider
from app.ai.exceptions import AIProviderError
from app.database.repository import (
    get_case_context,
    get_case_request,
)
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

        # No policy evidence means CivicFlow should
        # not continue toward an automated action.
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

        # Document state may matter even when the
        # citizen's primary request is not about documents.
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
        END,
    )

    return graph.compile()