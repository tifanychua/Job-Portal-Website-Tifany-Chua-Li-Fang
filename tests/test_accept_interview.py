from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview
from job_portal_web.backend.database import db

# ==================================================
# LOAD FEATURE
# ==================================================

scenarios("features/accept_interview_invitation.feature")


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

    context = {"sent": False}

    async def fake_send_notification(*args, **kwargs):

        context["sent"] = True

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    return context


# ==================================================
# CREATE TEST INTERVIEW
# ==================================================


def create_test_interview(client):

    candidate_id = "TEST_CANDIDATE_001"
    company_id = "TEST_COMPANY_001"

    db.collection("job_seeker").document(candidate_id).set(
        {"name": "James", "email": "james@test.com"}
    )

    db.collection("company").document(company_id).set(
        {"companyName": "ABC Technology", "email": "hr@abc.com", "address": "Penang"}
    )

    data = {
        "candidateId": candidate_id,
        "companyId": company_id,
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
# NORMAL TEST
# ==================================================


def test_accept_interview_success(client, mock_email):

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/accept")

    assert response.status_code == 200

    assert response.json()["message"] == "Interview accepted"


# ==================================================
# VERIFY STATUS
# ==================================================


def test_accepted_interview_saved(client, mock_email):

    interview_id = create_test_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/accept")

    assert response.status_code == 200

    # Check Firestore directly
    document = db.collection("interviews").document(interview_id).get()

    data = document.to_dict()

    assert data["status"] == "Accepted"


# ==================================================
# INVALID INTERVIEW
# ==================================================


def test_accept_invalid_interview(client, mock_email):

    response = client.put("/api/interviews/INVALID_ID/accept")

    assert response.status_code in (404, 400)


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


@when("the job seeker accepts the interview")
def accept_interview(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/accept")


@then('the interview status should be updated to "Accepted"')
def verify_accept(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Interview accepted"


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the job seeker has accepted an interview")
def accepted_before(client, context):

    context.interview_id = create_test_interview(client)

    client.put(f"/api/interviews/{context.interview_id}/accept")


@when("the system processes the request")
def process_request(client, context):

    context.response = client.put(f"/api/interviews/{context.interview_id}/accept")


@then("the updated interview status should be saved in the database")
def verify_saved_status(context):

    assert context.response.status_code == 200
