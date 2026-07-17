from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


def create_test_interview():

    interview_id = "WGHcFQI8s6URdhusEbGW"

    db.collection("interviews").document(interview_id).set(
        {
            "candidateName": "John Smith",
            "position": "Software Developer",
            "date": "2026-07-25",
            "time": "14:00",
            "status": "Scheduled",
        }
    )

    return interview_id


def test_cancel_interview_success():
    """
    Scenario:
    Given the employer has a scheduled interview
    When the employer selects the cancel interview option
    Then the interview status should be updated to "Cancelled"
    """

    interview_id = create_test_interview()

    response = client.put(f"/api/interviews/{interview_id}/cancel")

    assert response.status_code == 200

    assert response.json()["message"] == ("Interview cancelled successfully!")

    updated = db.collection("interviews").document(interview_id).get().to_dict()

    assert updated["status"] == "Cancelled"


def test_cancelled_status_saved():
    """
    Scenario:
    Given the employer has cancelled an interview
    When the cancellation process is completed
    Then the updated interview status should be saved in the database
    """

    interview_id = create_test_interview()

    # Cancel interview

    client.put(f"/api/interviews/{interview_id}/cancel")

    # Check database

    document = db.collection("interviews").document(interview_id).get()

    data = document.to_dict()

    assert data["status"] == "Cancelled"
