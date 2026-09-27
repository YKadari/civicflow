import pytest

from app.tools.payments import (
    check_payment,
)


pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)


def test_check_payment_returns_missing_payment():
    result = check_payment(
        "CF-10001"
    )

    assert result.success is True

    assert (
        result.case_id
        == "CF-10001"
    )

    assert len(
        result.payments
    ) >= 1

    payment = result.payments[0]

    assert (
        payment.payment_id
        == "PAY-10001-SEP"
    )

    assert (
        payment.status
        == "missing"
    )


def test_check_payment_returns_paid_payment():
    result = check_payment(
        "CF-10002"
    )

    assert result.success is True

    assert len(
        result.payments
    ) >= 1

    assert any(
        payment.status == "paid"
        for payment in result.payments
    )


def test_check_payment_case_not_found():
    result = check_payment(
        "CF-DOES-NOT-EXIST"
    )

    assert result.success is False

    assert result.payments == []

    assert (
        result.message
        == "Case not found."
    )