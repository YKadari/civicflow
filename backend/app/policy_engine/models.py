from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolicyCheckResult:
    allowed: bool
    requires_human_review: bool
    reasons: list[str] = field(
        default_factory=list
    )