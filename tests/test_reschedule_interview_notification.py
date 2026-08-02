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

scenarios("features/request_reschedule_interview_notification.feature")


# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# CONTEXT
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.interview_id: str | None = None
        self.document = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# MOCK EMAIL
# ==================================================


@pytest.fixture
def mock_email(monkeypatch):
    email_context = {
        "sent": False,
        "email": None,
        "company": None,
        "candidate": None,
        "position": None,
        "status": None,
        "reason": None,
        "requested_date": None,
        "requested_time": None,
    }

    async def fake_send_notification(
        email,
        company,
        candidate,
        position,
        status,
        reason=None,
        requested_date=None,
        requested_time=None,
    ):
        email_context["sent"] = True
        email_context["email"] = email
        email_context["company"] = company
        email_context["candidate"] = candidate
        email_context["position"] = position
        email_context["status"] = status
        email_context["reason"] = reason
        email_context["requested_date"] = requested_date
        email_context["requested_time"] = requested_time

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
        "interview_id": f"TEST_RESCHEDULE_REQUEST_{suffix}",
        "candidate_id": f"TEST_CANDIDATE_{suffix}",
        "company_id": f"TEST_COMPANY_{suffix}",
    }

    yield data

    db.collection("interviews").document(data["interview_id"]).delete()
    db.collection("job_seeker").document(data["candidate_id"]).delete()
    db.collection("company").document(data["company_id"]).delete()


# ==================================================
# CREATE TEST INTERVIEW
# ==================================================


def create_test_interview(test_data):
    interview_id = test_data["interview_id"]
    candidate_id = test_data["candidate_id"]
    company_id = test_data["company_id"]

    db.collection("job_seeker").document(candidate_id).set(
        {
            "name": "James",
            "email": "james@test.com",
        }
    )

    db.collection("company").document(company_id).set(
        {
            "companyName": "Test Company",
            "email": "employer@test.com",
            "address": "Penang",
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

    return interview_id


def create_reschedule_request(client, test_data):
    interview_id = create_test_interview(test_data)

    response = client.put(
        f"/api/interviews/{interview_id}/reschedule-request",
        json={
            "requestedDate": "2026-07-25",
            "requestedTime": "14:00",
            "reason": "Unable to attend original schedule",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Reschedule request sent"

    return interview_id, response


# ==================================================
# SCENARIO 1
# ==================================================


@given("a job seeker submits an interview reschedule request")
def submit_reschedule_request(
    client,
    context,
    mock_email,
    test_data,
):
    interview_id, response = create_reschedule_request(
        client,
        test_data,
    )

    context.interview_id = interview_id
    context.response = response


@when("the request is created successfully")
def request_created(context):
    assert context.interview_id is not None

    context.document = db.collection("interviews").document(context.interview_id).get()


@then("the employer should receive a notification about the request")
def verify_notification(mock_email, context):
    assert context.document is not None
    assert context.document.exists

    data = context.document.to_dict()

    assert data is not None
    assert data["status"] == "Reschedule Requested"
    assert data["applicantResponse"] == "Reschedule Requested"
    assert data["requestedDate"] == "2026-07-25"
    assert data["requestedTime"] == "14:00"
    assert data["rescheduleReason"] == ("Unable to attend original schedule")

    assert mock_email["sent"] is True
    assert mock_email["email"] == "employer@test.com"
    assert mock_email["company"] == "Test Company"
    assert mock_email["candidate"] == "James"
    assert mock_email["position"] == "Software Engineer"
    assert mock_email["status"] == "Reschedule Requested"
    assert mock_email["reason"] == ("Unable to attend original schedule")
    assert mock_email["requested_date"] == "2026-07-25"
    assert mock_email["requested_time"] == "14:00"


# ==================================================
# SCENARIO 2
# ==================================================


@given("the employer has received a reschedule request notification")
def employer_received_notification(
    client,
    context,
    mock_email,
    test_data,
):
    interview_id, response = create_reschedule_request(
        client,
        test_data,
    )

    context.interview_id = interview_id
    context.response = response

    assert mock_email["sent"] is True


@when("the employer opens the notification")
def employer_open_notification(context):
    assert context.interview_id is not None

    context.document = db.collection("interviews").document(context.interview_id).get()


@then("the requested new interview date and time should be displayed")
def verify_details(context):
    assert context.document is not None
    assert context.document.exists

    data = context.document.to_dict()

    assert data is not None
    assert data["requestedDate"] == "2026-07-25"
    assert data["requestedTime"] == "14:00"
    assert data["status"] == "Reschedule Requested"
    assert data["rescheduleReason"] == ("Unable to attend original schedule")
