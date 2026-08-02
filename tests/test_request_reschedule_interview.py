import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import interview
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# FEATURE
# ==================================================

scenarios("features/request_reschedule_interview.feature")


# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# MOCK EMAIL
# ==================================================


@pytest.fixture
def mock_email(monkeypatch):

    async def fake_send_email(*args, **kwargs):
        return None

    async def fake_notification(*args, **kwargs):
        return None

    if hasattr(interview, "send_interview_email"):
        monkeypatch.setattr(interview, "send_interview_email", fake_send_email)

    if hasattr(interview, "send_employer_interview_notification"):
        monkeypatch.setattr(interview, "send_employer_interview_notification", fake_notification)

    if hasattr(interview, "notify_employer"):
        monkeypatch.setattr(interview, "notify_employer", fake_notification)


# ==================================================
# CONTEXT
# ==================================================


class Context:
    def __init__(self):

        self.interview_id = None

        self.response = None

        self.document = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# CREATE TEST DATA
# ==================================================


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

    print("CREATE:", response.status_code, response.text)

    assert response.status_code == 200

    interviews = client.get("/api/interviews")

    data = interviews.json()

    print("ALL:", data)

    return data[-1]["id"]


# ==================================================
# SCENARIO 1
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

    print("RESCHEDULE:", context.response.status_code, context.response.text)


@then("the reschedule request should be sent to the employer")
def verify_sent(context):

    assert context.response.status_code == 200


# ==================================================
# SCENARIO 2
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

    print("SUBMIT:", response.status_code, response.text)

    assert response.status_code == 200


@when("the system processes the request")
def process_request(context):

    # Direct Firestore checking
    # Avoid protected GET API

    context.document = db.collection("interviews").document(context.interview_id).get()


@then("the reschedule request details should be saved in the database")
def verify_saved(context):

    assert context.document.exists

    data = context.document.to_dict()

    print("DATABASE:", data)

    assert data["status"] == "Reschedule Requested"

    assert data["requestedDate"] == "2026-07-25"

    assert data["requestedTime"] == "14:00"

    assert data["rescheduleReason"] == "Personal appointment"
