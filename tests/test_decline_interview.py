from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# Load feature file
scenarios("features/decline_interview_invitation.feature")


# --------------------------------------------------
# Client
# --------------------------------------------------


@pytest.fixture
def client():
    return TestClient(app)


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
# Helper
# --------------------------------------------------


def create_test_interview(client):

    data = {
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

    response = client.post("/api/interviews", json=data)

    assert response.status_code == 200

    interviews = client.get("/api/interviews").json()

    return interviews[-1]["id"]


# ==================================================
# Scenario 1
# ==================================================


@given("the job seeker has received an interview invitation")
def job_seeker_received_invitation(client, context):

    context.interview_id = create_test_interview(client)


@when("the job seeker declines the interview")
def job_seeker_declines(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/decline")


@then('the interview status should be updated to "Declined"')
def verify_declined_status(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Interview declined"


# ==================================================
# Scenario 2
# ==================================================


@given("the job seeker has declined the interview")
def job_seeker_already_declined(client, context):

    context.interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{context.interview_id}/decline")


@when("the system processes the request")
def system_processes_request(client, context):

    context.response = client.get(f"/api/interviews/{context.interview_id}")


@then("the updated interview status should be saved in the database")
def verify_database_status(context):

    assert context.response.status_code == 200

    assert context.response.json()["status"] == "Declined"
