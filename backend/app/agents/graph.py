from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.agents.state import (
    CaseAnalysisState,
)
from app.ai.base import AIProvider
from app.ai.exceptions import (
    AIProviderError,
)
from app.approvals.service import (
    create_approval_request,
)
from app.database.repository import (
    get_case_context,
    get_case_request,
)
from app.domain.models import (
    ActionType,
)
from app.policies.base import (
    PolicyRetriever,
)
from app.policy_engine.engine import (
    evaluate_action,
)
from app.services.analysis import (
    AI_CONFIDENCE_THRESHOLD,
    fallback_classify_intent,
)
from app.tools.registry import (
    get_tool_definition,
)


def build_case_analysis_graph(
    ai_provider: AIProvider,
    policy_retriever: PolicyRetriever,
):
    graph = StateGraph(
        CaseAnalysisState
    )

    # ========================================================
    # Load
    # ========================================================

    def load_context_node(
        state: CaseAnalysisState,
    ) -> dict:

        context = get_case_context(
            state["case_id"]
        )

        if context is None:
            return {
                "error": "Case not found",
            }

        request = get_case_request(
            case_id=state["case_id"],
            event_id=state["event_id"],
        )

        if request is None:
            return {
                "error": "Request not found",
            }

        return {
            "context": context,
            "description": (
                request.description or ""
            ),
        }

    # ========================================================
    # Classification
    # ========================================================

    def classify_intent_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        description = state.get(
            "description"
        )

        if description is None:
            return {
                "error": (
                    "Request description is missing"
                ),
                "requires_human_review": True,
            }

        try:
            classification = (
                ai_provider
                .classify_intent(
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

    # ========================================================
    # Policy retrieval
    # ========================================================

    def retrieve_policy_node(
        state: CaseAnalysisState,
    ) -> dict:

        if state.get("error"):
            return {}

        description = state.get(
            "description"
        )

        request_type = state.get(
            "request_type"
        )

        if (
            description is None
            or request_type is None
        ):
            return {
                "error": (
                    "Analysis state is incomplete."
                ),
                "requires_human_review": True,
            }

        policy_query = (
            f"Citizen request: "
            f"{description}\n"
            f"Request type: "
            f"{request_type}"
        )

        evidence = (
            policy_retriever.retrieve(
                query=policy_query,
                limit=3,
            )
        )

        return {
            "policy_evidence": evidence,
            "requires_human_review": (
                not bool(evidence)
            ),
        }

    # ========================================================
    # Facts
    # ========================================================

    def build_facts_node(
        state: CaseAnalysisState,
    ) -> dict:

        context = state["context"]

        request_type = state[
            "request_type"
        ]

        facts = [
            (
                f"Case status is "
                f"{context.case.status.value}"
            )
        ]

        if request_type == "payment_issue":
            for payment in context.payments:
                facts.append(
                    (
                        f"Payment "
                        f"{payment.payment_id} "
                        f"is marked "
                        f"{payment.status}"
                    )
                )

                facts.append(
                    (
                        f"Payment "
                        f"{payment.payment_id} "
                        f"was scheduled for "
                        f"{payment.scheduled_date}"
                    )
                )

        elif request_type == "document_issue":
            for document in context.documents:
                facts.append(
                    (
                        f"Document "
                        f"{document.document_type} "
                        f"is "
                        f"{document.review_status}"
                    )
                )

        for document in context.documents:
            fact = (
                f"Document "
                f"{document.document_type} "
                f"is "
                f"{document.review_status}"
            )

            if fact not in facts:
                facts.append(
                    fact
                )

        return {
            "facts": facts,
        }

    # ========================================================
    # Recommendation
    # ========================================================

    def recommend_action_node(
        state: CaseAnalysisState,
    ) -> dict:

        policy_payload = [
            {
                "chunk_id": (
                    evidence.chunk_id
                ),
                "policy_id": (
                    evidence.policy_id
                ),
                "section": (
                    evidence.section
                ),
                "content": (
                    evidence.content
                ),
            }
            for evidence
            in state.get(
                "policy_evidence",
                [],
            )
        ]

        try:
            recommendation = (
                ai_provider
                .recommend_action(
                    case_id=state[
                        "case_id"
                    ],
                    request_description=(
                        state[
                            "description"
                        ]
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
                recommendation
                .recommended_action
            ),
            "recommendation_rationale": (
                recommendation.rationale
            ),
            "recommendation_confidence": (
                recommendation.confidence
            ),
            "cited_policy_chunks": list(
                recommendation
                .cited_chunk_ids
            ),
        }

    # ========================================================
    # Recommendation validation
    # ========================================================

    def validate_recommendation_node(
        state: CaseAnalysisState,
    ) -> dict:

        valid_chunk_ids = {
            evidence.chunk_id
            for evidence
            in state.get(
                "policy_evidence",
                [],
            )
        }

        cited_chunks = state.get(
            "cited_policy_chunks",
            [],
        )

        invalid_citations = [
            chunk_id
            for chunk_id in cited_chunks
            if chunk_id
            not in valid_chunk_ids
        ]

        if invalid_citations:
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

        recommendation = state.get(
            "recommended_action"
        )

        if (
            recommendation is None
            or recommendation == "none"
        ):
            return {
                "recommended_action": None,
                "requires_human_review": True,
            }

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
            "recommended_action": (
                action.value
            ),
            "requires_human_review": False,
        }

    # ========================================================
    # Deterministic policy check
    # ========================================================

    def deterministic_policy_check_node(
        state: CaseAnalysisState,
    ) -> dict:

        action_value = state.get(
            "recommended_action"
        )

        if action_value is None:
            return {
                "policy_check_allowed": False,
                "policy_check_reasons": [
                    (
                        "No valid action was "
                        "available for policy "
                        "evaluation."
                    )
                ],
                "requires_human_review": True,
            }

        action = ActionType(
            action_value
        )

        result = evaluate_action(
            action=action,
            context=state["context"],
            policy_evidence=state.get(
                "policy_evidence",
                [],
            ),
        )

        if not result.allowed:
            return {
                "policy_check_allowed": False,
                "policy_check_reasons": (
                    result.reasons
                ),
                "recommended_action": None,
                "requires_human_review": True,
            }

        return {
            "policy_check_allowed": True,
            "policy_check_reasons": (
                result.reasons
            ),
            "requires_human_review": False,
        }

    # ========================================================
    # Decision Challenge
    # ========================================================

    def decision_challenge_node(
        state: CaseAnalysisState,
    ) -> dict:

        action_value = state.get(
            "recommended_action"
        )

        if action_value is None:
            return {
                "decision_challenge_passed": False,
                "challenge_verdict": "challenge",
                "challenge_reasons": [
                    (
                        "No proposed action was "
                        "available for challenge."
                    )
                ],
                "challenge_cited_policy_chunks": [],
                "challenge_missing_evidence": [],
                "challenged_action": None,
                "requires_human_review": True,
            }

        policy_payload = [
            {
                "chunk_id": (
                    evidence.chunk_id
                ),
                "policy_id": (
                    evidence.policy_id
                ),
                "section": (
                    evidence.section
                ),
                "content": (
                    evidence.content
                ),
            }
            for evidence
            in state.get(
                "policy_evidence",
                [],
            )
        ]

        try:
            challenge = (
                ai_provider
                .challenge_decision(
                    case_id=state[
                        "case_id"
                    ],
                    proposed_action=(
                        action_value
                    ),
                    facts=state[
                        "facts"
                    ],
                    policy_evidence=(
                        policy_payload
                    ),
                )
            )

        except AIProviderError:
            return {
                "decision_challenge_passed": False,
                "challenge_verdict": "challenge",
                "challenge_reasons": [
                    (
                        "Decision Challenge could "
                        "not be completed reliably."
                    )
                ],
                "challenge_cited_policy_chunks": [],
                "challenge_missing_evidence": [],
                "challenged_action": (
                    action_value
                ),
                "requires_human_review": True,
            }

        valid_chunk_ids = {
            evidence.chunk_id
            for evidence
            in state.get(
                "policy_evidence",
                [],
            )
        }

        invalid_citations = [
            chunk_id
            for chunk_id
            in challenge.cited_chunk_ids
            if chunk_id
            not in valid_chunk_ids
        ]

        if invalid_citations:
            return {
                "decision_challenge_passed": False,
                "challenge_verdict": "challenge",
                "challenge_reasons": [
                    (
                        "The Decision Challenge "
                        "cited policy evidence that "
                        "was not retrieved."
                    )
                ],
                "challenge_confidence": (
                    challenge.confidence
                ),
                "challenge_cited_policy_chunks": (
                    list(
                        challenge
                        .cited_chunk_ids
                    )
                ),
                "challenge_missing_evidence": (
                    list(
                        challenge
                        .missing_evidence
                    )
                ),
                "challenged_action": (
                    action_value
                ),
                "requires_human_review": True,
            }

        if (
            challenge.verdict
            == "challenge"
        ):
            return {
                "decision_challenge_passed": False,
                "challenge_verdict": (
                    challenge.verdict
                ),
                "challenge_reasons": list(
                    challenge.reasons
                ),
                "challenge_confidence": (
                    challenge.confidence
                ),
                "challenge_cited_policy_chunks": (
                    list(
                        challenge
                        .cited_chunk_ids
                    )
                ),
                "challenge_missing_evidence": (
                    list(
                        challenge
                        .missing_evidence
                    )
                ),
                "challenged_action": (
                    action_value
                ),
                "requires_human_review": True,
            }

        return {
            "decision_challenge_passed": True,
            "challenge_verdict": (
                challenge.verdict
            ),
            "challenge_reasons": list(
                challenge.reasons
            ),
            "challenge_confidence": (
                challenge.confidence
            ),
            "challenge_cited_policy_chunks": (
                list(
                    challenge
                    .cited_chunk_ids
                )
            ),
            "challenge_missing_evidence": (
                list(
                    challenge
                    .missing_evidence
                )
            ),
            "challenged_action": (
                action_value
            ),
            "requires_human_review": False,
        }

    # ========================================================
    # Tool gate / execution
    # ========================================================

    def execute_tool_node(
        state: CaseAnalysisState,
    ) -> dict:

        action_value = state.get(
            "recommended_action"
        )

        if action_value is None:
            return {
                "executed_tool": None,
                "requires_human_review": True,
            }

        action = ActionType(
            action_value
        )

        tool = get_tool_definition(
            action
        )

        if tool is None:
            return {
                "executed_tool": None,
                "requires_human_review": True,
            }

        if tool.requires_approval:
            approval = (
                create_approval_request(
                    case_id=state[
                        "case_id"
                    ],
                    action_type=(
                        action.value
                    ),
                )
            )

            return {
                "tool_access_mode": (
                    tool.access_mode
                ),
                "tool_requires_approval": True,
                "approval_request": (
                    approval
                ),
                "executed_tool": None,
                "requires_human_review": True,
            }

        if tool.handler is None:
            return {
                "tool_access_mode": (
                    tool.access_mode
                ),
                "tool_requires_approval": (
                    tool.requires_approval
                ),
                "executed_tool": None,
                "requires_human_review": True,
            }

        if action == ActionType.CHECK_PAYMENT:
            result = tool.handler(
                state["case_id"]
            )

            return {
                "tool_access_mode": (
                    tool.access_mode
                ),
                "tool_requires_approval": False,
                "executed_tool": (
                    tool.name
                ),
                "payment_check_result": (
                    result
                ),
                "requires_human_review": (
                    not result.success
                ),
            }

        return {
            "executed_tool": None,
            "requires_human_review": True,
        }

    # ========================================================
    # Human review
    # ========================================================

    def human_review_node(
        state: CaseAnalysisState,
    ) -> dict:

        return {
            "recommended_action": None,
            "requires_human_review": True,
        }

    # ========================================================
    # Routing
    # ========================================================

    def route_after_load(
        state: CaseAnalysisState,
    ) -> str:

        if state.get("error"):
            return "end"

        return "classify"

    def route_after_classification(
        state: CaseAnalysisState,
    ) -> str:

        if state.get("error"):
            return "end"

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "retrieve_policy"

    def route_after_policy(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "build_facts"

    def route_after_recommendation(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "validate"

    def route_after_validation(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "policy_check"

    def route_after_policy_check(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        action_value = state.get(
            "recommended_action"
        )

        if action_value is None:
            return "human_review"

        try:
            action = ActionType(
                action_value
            )

        except ValueError:
            return "human_review"

        tool = get_tool_definition(
            action
        )

        if tool is None:
            return "human_review"

        if tool.requires_approval:
            return "challenge"

        return "execute_tool"

    def route_after_challenge(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "execute_tool"

    def route_after_tool(
        state: CaseAnalysisState,
    ) -> str:

        if state.get(
            "requires_human_review",
            False,
        ):
            return "human_review"

        return "end"

    # ========================================================
    # Nodes
    # ========================================================

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

    graph.add_node(
        "deterministic_policy_check",
        deterministic_policy_check_node,
    )

    graph.add_node(
        "decision_challenge",
        decision_challenge_node,
    )

    graph.add_node(
        "execute_tool",
        execute_tool_node,
    )

    graph.add_node(
        "human_review",
        human_review_node,
    )

    # ========================================================
    # Edges
    # ========================================================

    graph.add_edge(
        START,
        "load_context",
    )

    graph.add_conditional_edges(
        "load_context",
        route_after_load,
        {
            "classify": (
                "classify_intent"
            ),
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {
            "human_review": (
                "human_review"
            ),
            "retrieve_policy": (
                "retrieve_policy"
            ),
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "retrieve_policy",
        route_after_policy,
        {
            "human_review": (
                "human_review"
            ),
            "build_facts": (
                "build_facts"
            ),
        },
    )

    graph.add_edge(
        "build_facts",
        "recommend_action",
    )

    graph.add_conditional_edges(
        "recommend_action",
        route_after_recommendation,
        {
            "human_review": (
                "human_review"
            ),
            "validate": (
                "validate_recommendation"
            ),
        },
    )

    graph.add_conditional_edges(
        "validate_recommendation",
        route_after_validation,
        {
            "human_review": (
                "human_review"
            ),
            "policy_check": (
                "deterministic_policy_check"
            ),
        },
    )

    graph.add_conditional_edges(
        "deterministic_policy_check",
        route_after_policy_check,
        {
            "human_review": (
                "human_review"
            ),
            "challenge": (
                "decision_challenge"
            ),
            "execute_tool": (
                "execute_tool"
            ),
        },
    )

    graph.add_conditional_edges(
        "decision_challenge",
        route_after_challenge,
        {
            "human_review": (
                "human_review"
            ),
            "execute_tool": (
                "execute_tool"
            ),
        },
    )

    graph.add_conditional_edges(
        "execute_tool",
        route_after_tool,
        {
            "human_review": (
                "human_review"
            ),
            "end": END,
        },
    )

    graph.add_edge(
        "human_review",
        END,
    )

    return graph.compile()