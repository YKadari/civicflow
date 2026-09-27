from app.tools.payments import (
    check_payment,
)


def main():
    result = check_payment(
        "CF-10001"
    )

    print()
    print("Success:")
    print(result.success)

    print()
    print("Message:")
    print(result.message)

    print()
    print("Payments:")

    for payment in result.payments:
        print(
            f"- {payment.payment_id}: "
            f"${payment.amount} "
            f"({payment.status})"
        )


if __name__ == "__main__":
    main()