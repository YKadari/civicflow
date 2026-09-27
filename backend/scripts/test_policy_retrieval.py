from app.policies.retrieval import retrieve_policy


def run_query(query: str):
    print()
    print("=" * 70)
    print("QUERY:")
    print(query)

    results = retrieve_policy(
        query=query,
        limit=3,
    )

    for index, result in enumerate(
        results,
        start=1,
    ):
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
    queries = [
        (
            "The $850 I expected at the beginning "
            "of the month never showed up."
        ),

        (
            "I uploaded my income verification, "
            "but nobody has reviewed it yet."
        ),

        (
            "I moved and need to change "
            "my mailing address."
        ),

        (
            "Can my case be closed even though "
            "I only received the notice eight days ago?"
        ),
    ]

    for query in queries:
        run_query(query)


if __name__ == "__main__":
    main()