from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timezone,
)
from decimal import Decimal

from sqlalchemy import delete

from app.database.connection import SessionLocal
from app.database.models import (
    ApprovalModel,
    CaseEventModel,
    CaseModel,
    CitizenModel,
    DocumentModel,
    PaymentModel,
)


@dataclass(frozen=True)
class SyntheticCaseSpec:
    case_id: str
    citizen_id: str
    payment_id: str
    document_id: str
    event_id: str

    case_status: str
    payment_status: str
    address_review_status: str


def _build_case_specs() -> list[SyntheticCaseSpec]:
    specs: list[SyntheticCaseSpec] = []

    def add_group(
        start: int,
        end: int,
        case_status: str,
        payment_status: str,
        address_review_status: str,
    ) -> None:

        for number in range(
            start,
            end + 1,
        ):
            suffix = f"{number:03d}"

            specs.append(
                SyntheticCaseSpec(
                    case_id=(
                        f"CF-EVAL-{suffix}"
                    ),
                    citizen_id=(
                        f"CIT-EVAL-{suffix}"
                    ),
                    payment_id=(
                        f"PAY-EVAL-{suffix}"
                    ),
                    document_id=(
                        f"DOC-EVAL-{suffix}"
                    ),
                    event_id=(
                        f"EVT-EVAL-{suffix}"
                    ),
                    case_status=case_status,
                    payment_status=payment_status,
                    address_review_status=(
                        address_review_status
                    ),
                )
            )

    # Active + missing + approved address.
    #
    # HA-PAY v1: allowed
    # HA-PAY v2: allowed
    add_group(
        1,
        6,
        case_status="active",
        payment_status="missing",
        address_review_status="approved",
    )

    # Active + missing + address not approved.
    #
    # HA-PAY v1: allowed
    # HA-PAY v2: blocked
    #
    # These are our Policy Replay "changed" cases.
    add_group(
        7,
        12,
        case_status="active",
        payment_status="missing",
        address_review_status="pending",
    )

    # Active + held payment.
    #
    # check_payment: allowed
    # open_investigation: blocked
    add_group(
        13,
        16,
        case_status="active",
        payment_status="held",
        address_review_status="approved",
    )

    # Active + already-paid payment.
    #
    # No missing-payment action is necessary.
    add_group(
        17,
        20,
        case_status="active",
        payment_status="paid",
        address_review_status="approved",
    )

    # Pending case + missing payment.
    #
    # Missing payment exists, but the case itself
    # is not active.
    add_group(
        21,
        22,
        case_status="pending",
        payment_status="missing",
        address_review_status="approved",
    )

    add_group(
        23,
        24,
        case_status="pending",
        payment_status="missing",
        address_review_status="pending",
    )

    return specs


EVALUATION_CASES = (
    _build_case_specs()
)


def get_evaluation_case_specs(
) -> list[SyntheticCaseSpec]:

    return list(
        EVALUATION_CASES
    )


def _request_description(
    spec: SyntheticCaseSpec,
) -> str:

    if spec.payment_status == "missing":
        return (
            "My housing assistance payment "
            "has not arrived. Please investigate "
            "the missing payment."
        )

    if spec.payment_status == "held":
        return (
            "My housing assistance payment "
            "appears to be held. Please check "
            "the payment status."
        )

    return (
        "I have a question about my recent "
        "housing assistance payment."
    )


def seed_evaluation_dataset(
) -> list[SyntheticCaseSpec]:
    """
    Add a deterministic synthetic evaluation
    dataset to CivicFlow.

    Only CF-EVAL-* records are replaced.
    Existing demo cases such as CF-10001 are
    left untouched.
    """

    specs = get_evaluation_case_specs()

    case_ids = [
        spec.case_id
        for spec in specs
    ]

    citizen_ids = [
        spec.citizen_id
        for spec in specs
    ]

    created_at = datetime(
        2026,
        9,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )

    scheduled_date = date(
        2026,
        9,
        1,
    )

    with SessionLocal() as session:
        # -------------------------------------
        # Remove a prior evaluation dataset.
        #
        # Delete children before parents.
        # -------------------------------------

        session.execute(
            delete(
                ApprovalModel
            ).where(
                ApprovalModel.case_id.in_(
                    case_ids
                )
            )
        )

        session.execute(
            delete(
                CaseEventModel
            ).where(
                CaseEventModel.case_id.in_(
                    case_ids
                )
            )
        )

        session.execute(
            delete(
                DocumentModel
            ).where(
                DocumentModel.case_id.in_(
                    case_ids
                )
            )
        )

        session.execute(
            delete(
                PaymentModel
            ).where(
                PaymentModel.case_id.in_(
                    case_ids
                )
            )
        )

        session.execute(
            delete(
                CaseModel
            ).where(
                CaseModel.case_id.in_(
                    case_ids
                )
            )
        )

        session.execute(
            delete(
                CitizenModel
            ).where(
                CitizenModel.citizen_id.in_(
                    citizen_ids
                )
            )
        )

        session.flush()

        # -------------------------------------
        # Insert the new synthetic cases.
        # -------------------------------------

        for index, spec in enumerate(
            specs,
            start=1,
        ):
            suffix = f"{index:03d}"

            citizen = CitizenModel(
                citizen_id=(
                    spec.citizen_id
                ),
                full_name=(
                    f"Synthetic Citizen "
                    f"{suffix}"
                ),
                email=(
                    f"citizen{suffix}"
                    "@example.test"
                ),
                phone=(
                    f"555-01{index:02d}"
                ),
            )

            case = CaseModel(
                case_id=spec.case_id,
                citizen_id=(
                    spec.citizen_id
                ),
                program=(
                    "housing_assistance"
                ),
                status=(
                    spec.case_status
                ),
            )

            paid_date = None

            if (
                spec.payment_status
                == "paid"
            ):
                paid_date = date(
                    2026,
                    9,
                    2,
                )

            payment = PaymentModel(
                payment_id=(
                    spec.payment_id
                ),
                case_id=spec.case_id,
                amount=Decimal(
                    "850.00"
                ),
                scheduled_date=(
                    scheduled_date
                ),
                paid_date=paid_date,
                status=(
                    spec.payment_status
                ),
            )

            document = DocumentModel(
                document_id=(
                    spec.document_id
                ),
                case_id=spec.case_id,
                document_type=(
                    "address_verification"
                ),
                file_name=(
                    f"address_{suffix}.pdf"
                ),
                uploaded_at=created_at,
                review_status=(
                    spec
                    .address_review_status
                ),
            )

            event = CaseEventModel(
                event_id=spec.event_id,
                case_id=spec.case_id,
                event_type=(
                    "citizen_request"
                ),
                description=(
                    _request_description(
                        spec
                    )
                ),
                created_at=created_at,
            )

            session.add(
                citizen
            )

            session.add(
                case
            )

            session.add(
                payment
            )

            session.add(
                document
            )

            session.add(
                event
            )

        session.commit()

    return specs