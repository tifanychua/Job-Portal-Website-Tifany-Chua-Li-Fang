from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db
from job_portal_web.backend import interview

# --------------------------------------------------
# BDD Feature
# --------------------------------------------------

scenarios("features/request_reschedule_interview.feature")


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

    async def fake_send_email(*args, **kwargs):
        return None

    async def fake_send_notification(*args, **kwargs):
        return None

    monkeypatch.setattr(interview, "send_interview_email", fake_send_email)

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    monkeypatch.setattr(interview, "notify_employer", fake_send_notification)


# --------------------------------------------------
# Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.interview_id = None

        self.response = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Helper Function
# --------------------------------------------------


def create_interview(client):

    db.collection("company").document("C000001").set(
        {"companyName": "Test Company", "employerId": "EMP001"}
    )

    response = client.post(
        "/api/interviews",
        json={
            "candidateId": "A000001",
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
        },
    )

    assert response.status_code == 200

    interviews = client.get("/api/interviews").json()

    return interviews[-1]["id"]


# ==================================================
# Scenario 1:
# Job Seeker Requests Reschedule
# ==================================================


@given("the job seeker has a scheduled interview")
def scheduled_interview(client, context, mock_email):

    context.interview_id = create_interview(client)


@when("the job seeker selects a new preferred date and time")
def select_new_date_time():

    pass


@when("submits the reschedule request")
def submit_request(client, context):

    context.response = client.put(
        f"/api/interviews/{context.interview_id}/reschedule-request",
        json={
            "requestedDate": "2026-07-25",
            "requestedTime": "14:00",
            "reason": "Unable to attend original schedule",
        },
    )


@then("the reschedule request should be sent to the employer")
def verify_sent(context):

    assert context.response.status_code == 200


# ==================================================
# Scenario 2:
# Save Reschedule Request
# ==================================================


@given("the job seeker has submitted a reschedule request")
def submitted_request(client, context, mock_email):

    context.interview_id = create_interview(client)

    response = client.put(
        f"/api/interviews/{context.interview_id}/reschedule-request",
        json={
            "requestedDate": "2026-07-25",
            "requestedTime": "14:00",
            "reason": "Personal appointment",
        },
    )

    assert response.status_code == 200


@when("the system processes the request")
def process_request(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the reschedule request details should be saved in the database")
def verify_saved(context):

    assert context.response.status_code == 200

    data = context.response.json()

    assert data["requestedDate"] == "2026-07-25"

    assert data["requestedTime"] == "14:00"

    assert data["rescheduleReason"] == "Personal appointment"
