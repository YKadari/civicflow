from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReplayPolicyOutcome:
    policy_id: str
    version: int
    allowed: bool
    requires_human_review: bool
    reasons: list[str] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class PolicyReplayResult:
    case_id: str
    action: str
    policy_id: str

    baseline: ReplayPolicyOutcome
    candidate: ReplayPolicyOutcome

    outcome_changed: bool
    change_type: str


@dataclass(frozen=True)
class PolicyReplayBatchResult:
    action: str
    policy_id: str

    baseline_version: int
    candidate_version: int

    total_cases: int
    changed_cases: int
    unchanged_cases: int

    results: list[PolicyReplayResult] = field(
        default_factory=list
    )