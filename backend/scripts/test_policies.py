from datetime import date

from app.policies.loader import load_policy


def test_load_payment_policy():
    policy = load_policy(
        file_name="housing_payments_v1.md",
        policy_id="HA-PAY",
        title="Housing Assistance Payment Policy",
        version=1,
        effective_date=date(2026, 1, 1),
    )

    assert policy.policy_id == "HA-PAY"
    assert policy.version == 1

    assert (
        "five business days"
        in policy.content
    )

    assert (
        "payment-status investigation"
        in policy.content
    )