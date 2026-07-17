from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview
from job_portal_web.backend.database import db

# ==================================================
# Load Feature File
# ==================================================

scenarios("features/request_reschedule_interview_notification.feature")


# ==================================================
# Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


@pytest.fixture
def mock_email(monkeypatch):

    context = {"sent": False, "status": None, "reason": None}

    async def fake_send_notification(*args, **kwargs):

        context["sent"] = True

        # Your notify_employer sends:
        # email,
        # employer name,
        # candidate,
        # position,
        # status,
        # reason

        if len(args) >= 5:

            context["status"] = args[4]

        if len(args) >= 6:

            context["reason"] = args[5]

    # IMPORTANT:
    # patch the function used inside interview.py

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    return context


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.interview_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Helper
# ==================================================


def create_test_interview(client):

    # Create company

    db.collection("company").document("C000001").set(
        {"companyName": "Test Company", "employerId": "EMP001"}
    )

    # Create employer

    db.collection("employers").document("EMP001").set(
        {"name": "John", "email": "chualifang@gmail.com"}
    )

    # Create interview

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


def create_reschedule_request(client):

    interview_id = create_test_interview(client)

    response = client.put(
        f"/api/interviews/{interview_id}/reschedule-request",
        json={
            "requestedDate": "2026-07-25",
            "requestedTime": "14:00",
            "reason": "Unable to attend original schedule",
        },
    )

    assert response.status_code == 200

    return interview_id


# ==================================================
# Scenario 1
# ==================================================


@given("a job seeker submits an interview reschedule request")
def submit_reschedule_request(client, context, mock_email):

    context.interview_id = create_reschedule_request(client)


@when("the request is created successfully")
def request_created(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the employer should receive a notification about the request")
def verify_notification(mock_email):

    assert mock_email["sent"] is True

    assert mock_email["status"] == "Reschedule Requested"


# ==================================================
# Scenario 2
# ==================================================


@given("the employer has received a reschedule request notification")
def employer_received_notification(client, context, mock_email):

    context.interview_id = create_reschedule_request(client)


@when("the employer opens the notification")
def employer_open_notification(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the requested new interview date and time should be displayed")
def verify_details(context):

    data = context.response.json()

    assert data["requestedDate"] == "2026-07-25"

    assert data["requestedTime"] == "14:00"
