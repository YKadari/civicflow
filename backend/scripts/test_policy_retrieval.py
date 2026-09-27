from app.policies.retrieval import PgVectorPolicyRetriever


def run_query(
    retriever: PgVectorPolicyRetriever,
    query: str,
):
    print()
    print("=" * 70)
    print("QUERY:")
    print(query)

    results = retriever.retrieve(
        query=query,
        limit=3,
    )

    if not results:
        print()
        print("No relevant policy found.")
        return

    for index, result in enumerate(results, start=1):
        print()
        print(f"RESULT {index}")

        print("Policy:")
        print(result.policy_id)

        print("Section:")
        print(result.section)

        print("Similarity:")
        print(round(result.similarity, 4))

        print("Content:")
        print(result.content)


def main():
    retriever = PgVectorPolicyRetriever()

    queries = [
        "The $850 I expected at the beginning of the month never showed up.",
        "I uploaded my income verification, but nobody has reviewed it yet.",
        "I moved and need to change my mailing address.",
        "Can my case be closed even though I only received the notice eight days ago?",
        "What is the weather tomorrow?",
    ]

    for query in queries:
        run_query(
            retriever,
            query,
        )


if __name__ == "__main__":
    main()