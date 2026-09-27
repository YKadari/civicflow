from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import CaseModel
from app.domain.models import Case, CaseStatus


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