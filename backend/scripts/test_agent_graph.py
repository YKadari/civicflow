from app.agents.graph import (
    build_case_analysis_graph,
)
from app.ai.factory import get_ai_provider


def main():
    ai_provider = get_ai_provider()

    graph = build_case_analysis_graph(
        ai_provider=ai_provider,
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
    print("Confidence:")
    print(
        result[
            "classification_confidence"
        ]
    )

    print()
    print("Source:")
    print(
        result[
            "classification_source"
        ]
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