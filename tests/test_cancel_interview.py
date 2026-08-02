from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# TEST INTERVIEW FIXTURE
# ==================================================


@pytest.fixture
def interview_id():
    """
    Create a unique interview for each test and remove it afterwards.
    """

    test_interview_id = f"TEST_CANCEL_{uuid4()}"

    db.collection("interviews").document(test_interview_id).set(
        {
            "candidateId": "123",
            "companyId": "C000001",
            "candidateName": "John Smith",
            "position": "Software Developer",
            "date": "2026-07-25",
            "time": "14:00",
            "duration": "60 Minutes",
            "interviewType": "online",
            "interviewer": "Michael",
            "meetingLink": "https://meet.google.com/test",
            "notes": "Prepare documents",
            "status": "Scheduled",
            "applicantResponse": "Pending",
        }
    )

    yield test_interview_id

    db.collection("interviews").document(test_interview_id).delete()


# ==================================================
# TEST 1
# ==================================================


def test_cancel_interview_success(client, interview_id):
    """
    Given the employer has a scheduled interview

    When the employer selects cancel interview

    Then the interview status should become Cancelled
    """

    response = client.put(f"/api/interviews/{interview_id}/cancel")

    assert response.status_code == 200
    assert response.json()["message"] == "Interview cancelled successfully"

    document = db.collection("interviews").document(interview_id).get()

    assert document.exists

    interview = document.to_dict()

    assert interview is not None
    assert interview["status"] == "Cancelled"
    assert interview["applicantResponse"] == "Cancelled"


# ==================================================
# TEST 2
# ==================================================


def test_cancelled_status_saved(client, interview_id):
    """
    Given the employer cancelled an interview

    When the cancellation process is completed

    Then the cancelled status should persist
    """

    response = client.put(f"/api/interviews/{interview_id}/cancel")

    assert response.status_code == 200

    document = db.collection("interviews").document(interview_id).get()

    assert document.exists

    saved_interview = document.to_dict()

    assert saved_interview is not None
    assert saved_interview["status"] == "Cancelled"
    assert saved_interview["applicantResponse"] == "Cancelled"


# ==================================================
# TEST 3
# ==================================================


def test_cancel_invalid_interview(client):
    """
    Given the interview does not exist

    When the employer cancels the interview

    Then the system should return 404
    """

    invalid_interview_id = f"INVALID_CANCEL_{uuid4()}"

    response = client.put(f"/api/interviews/{invalid_interview_id}/cancel")

    assert response.status_code == 404
