from fastapi.testclient import TestClient

from app.main import app
import pytest

from app.ai.factory import get_ai_provider
from app.ai.models import (
    GroundedRecommendation,
    IntentClassification,
)
from app.domain.models import PolicyEvidence
from app.policies.factory import (
    get_policy_retriever,
)
pytestmark = pytest.mark.usefixtures("seeded_database")

client = TestClient(app)
class FakePolicyRetriever:
    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        return [
            PolicyEvidence(
                chunk_id="HA-PAY-V1-4_2",
                policy_id="HA-PAY",
                version=1,
                section="4.2 Missing Payments",
                content=(
                    "If a scheduled payment has not "
                    "been received within five "
                    "business days, a payment-status "
                    "investigation may be opened."
                ),
                similarity=0.90,
            )
        ]


def override_policy_retriever():
    return FakePolicyRetriever()
class FakeAIProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.99,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:

        return GroundedRecommendation(
            recommended_action="check_payment",
            rationale=(
                "The payment is marked missing and "
                "the payment policy applies."
            ),
            cited_chunk_ids=[
                "HA-PAY-V1-4_2"
            ],
            confidence=0.95,
        )
def override_ai_provider():
    return FakeAIProvider()


app.dependency_overrides[get_ai_provider] = (
    override_ai_provider
)
def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "civicflow-api",
    }

def test_get_case_context():
    response = client.get("/cases/CF-10003")

    assert response.status_code == 200

    data = response.json()

    assert data["case"]["case_id"] == "CF-10003"
    assert data["citizen"]["citizen_id"] == "CIT-5003"

    assert data["payments"][0]["status"] == "held"

    assert data["documents"][0]["review_status"] == "unreviewed"

    assert data["events"][0]["event_type"] == "notice_sent"

    assert data["approvals"][0]["action_type"] == "close_case"


def test_get_case_not_found():
    response = client.get("/cases/CF-99999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Case not found"
    }


def test_list_cases():
    response = client.get("/cases")

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 3


def test_filter_active_cases():
    response = client.get("/cases?status=active")

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for case in data:
        assert case["status"] == "active"

def test_create_case_request():
    response = client.post(
        "/cases/CF-10001/requests",
        json={
            "description": "Testing a new citizen request."
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_type"] == "citizen_request"

    assert data["description"] == (
        "Testing a new citizen request."
    )


def test_create_request_case_not_found():
    response = client.post(
        "/cases/CF-99999/requests",
        json={
            "description": "This should not work."
        },
    )

    assert response.status_code == 404


def test_analyze_payment_request():
    response = client.post(
        "/cases/CF-10001/analyze",
        json={
            "event_id": "EVT-10001-1"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["case_id"] == "CF-10001"
    assert data["request_type"] == "payment_issue"
    assert data["recommended_action"] == "check_payment"


def test_analyze_request_not_found():
    response = client.post(
        "/cases/CF-10001/analyze",
        json={
            "event_id": "EVT-DOES-NOT-EXIST"
        },
    )

    assert response.status_code == 404