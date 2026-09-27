from datetime import date

from app.policies.loader import load_policy


def main():
    policy = load_policy(
        file_name="housing_payments_v1.md",
        policy_id="HA-PAY",
        title="Housing Assistance Payment Policy",
        version=1,
        effective_date=date(2026, 1, 1),
    )

    print("Policy ID:")
    print(policy.policy_id)

    print()
    print("Title:")
    print(policy.title)

    print()
    print("Version:")
    print(policy.version)

    print()
    print("Content:")
    print(policy.content)


if __name__ == "__main__":
    main()