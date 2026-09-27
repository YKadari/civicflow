from datetime import date

from app.policies.chunking import chunk_policy
from app.policies.loader import load_policy


def main():
    policy = load_policy(
        file_name="housing_payments_v1.md",
        policy_id="HA-PAY",
        title="Housing Assistance Payment Policy",
        version=1,
        effective_date=date(2026, 1, 1),
    )

    chunks = chunk_policy(policy)

    for chunk in chunks:
        print()
        print("Chunk ID:")
        print(chunk.chunk_id)

        print("Section:")
        print(chunk.section)

        print("Content:")
        print(chunk.content)


if __name__ == "__main__":
    main()