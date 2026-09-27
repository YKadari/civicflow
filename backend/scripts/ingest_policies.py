from datetime import date

from app.policies.ingestion import ingest_policy
from app.policies.loader import load_policy


POLICIES = [
    {
        "file_name": "housing_payments_v1.md",
        "policy_id": "HA-PAY",
        "title": "Housing Assistance Payment Policy",
    },
    {
        "file_name": "verification_v1.md",
        "policy_id": "HA-VER",
        "title": "Housing Assistance Verification Policy",
    },
    {
        "file_name": "contact_information_v1.md",
        "policy_id": "HA-CONTACT",
        "title": "Contact Information Update Policy",
    },
]


def main():
    total_chunks = 0

    for policy_config in POLICIES:
        policy = load_policy(
            file_name=policy_config["file_name"],
            policy_id=policy_config["policy_id"],
            title=policy_config["title"],
            version=1,
            effective_date=date(2026, 1, 1),
        )

        count = ingest_policy(policy)

        total_chunks += count

        print(
            f"{policy.policy_id}: "
            f"{count} chunks indexed"
        )

    print()
    print(
        f"Total policy chunks indexed: "
        f"{total_chunks}"
    )


if __name__ == "__main__":
    main()