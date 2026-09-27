from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.factory import get_ai_provider
from app.policies.factory import (
    get_policy_retriever,
)


def main():
    ai_provider = get_ai_provider()
    policy_retriever = (
        get_policy_retriever()
    )

    graph = build_case_analysis_graph(
        ai_provider=ai_provider,
        policy_retriever=policy_retriever,
    )

    result = graph.invoke(
        {
            "case_id": "CF-10001",
            "event_id": "EVT-10001-1",
        }
    )

    print()
    print("Case:")
    print(result["case_id"])

    print()
    print("Description:")
    print(result["description"])

    print()
    print("Request Type:")
    print(result["request_type"])

    print()
    print("Classification Confidence:")
    print(
        result[
            "classification_confidence"
        ]
    )

    print()
    print("Facts:")

    for fact in result["facts"]:
        print(f"- {fact}")

    print()
    print("Policy Evidence:")

    for evidence in result[
        "policy_evidence"
    ]:
        print(
            f"- {evidence.policy_id} "
            f"{evidence.section} "
            f"({evidence.similarity:.3f})"
        )

    print()
    print("Human Review:")
    print(
        result[
            "requires_human_review"
        ]
    )


if __name__ == "__main__":
    main()