from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# TEST DATA
# ==================================================

TEST_INTERVIEW_ID = "TEST_CANCEL_INTERVIEW_001"


def delete_test_interview():

    db.collection("interviews").document(TEST_INTERVIEW_ID).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_interview()

    yield

    delete_test_interview()


# ==================================================
# CREATE TEST INTERVIEW
# ==================================================


def create_test_interview():

    db.collection("interviews").document(TEST_INTERVIEW_ID).set(
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
        }
    )

    return TEST_INTERVIEW_ID


# ==================================================
# TEST 1
# ==================================================


def test_cancel_interview_success(client):
    """
    Given the employer has a scheduled interview

    When the employer selects cancel interview

    Then the interview status should become Cancelled
    """

    interview_id = create_test_interview()

    response = client.put(f"/api/interviews/{interview_id}/cancel")

    assert response.status_code == 200

    assert response.json()["message"] == ("Interview cancelled successfully")

    interview = db.collection("interviews").document(interview_id).get().to_dict()

    assert interview["status"] == "Cancelled"


# ==================================================
# TEST 2
# ==================================================


def test_cancelled_status_saved(client):
    """
    Given the employer cancelled an interview

    When the cancellation process is completed

    Then the cancelled status should persist
    """

    interview_id = create_test_interview()

    response = client.put(f"/api/interviews/{interview_id}/cancel")

    assert response.status_code == 200

    saved_interview = db.collection("interviews").document(interview_id).get().to_dict()

    assert saved_interview["status"] == "Cancelled"


# ==================================================
# TEST 3
# ==================================================


def test_cancel_invalid_interview(client):
    """
    Given the interview does not exist

    When employer cancels the interview

    Then system should return 404
    """

    response = client.put("/api/interviews/INVALID_ID/cancel")

    assert response.status_code == 404
