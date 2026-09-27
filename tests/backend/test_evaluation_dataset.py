import pytest

from app.database.repository import (
    get_case_context,
    list_cases,
)
from app.evaluation.dataset import (
    seed_evaluation_dataset,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def test_seed_evaluation_dataset_creates_24_cases():
    seed_evaluation_dataset()

    cases = list_cases()

    evaluation_cases = [
        case
        for case in cases
        if case.case_id.startswith(
            "CF-EVAL-"
        )
    ]

    assert (
        len(evaluation_cases)
        == 24
    )


def test_evaluation_dataset_contains_expected_scenarios():
    seed_evaluation_dataset()

    approved_case = (
        get_case_context(
            "CF-EVAL-001"
        )
    )

    changed_case = (
        get_case_context(
            "CF-EVAL-007"
        )
    )

    held_case = (
        get_case_context(
            "CF-EVAL-013"
        )
    )

    paid_case = (
        get_case_context(
            "CF-EVAL-017"
        )
    )

    pending_case = (
        get_case_context(
            "CF-EVAL-021"
        )
    )

    assert approved_case is not None
    assert changed_case is not None
    assert held_case is not None
    assert paid_case is not None
    assert pending_case is not None

    assert (
        approved_case.payments[0].status
        == "missing"
    )

    assert any(
        document.document_type
        == "address_verification"
        and document.review_status
        == "approved"
        for document
        in approved_case.documents
    )

    assert any(
        document.document_type
        == "address_verification"
        and document.review_status
        == "pending"
        for document
        in changed_case.documents
    )

    assert (
        held_case.payments[0].status
        == "held"
    )

    assert (
        paid_case.payments[0].status
        == "paid"
    )

    assert (
        pending_case.case.status.value
        == "pending"
    )