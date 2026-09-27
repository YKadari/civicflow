from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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