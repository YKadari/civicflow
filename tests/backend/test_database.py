from app.database.repository import get_case
from app.domain.models import CaseStatus


def test_get_case():
    case = get_case("CF-10001")

    assert case is not None
    assert case.case_id == "CF-10001"
    assert case.program == "housing_assistance"
    assert case.status == CaseStatus.ACTIVE
    assert case.citizen_id == "CIT-5001"

def test_get_case_not_found():
    case = get_case("CF-DOES-NOT-EXIST")

    assert case is None