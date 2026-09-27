from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.connection import SessionLocal
from app.database.models import CaseModel
from app.domain.models import (
    Approval,
    Case,
    CaseContext,
    CaseEvent,
    CaseStatus,
    Citizen,
    Document,
    Payment,
)

def get_case(case_id: str) -> Case | None:
    with SessionLocal() as session:
        statement = select(CaseModel).where(
            CaseModel.case_id == case_id
        )

        result = session.execute(statement)

        db_case = result.scalar_one_or_none()

        if db_case is None:
            return None

        return Case(
            case_id=db_case.case_id,
            program=db_case.program,
            status=CaseStatus(db_case.status),
            citizen_id=db_case.citizen_id,
            created_at=db_case.opened_at,
        )

def get_case_context(case_id: str) -> CaseContext | None:
    with SessionLocal() as session:
        statement = (
            select(CaseModel)
            .where(CaseModel.case_id == case_id)
            .options(
                selectinload(CaseModel.citizen),
                selectinload(CaseModel.payments),
                selectinload(CaseModel.documents),
                selectinload(CaseModel.events),
                selectinload(CaseModel.approvals),
            )
        )

        result = session.execute(statement)

        db_case = result.scalar_one_or_none()

        if db_case is None:
            return None

        case = Case(
            case_id=db_case.case_id,
            program=db_case.program,
            status=CaseStatus(db_case.status),
            citizen_id=db_case.citizen_id,
            created_at=db_case.opened_at,
        )

        citizen = Citizen(
            citizen_id=db_case.citizen.citizen_id,
            full_name=db_case.citizen.full_name,
            email=db_case.citizen.email,
            phone=db_case.citizen.phone,
        )

        payments = [
            Payment(
                payment_id=payment.payment_id,
                amount=payment.amount,
                scheduled_date=payment.scheduled_date,
                paid_date=payment.paid_date,
                status=payment.status,
            )
            for payment in db_case.payments
        ]

        documents = [
            Document(
                document_id=document.document_id,
                document_type=document.document_type,
                file_name=document.file_name,
                uploaded_at=document.uploaded_at,
                review_status=document.review_status,
            )
            for document in db_case.documents
        ]

        events = [
            CaseEvent(
                event_id=event.event_id,
                event_type=event.event_type,
                description=event.description,
                created_at=event.created_at,
            )
            for event in db_case.events
        ]

        approvals = [
            Approval(
                approval_id=approval.approval_id,
                action_type=approval.action_type,
                status=approval.status,
                requested_at=approval.requested_at,
                decided_at=approval.decided_at,
                reviewer=approval.reviewer,
            )
            for approval in db_case.approvals
        ]

        return CaseContext(
            case=case,
            citizen=citizen,
            payments=payments,
            documents=documents,
            events=events,
            approvals=approvals,
        )