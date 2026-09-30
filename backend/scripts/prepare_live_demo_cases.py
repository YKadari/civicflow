from sqlalchemy import delete

from app.database.connection import SessionLocal
from app.database.models import (
    ApprovalModel,
    CaseEventModel,
    CaseModel,
    DocumentModel,
    PaymentModel,
)


def require(value, label):
    if value is None:
        raise RuntimeError(
            f"Required demo record not found: {label}"
        )

    return value


def prepare_live_demo_cases():
    with SessionLocal() as session:

        # ====================================================
        # CF-10002
        #
        # Demo purpose:
        # Investigation is plausible, but important evidence
        # is missing. The deterministic gate should allow the
        # proposal to reach Decision Challenge, which should
        # CHALLENGE it.
        # ====================================================

        case_2 = require(
            session.get(
                CaseModel,
                "CF-10002",
            ),
            "CF-10002",
        )

        payment_2 = require(
            session.get(
                PaymentModel,
                "PAY-10002-SEP",
            ),
            "PAY-10002-SEP",
        )

        document_2 = require(
            session.get(
                DocumentModel,
                "DOC-10002-1",
            ),
            "DOC-10002-1",
        )

        case_2.status = "active"

        payment_2.status = "missing"
        payment_2.paid_date = None

        document_2.review_status = "approved"

        # Remove stale approvals/events that could interfere
        # with the controlled recruiter demo.
        session.execute(
            delete(ApprovalModel).where(
                ApprovalModel.case_id
                == "CF-10002"
            )
        )

        session.execute(
            delete(CaseEventModel).where(
                CaseEventModel.case_id
                == "CF-10002"
            )
        )

        session.add(
            CaseEventModel(
                event_id="EVT-10002-DEMO-1",
                case_id="CF-10002",
                event_type=(
                    "payment_reported_missing"
                ),
                description=(
                    "Citizen reported that the "
                    "scheduled September payment "
                    "has not been received. "
                    "No confirmed determination "
                    "has yet established that more "
                    "than five business days have "
                    "elapsed or that required "
                    "verification documents are "
                    "not expired."
                ),
            )
        )

        # ====================================================
        # CF-10003
        #
        # Demo purpose:
        # Investigation prerequisites ARE established.
        # Decision Challenge should PASS and CivicFlow
        # should create a pending human approval.
        # ====================================================

        case_3 = require(
            session.get(
                CaseModel,
                "CF-10003",
            ),
            "CF-10003",
        )

        payment_3 = require(
            session.get(
                PaymentModel,
                "PAY-10003-SEP",
            ),
            "PAY-10003-SEP",
        )

        document_3 = require(
            session.get(
                DocumentModel,
                "DOC-10003-1",
            ),
            "DOC-10003-1",
        )

        case_3.status = "active"

        payment_3.status = "missing"
        payment_3.paid_date = None

        document_3.review_status = "approved"

        # Remove the original close-case approval and
        # previous case history so this becomes a clean
        # approval demo.
        session.execute(
            delete(ApprovalModel).where(
                ApprovalModel.case_id
                == "CF-10003"
            )
        )

        session.execute(
            delete(CaseEventModel).where(
                CaseEventModel.case_id
                == "CF-10003"
            )
        )

        session.add_all(
            [
                CaseEventModel(
                    event_id=(
                        "EVT-10003-DEMO-1"
                    ),
                    case_id="CF-10003",
                    event_type=(
                        "payment_timing_confirmed"
                    ),
                    description=(
                        "The September 1, 2026 "
                        "housing assistance payment "
                        "remains unreceived more than "
                        "five business days after its "
                        "scheduled payment date."
                    ),
                ),
                CaseEventModel(
                    event_id=(
                        "EVT-10003-DEMO-2"
                    ),
                    case_id="CF-10003",
                    event_type=(
                        "verification_confirmed"
                    ),
                    description=(
                        "Required income verification "
                        "is approved, current, and "
                        "confirmed not expired."
                    ),
                ),
            ]
        )

        session.commit()

        print(
            "Live CivicFlow demo cases prepared."
        )
        print(
            "CF-10001: read-only payment check"
        )
        print(
            "CF-10002: Decision Challenge demo"
        )
        print(
            "CF-10003: human approval demo"
        )


if __name__ == "__main__":
    prepare_live_demo_cases()