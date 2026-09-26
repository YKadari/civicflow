from datetime import datetime

from app.domain.models import Case, CaseStatus


def test_case_creation():
    case = Case(
        case_id="CF-10001",
        program="housing_assistance",
        status=CaseStatus.ACTIVE,
        citizen_id="CIT-5001",
        created_at=datetime.now(),
    )

    assert case.case_id == "CF-10001"
    assert case.program == "housing_assistance"
    assert case.status == CaseStatus.ACTIVE
    assert case.citizen_id == "CIT-5001"