from dataclasses import (
    dataclass,
    field,
)


@dataclass(frozen=True)
class EvaluationMetric:
    name: str

    passed: int
    total: int

    rate: float

    description: str


@dataclass(frozen=True)
class EvaluationReport:
    dataset_cases: int

    replay_changed_cases: int
    replay_unchanged_cases: int

    metrics: list[
        EvaluationMetric
    ] = field(
        default_factory=list
    )

    notes: list[str] = field(
        default_factory=list
    )