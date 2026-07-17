from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client() -> TestClient:

    return TestClient(app)


# --------------------------------------------------
# Mock Email / Notification
# --------------------------------------------------


@pytest.fixture
def mock_email(monkeypatch):

    async def fake_send_email(*args, **kwargs):
        return None

    async def fake_send_notification(*args, **kwargs):
        return None

    monkeypatch.setattr(interview, "send_interview_email", fake_send_email)

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    monkeypatch.setattr(interview, "notify_employer", fake_send_notification)


# --------------------------------------------------
# Helper Function
# --------------------------------------------------


def create_test_interview(client):

    interview_data = {
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
    }

    response = client.post("/api/interviews", json=interview_data)

    assert response.status_code == 200

    # Get created Firestore ID

    response = client.get("/api/interviews")

    assert response.status_code == 200

    interviews = response.json()

    return interviews[-1]["id"]


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_accept_interview_success(client: TestClient, mock_email):
    """
    Given the job seeker has received an interview invitation
    When the job seeker accepts the interview
    Then the interview should be accepted successfully
    """

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/accept")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Interview accepted"


# --------------------------------------------------
# 2. Verify Saved Status
# --------------------------------------------------


def test_accepted_interview_saved(client: TestClient, mock_email):
    """
    Given the job seeker has accepted an interview
    When the system retrieves the interview
    Then the status should be Accepted
    """

    interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{interview_id}/accept")

    response = client.get(f"/api/interviews/{interview_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Accepted"


# --------------------------------------------------
# 3. Negative Test
# --------------------------------------------------


def test_accept_invalid_interview(client: TestClient, mock_email):
    """
    Given the interview does not exist
    When the job seeker accepts the interview
    Then the system should reject the request
    """

    response = client.put("/api/interviews/INVALID_ID/accept")

    assert response.status_code in (404, 500)


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/accept_interview_invitation.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None

        self.interview_id = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1:
# Accept Interview
# --------------------------------------------------


@given("the job seeker has received an interview invitation")
def received_invitation(client, context, mock_email):

    context.interview_id = create_test_interview(client)


@when("the job seeker accepts the interview")
def accept_interview(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/accept")


@then('the interview status should be updated to "Accepted"')
def verify_accept(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Interview accepted"


# --------------------------------------------------
# Scenario 2:
# Save Accepted Status
# --------------------------------------------------


@given("the job seeker has accepted an interview")
def already_accepted(client, context, mock_email):

    context.interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{context.interview_id}/accept")


@when("the system processes the request")
def process_request(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the updated interview status should be saved in the database")
def verify_saved(context):

    assert context.response.status_code == 200

    assert context.response.json()["status"] == "Accepted"
