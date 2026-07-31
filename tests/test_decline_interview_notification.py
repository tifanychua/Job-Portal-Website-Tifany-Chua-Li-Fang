from __future__ import annotations

import pytest

from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview
from job_portal_web.backend.database import db

# ==================================================
# TEST CLIENT
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# MOCK EMAIL NOTIFICATION
# ==================================================


@pytest.fixture
def mock_email(monkeypatch):

    context = {"sent": False, "status": None}

    async def fake_send_notification(*args, **kwargs):

        context["sent"] = True

        if "status" in kwargs:

            context["status"] = kwargs["status"]

        elif len(args) >= 5:

            context["status"] = args[4]

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    return context


# ==================================================
# TEST DATA
# ==================================================

TEST_INTERVIEW_ID = "TEST_DECLINE_INTERVIEW_001"


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


def create_test_interview(client):

    db.collection("interviews").document(TEST_INTERVIEW_ID).set(
        {
            "candidateId": "123",
            "companyId": "C000001",
            "candidateName": "James",
            "position": "Software Engineer",
            "stage": "Technical Interview",
            "date": "2026-07-20",
            "time": "10:00",
            "duration": "60 Minutes",
            "interviewType": "online",
            "interviewer": "John",
            "meetingLink": "https://meet.google.com/test",
            "notes": "Prepare portfolio",
            "status": "Scheduled",
        }
    )

    return TEST_INTERVIEW_ID


# ==================================================
# NORMAL TEST 1
# ==================================================


def test_decline_interview_success(client, mock_email):

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/decline")

    assert response.status_code == 200

    assert response.json()["message"] == ("Interview declined")

    assert mock_email["sent"] is True

    assert mock_email["status"] == ("Declined")


# ==================================================
# NORMAL TEST 2
# ==================================================


def test_declined_interview_saved(client, mock_email):

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/decline")

    assert response.status_code == 200

    document = db.collection("interviews").document(interview_id).get()

    data = document.to_dict()

    assert data["status"] == "Declined"


# ==================================================
# NORMAL TEST 3
# ==================================================


def test_decline_invalid_interview(client):

    response = client.put("/api/interviews/INVALID_ID/decline")

    assert response.status_code in (404, 500)


# ==================================================
# BDD FEATURE
# ==================================================

scenarios("features/decline_interview_invitation.feature")


# ==================================================
# BDD CONTEXT
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.interview_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# BDD SCENARIO 1
# ==================================================


@given("the job seeker has received an interview invitation")
def received_invitation(client, context):

    context.interview_id = create_test_interview(client)


@when("the job seeker declines the interview")
def decline_interview(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/decline")


@then('the interview status should be updated to "Declined"')
def verify_declined(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == ("Interview declined")


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the job seeker has declined the interview")
def already_declined(client, context):

    context.interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{context.interview_id}/decline")

    assert response.status_code == 200


@when("the system processes the request")
def process_request(context):

    # Status is already saved after decline API call.
    # Avoid GET API because it requires authentication.

    pass


@then("the updated interview status should be saved in the database")
def verify_database_status(context):

    document = db.collection("interviews").document(context.interview_id).get()

    assert document.exists is True

    data = document.to_dict()

    assert data["status"] == "Declined"
