from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import interview
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# LOAD FEATURE FILE
# ==================================================

scenarios("features/decline_interview_invitation.feature")


# ==================================================
# TEST CLIENT
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


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
# MOCK EMAIL NOTIFICATION
# ==================================================


@pytest.fixture
def mock_email(monkeypatch):
    email_context = {
        "sent": False,
        "email": None,
        "employer_name": None,
        "candidate_name": None,
        "position": None,
        "status": None,
    }

    async def fake_send_notification(
        email,
        employer_name,
        candidate_name,
        position,
        status,
        reason=None,
        requested_date=None,
        requested_time=None,
    ):
        email_context["sent"] = True
        email_context["email"] = email
        email_context["employer_name"] = employer_name
        email_context["candidate_name"] = candidate_name
        email_context["position"] = position
        email_context["status"] = status

    monkeypatch.setattr(
        interview,
        "send_employer_interview_notification",
        fake_send_notification,
    )

    return email_context


# ==================================================
# UNIQUE TEST DATA
# ==================================================


@pytest.fixture
def test_data():
    suffix = uuid4().hex

    data = {
        "interview_id": f"TEST_DECLINE_INTERVIEW_{suffix}",
        "company_id": f"TEST_DECLINE_COMPANY_{suffix}",
        "employer_id": f"TEST_DECLINE_EMPLOYER_{suffix}",
        "candidate_id": f"TEST_DECLINE_CANDIDATE_{suffix}",
    }

    yield data

    db.collection("interviews").document(data["interview_id"]).delete()

    db.collection("company").document(data["company_id"]).delete()

    db.collection("employers").document(data["employer_id"]).delete()

    db.collection("job_seeker").document(data["candidate_id"]).delete()


# ==================================================
# CREATE TEST DATA
# ==================================================


def create_test_interview(test_data):
    interview_id = test_data["interview_id"]
    company_id = test_data["company_id"]
    employer_id = test_data["employer_id"]
    candidate_id = test_data["candidate_id"]

    db.collection("employers").document(employer_id).set(
        {
            "name": "John",
            "email": "employer@example.com",
        }
    )

    db.collection("company").document(company_id).set(
        {
            "companyName": "ABC Technology",
            "employerId": employer_id,
            "email": "employer@example.com",
            "address": "Penang",
            "status": "Verified",
        }
    )

    db.collection("job_seeker").document(candidate_id).set(
        {
            "name": "James",
            "email": "james@example.com",
        }
    )

    db.collection("interviews").document(interview_id).set(
        {
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
            "status": "Scheduled",
            "applicantResponse": "Pending",
        }
    )

    interview_document = db.collection("interviews").document(interview_id).get()

    company_document = db.collection("company").document(company_id).get()

    employer_document = db.collection("employers").document(employer_id).get()

    assert interview_document.exists
    assert company_document.exists
    assert employer_document.exists

    return interview_id


def decline_interview_request(client, interview_id):
    document = db.collection("interviews").document(interview_id).get()

    assert document.exists

    response = client.put(f"/api/interviews/{interview_id}/decline")

    return response


# ==================================================
# NORMAL TEST 1
# ==================================================


def test_decline_interview_success(
    client,
    mock_email,
    test_data,
):
    interview_id = create_test_interview(test_data)

    response = decline_interview_request(
        client,
        interview_id,
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Interview declined"

    assert mock_email["sent"] is True
    assert mock_email["email"] == "employer@example.com"
    assert mock_email["candidate_name"] == "James"
    assert mock_email["position"] == "Software Engineer"
    assert mock_email["status"] == "Declined"


# ==================================================
# NORMAL TEST 2
# ==================================================


def test_declined_interview_saved(
    client,
    mock_email,
    test_data,
):
    interview_id = create_test_interview(test_data)

    response = decline_interview_request(
        client,
        interview_id,
    )

    assert response.status_code == 200, response.text

    document = db.collection("interviews").document(interview_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Declined"
    assert mock_email["sent"] is True


# ==================================================
# NORMAL TEST 3
# ==================================================


def test_decline_invalid_interview(client):
    invalid_id = f"INVALID_INTERVIEW_{uuid4().hex}"

    response = client.put(f"/api/interviews/{invalid_id}/decline")

    assert response.status_code == 404


# ==================================================
# BDD SCENARIO 1
# ==================================================


@given("the job seeker has received an interview invitation")
def received_invitation(context, test_data):
    context.interview_id = create_test_interview(test_data)


@when("the job seeker declines the interview")
def decline_interview(client, context):
    context.response = decline_interview_request(
        client,
        context.interview_id,
    )


@then('the interview status should be updated to "Declined"')
def verify_declined(context):
    assert context.response.status_code == 200
    assert context.response.json()["message"] == ("Interview declined")

    document = db.collection("interviews").document(context.interview_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Declined"


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the job seeker has declined the interview")
def already_declined(client, context, test_data):
    context.interview_id = create_test_interview(test_data)

    context.response = decline_interview_request(
        client,
        context.interview_id,
    )

    assert context.response.status_code == 200


@when("the system processes the request")
def process_request():
    pass


@then("the updated interview status should be saved in the database")
def verify_database_status(context):
    document = db.collection("interviews").document(context.interview_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Declined"
