from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview

# --------------------------------------------------
# Test Client
# --------------------------------------------------


@pytest.fixture
def client():

    return TestClient(app)


# --------------------------------------------------
# Mock Email Notification
# --------------------------------------------------


@pytest.fixture
def mock_email(monkeypatch):

    context = {"sent": False, "status": None}

    async def fake_send_notification(*args, **kwargs):

        context["sent"] = True

        # get status from kwargs
        if "status" in kwargs:
            context["status"] = kwargs["status"]

        # if status is positional argument
        elif len(args) >= 5:
            context["status"] = args[4]

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    return context


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

    interviews = client.get("/api/interviews").json()

    return interviews[-1]["id"]


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_decline_interview_success(client, mock_email):
    """
    Given the job seeker has received an interview invitation
    When the job seeker declines the interview
    Then the interview status should be updated to Declined
    """

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/decline")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Interview declined"

    assert mock_email["sent"] is True

    assert mock_email["status"] == "Declined"


# --------------------------------------------------
# 2. Verify Saved Status
# --------------------------------------------------


def test_declined_interview_saved(client, mock_email):
    """
    Given the job seeker has declined the interview
    When the system processes the request
    Then the declined status should be saved
    """

    interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{interview_id}/decline")

    response = client.get(f"/api/interviews/{interview_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Declined"


# --------------------------------------------------
# 3. Negative Test
# --------------------------------------------------


def test_decline_invalid_interview(client, mock_email):
    """
    Given the interview does not exist
    When the job seeker declines the interview
    Then the system should return 404
    """

    response = client.put("/api/interviews/INVALID_ID/decline")

    assert response.status_code == 404


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/decline_interview_invitation.feature")


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
# Scenario 1
# --------------------------------------------------


@given("the job seeker has received an interview invitation")
def received_invitation(client, context):

    context.interview_id = create_test_interview(client)


@when("the job seeker declines the interview")
def decline_interview(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/decline")


@then('the interview status should be updated to "Declined"')
def verify_declined(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Interview declined"


# --------------------------------------------------
# Scenario 2
# --------------------------------------------------


@given("the job seeker has declined the interview")
def already_declined(client, context):

    context.interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{context.interview_id}/decline")


@when("the system processes the request")
def process_request(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the updated interview status should be saved in the database")
def verify_saved(context):

    assert context.response.status_code == 200

    assert context.response.json()["status"] == "Declined"
