from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import text

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


def clear_database(session):
    session.execute(
        text(
            """
            TRUNCATE TABLE
                audit_logs,
                approvals,
                case_events,
                documents,
                payments,
                cases,
                citizens
            CASCADE;
            """
        )
    )


def seed_database():
    with SessionLocal() as session:
        clear_database(session)

        citizens = [
            CitizenModel(
                citizen_id="CIT-5001",
                full_name="Jordan Lee",
                email="jordan.lee@example.com",
                phone="555-0101",
            ),
            CitizenModel(
                citizen_id="CIT-5002",
                full_name="Taylor Morgan",
                email="taylor.morgan@example.com",
                phone="555-0102",
            ),
            CitizenModel(
                citizen_id="CIT-5003",
                full_name="Alex Rivera",
                email="alex.rivera@example.com",
                phone="555-0103",
            ),
        ]

        session.add_all(citizens)

        cases = [
            CaseModel(
                case_id="CF-10001",
                citizen_id="CIT-5001",
                program="housing_assistance",
                status="active",
            ),
            CaseModel(
                case_id="CF-10002",
                citizen_id="CIT-5002",
                program="housing_assistance",
                status="pending",
            ),
            CaseModel(
                case_id="CF-10003",
                citizen_id="CIT-5003",
                program="housing_assistance",
                status="active",
            ),
        ]

        session.add_all(cases)

        payments = [
            PaymentModel(
                payment_id="PAY-10001-SEP",
                case_id="CF-10001",
                amount=Decimal("850.00"),
                scheduled_date=date(2026, 9, 1),
                paid_date=None,
                status="missing",
            ),
            PaymentModel(
                payment_id="PAY-10002-SEP",
                case_id="CF-10002",
                amount=Decimal("725.00"),
                scheduled_date=date(2026, 9, 1),
                paid_date=date(2026, 9, 1),
                status="paid",
            ),
            PaymentModel(
                payment_id="PAY-10003-SEP",
                case_id="CF-10003",
                amount=Decimal("900.00"),
                scheduled_date=date(2026, 9, 1),
                paid_date=None,
                status="held",
            ),
        ]

        session.add_all(payments)

        documents = [
            DocumentModel(
                document_id="DOC-10001-1",
                case_id="CF-10001",
                document_type="income_verification",
                file_name="income_verification_2026.pdf",
                review_status="approved",
            ),
            DocumentModel(
                document_id="DOC-10002-1",
                case_id="CF-10002",
                document_type="address_verification",
                file_name="address_verification.pdf",
                review_status="approved",
            ),
            DocumentModel(
                document_id="DOC-10003-1",
                case_id="CF-10003",
                document_type="income_verification",
                file_name="income_verification_update.pdf",
                review_status="unreviewed",
            ),
        ]

        session.add_all(documents)

        now = datetime.now()

        events = [
            CaseEventModel(
                event_id="EVT-10001-1",
                case_id="CF-10001",
                event_type="citizen_request",
                description=(
                    "Citizen reported that the September payment "
                    "was not received."
                ),
            ),
            CaseEventModel(
                event_id="EVT-10002-1",
                case_id="CF-10002",
                event_type="payment_processed",
                description="September payment processed successfully.",
            ),
            CaseEventModel(
                event_id="EVT-10003-1",
                case_id="CF-10003",
                event_type="notice_sent",
                description=(
                    "Citizen notified that updated income verification "
                    "was required."
                ),
                created_at=now - timedelta(days=8),
            ),
        ]

        session.add_all(events)

        approvals = [
            ApprovalModel(
                approval_id="APR-10003-1",
                case_id="CF-10003",
                action_type="close_case",
                status="pending",
            )
        ]

        session.add_all(approvals)

        audit_logs = [
            AuditLogModel(
                audit_id="AUD-10001-1",
                case_id="CF-10001",
                event_type="case_created",
                details={"source": "synthetic_seed"},
            ),
            AuditLogModel(
                audit_id="AUD-10002-1",
                case_id="CF-10002",
                event_type="case_created",
                details={"source": "synthetic_seed"},
            ),
            AuditLogModel(
                audit_id="AUD-10003-1",
                case_id="CF-10003",
                event_type="case_created",
                details={"source": "synthetic_seed"},
            ),
        ]

        session.add_all(audit_logs)

        session.commit()

        print("CivicFlow database seeded successfully.")


if __name__ == "__main__":
    seed_database()