from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.factory import (
    get_ai_provider,
)
from app.policies.factory import (
    get_policy_retriever,
)


def main():
    graph = build_case_analysis_graph(
        ai_provider=(
            get_ai_provider()
        ),
        policy_retriever=(
            get_policy_retriever()
        ),
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    print()
    print("REQUEST TYPE")
    print(
        result.get(
            "request_type"
        )
    )

    print()
    print("RECOMMENDED ACTION")
    print(
        result.get(
            "recommended_action"
        )
    )

    print()
    print("POLICY CHECK")
    print(
        result.get(
            "policy_check_allowed"
        )
    )

    print()
    print("DECISION CHALLENGE")
    print(
        result.get(
            "challenge_verdict"
        )
    )

    print()
    print("CHALLENGE REASONS")

    for reason in result.get(
        "challenge_reasons",
        [],
    ):
        print(
            f"- {reason}"
        )

    print()
    print("MISSING EVIDENCE")

    for item in result.get(
        "challenge_missing_evidence",
        [],
    ):
        print(
            f"- {item}"
        )

    print()
    print("APPROVAL")

    approval = result.get(
        "approval_request"
    )

    if approval is None:
        print("None")
    else:
        print(
            approval.approval_id
        )
        print(
            approval.status
        )

    print()
    print("EXECUTED TOOL")
    print(
        result.get(
            "executed_tool"
        )
    )

    print()
    print("HUMAN REVIEW")
    print(
        result.get(
            "requires_human_review"
        )
    )


if __name__ == "__main__":
    main()