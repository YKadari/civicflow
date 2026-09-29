from datetime import date

from decimal import Decimal

from sqlalchemy import delete

from app.database.connection import SessionLocal
from app.database.models import (
    ApprovalModel,
    AuditLogModel,
    CaseEventModel,
    CaseModel,
    CitizenModel,
    DocumentModel,
    PaymentModel,
)


DEMO_CASE_ID = "DEMO-APPROVAL"
DEMO_CITIZEN_ID = "CIT-DEMO-APPROVAL"


def seed_demo_approval():
    with SessionLocal() as session:
        # Make the script safe to rerun.
        session.execute(
            delete(ApprovalModel).where(
                ApprovalModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(AuditLogModel).where(
                AuditLogModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(CaseEventModel).where(
                CaseEventModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(DocumentModel).where(
                DocumentModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(PaymentModel).where(
                PaymentModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(CaseModel).where(
                CaseModel.case_id
                == DEMO_CASE_ID
            )
        )

        session.execute(
            delete(CitizenModel).where(
                CitizenModel.citizen_id
                == DEMO_CITIZEN_ID
            )
        )

        citizen = CitizenModel(
            citizen_id=DEMO_CITIZEN_ID,
            full_name="Morgan Chen",
            email="morgan.chen@example.com",
            phone="555-0199",
        )

        case = CaseModel(
            case_id=DEMO_CASE_ID,
            citizen_id=DEMO_CITIZEN_ID,
            program="housing_assistance",
            status="active",
        )

        payment = PaymentModel(
            payment_id="PAY-DEMO-APPROVAL-SEP",
            case_id=DEMO_CASE_ID,
            amount=Decimal("825.00"),
            scheduled_date=date(2026, 9, 1),
            paid_date=None,
            status="missing",
        )

        verification = DocumentModel(
            document_id="DOC-DEMO-APPROVAL-1",
            case_id=DEMO_CASE_ID,
            document_type="income_verification",
            file_name=(
                "income_verification_demo.pdf"
            ),
            review_status="approved",
        )

        payment_event = CaseEventModel(
            event_id="EVT-DEMO-APPROVAL-1",
            case_id=DEMO_CASE_ID,
            event_type="payment_missing",
            description=(
                "The September housing assistance "
                "payment was scheduled for "
                "September 1, 2026 and remains "
                "unreceived more than five "
                "business days after the scheduled "
                "payment date."
            ),
        )

        verification_event = CaseEventModel(
            event_id="EVT-DEMO-APPROVAL-2",
            case_id=DEMO_CASE_ID,
            event_type="verification_confirmed",
            description=(
                "Required income verification was "
                "approved and confirmed current and "
                "not expired for this case."
            ),
        )

        audit_log = AuditLogModel(
            audit_id="AUD-DEMO-APPROVAL-1",
            case_id=DEMO_CASE_ID,
            event_type="case_created",
            details={
                "source": "synthetic_demo",
                "purpose": (
                    "human_approval_demo"
                ),
            },
        )

        session.add_all(
            [
                citizen,
                case,
                payment,
                verification,
                payment_event,
                verification_event,
                audit_log,
            ]
        )

        session.commit()

        print(
            "DEMO-APPROVAL seeded successfully."
        )


if __name__ == "__main__":
    seed_demo_approval()