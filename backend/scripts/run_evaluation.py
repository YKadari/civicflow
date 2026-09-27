import json
from pathlib import Path

from app.evaluation.runner import (
    evaluation_report_to_dict,
    run_evaluation,
)


def main():
    print()
    print(
        "Running CivicFlow evaluation..."
    )
    print()

    report = run_evaluation(
        seed_dataset=True
    )

    print(
        "Synthetic cases:",
        report.dataset_cases,
    )

    print()

    print(
        "Policy Replay:"
    )

    print(
        "  Changed cases:",
        report.replay_changed_cases,
    )

    print(
        "  Unchanged cases:",
        report.replay_unchanged_cases,
    )

    print()

    print(
        "Safety / workflow metrics:"
    )

    for metric in report.metrics:
        print()

        print(
            f"  {metric.name}"
        )

        print(
            f"    "
            f"{metric.passed}/"
            f"{metric.total}"
        )

        print(
            f"    {metric.rate}%"
        )

        print(
            f"    "
            f"{metric.description}"
        )

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    docs_directory = (
        project_root
        / "docs"
    )

    docs_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        docs_directory
        / "evaluation_results.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            evaluation_report_to_dict(
                report
            ),
            file,
            indent=2,
        )

    print()
    print(
        "Evaluation report written to:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()