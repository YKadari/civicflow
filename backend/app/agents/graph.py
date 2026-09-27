from langgraph.graph import END, START, StateGraph

from app.agents.state import CaseAnalysisState
from app.ai.base import AIProvider
from app.ai.exceptions import AIProviderError
from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.services.analysis import (
    AI_CONFIDENCE_THRESHOLD,
    fallback_classify_intent,
)


def build_case_analysis_graph(
    ai_provider: AIProvider,
):
    graph = StateGraph(CaseAnalysisState)

    def load_context_node(
        state: CaseAnalysisState,
    ) -> dict:

        case_id = state["case_id"]
        event_id = state["event_id"]

        context = get_case_context(case_id)

        if context is None:
            return {
                "error": "Case not found",
            }

        request = get_case_request(
            case_id=case_id,
            event_id=event_id,
        )

        if request is None:
            return {
                "error": "Request not found",
            }

        return {
            "context": context,
            "description": request.description or "",
        }

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

    graph.add_node(
        "load_context",
        load_context_node,
    )

    graph.add_node(
        "classify_intent",
        classify_intent_node,
    )

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
        END,
    )

    return graph.compile()