from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayPolicyVersion:
    policy_id: str
    version: int
    title: str
    summary: str


HA_PAY_V1 = ReplayPolicyVersion(
    policy_id="HA-PAY",
    version=1,
    title="Housing Assistance Payment Policy v1",
    summary=(
        "An active case with a missing payment "
        "may be considered for a payment-status "
        "investigation."
    ),
)


HA_PAY_V2 = ReplayPolicyVersion(
    policy_id="HA-PAY",
    version=2,
    title="Housing Assistance Payment Policy v2",
    summary=(
        "An active case with a missing payment "
        "may be considered for a payment-status "
        "investigation only when address "
        "verification has been approved."
    ),
)


POLICY_VERSIONS = {
    ("HA-PAY", 1): HA_PAY_V1,
    ("HA-PAY", 2): HA_PAY_V2,
}


def get_policy_version(
    policy_id: str,
    version: int,
) -> ReplayPolicyVersion | None:

    return POLICY_VERSIONS.get(
        (
            policy_id,
            version,
        )
    )