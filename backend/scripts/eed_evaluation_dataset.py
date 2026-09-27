from app.evaluation.dataset import (
    seed_evaluation_dataset,
)


def main():
    specs = (
        seed_evaluation_dataset()
    )

    print()
    print(
        "CivicFlow synthetic evaluation "
        "dataset seeded successfully."
    )

    print(
        f"Evaluation cases: "
        f"{len(specs)}"
    )

    print()

    print(
        "First case:",
        specs[0].case_id,
    )

    print(
        "Last case:",
        specs[-1].case_id,
    )


if __name__ == "__main__":
    main()