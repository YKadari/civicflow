from app.database.repository import get_case
from app.domain.models import CaseStatus
from app.database.repository import get_case, get_case_context
import pytest
pytestmark = pytest.mark.usefixtures("seeded_database")
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

def test_get_case_context():
    context = get_case_context("CF-10003")

    assert context is not None

    assert context.case.case_id == "CF-10003"
    assert context.citizen.citizen_id == "CIT-5003"

    assert len(context.payments) == 1
    assert context.payments[0].status == "held"

    assert len(context.documents) == 1
    assert context.documents[0].review_status == "unreviewed"

    assert len(context.events) == 1
    assert context.events[0].event_type == "notice_sent"

    assert len(context.approvals) == 1
    assert context.approvals[0].action_type == "close_case"
    assert context.approvals[0].status == "pending"