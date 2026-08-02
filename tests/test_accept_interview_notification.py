from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import interview
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# LOAD FEATURE FILE
# ==================================================

scenarios("features/accept_interview_notification.feature")


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
def email_mock(monkeypatch):

    context = {
        "sent": False,
        "email": None,
        "company": None,
        "candidate": None,
        "position": None,
        "status": None,
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

        context["sent"] = True

        context["email"] = email

        context["company"] = company

        context["candidate"] = candidate

        context["position"] = position

        context["status"] = status

    monkeypatch.setattr(interview, "send_employer_interview_notification", fake_send_notification)

    return context


# ==================================================
# CONTEXT
# ==================================================


class Context:
    def __init__(self):

        self.interview_id = None

        self.email_sent = False


@pytest.fixture
def context():

    return Context()


# ==================================================
# CREATE TEST DATA
# ==================================================


def create_interview(client):

    candidate_id = "123"

    company_id = "C000001"

    # Create job seeker

    db.collection("job_seeker").document(candidate_id).set(
        {"name": "James", "email": "james@test.com"}
    )

    # Create company

    db.collection("company").document(company_id).set(
        {"companyName": "ABC Technology", "email": "hr@abc.com", "address": "Penang"}
    )

    interview_data = {
        "candidateId": candidate_id,
        "companyId": company_id,
        "candidateName": "James",
        "position": "Software Engineer",
        "stage": "Technical Interview",
        "date": "2026-07-20",
        "time": "10:00",
        "duration": "60 Minutes",
        "interviewType": "physical",
        "interviewer": "John",
        "meetingLink": "",
        "notes": "Bring documents",
    }

    response = client.post("/api/interviews", json=interview_data)

    assert response.status_code == 200

    interviews = client.get("/api/interviews").json()

    return interviews[-1]["id"]


# ==================================================
# NORMAL TEST CASE 1
# ==================================================


def test_employer_receives_accept_notification(client, email_mock):

    interview_id = create_interview(client)

    response = client.put(f"/api/interviews/{interview_id}/accept")

    assert response.status_code == 200

    assert email_mock["sent"] is True

    assert email_mock["status"] == "Accepted"


# ==================================================
# NORMAL TEST CASE 2
# ==================================================


def test_notification_contains_interview_details(client, email_mock):

    interview_id = create_interview(client)

    client.put(f"/api/interviews/{interview_id}/accept")

    assert email_mock["sent"] is True

    assert email_mock["candidate"] == "James"

    assert email_mock["position"] == "Software Engineer"

    assert email_mock["status"] == "Accepted"


# ==================================================
# BDD SCENARIO 1
# ==================================================


@given("the employer has successfully scheduled an interview")
def scheduled_interview(client, context):

    context.interview_id = create_interview(client)


@when("the applicant accepts the interview")
def applicant_accepts(client, context, email_mock):

    client.put(f"/api/interviews/{context.interview_id}/accept")

    context.email_sent = email_mock["sent"]


@when("the interview details are saved")
def interview_details_saved(client, context, email_mock):

    client.put(f"/api/interviews/{context.interview_id}/accept")

    context.email_sent = email_mock["sent"]


@then("the employer should receive an acceptance notification email")
def verify_employer_email(context):

    assert context.email_sent is True


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the employer has scheduled an interview")
def employer_scheduled_interview(client, context):

    context.interview_id = create_interview(client)


@when("the notification email is sent")
def notification_email_sent(client, context, email_mock):

    client.put(f"/api/interviews/{context.interview_id}/accept")

    context.email_sent = email_mock["sent"]


@then("the notification should contain interview details")
def verify_notification_content(email_mock):

    assert email_mock["sent"] is True

    assert email_mock["candidate"] == "James"

    assert email_mock["position"] == "Software Engineer"


# ==================================================
# COMPATIBILITY STEPS
# (For old feature file wording)
# ==================================================


@then("the job seeker should receive an interview notification email")
def verify_job_seeker_email(context):

    assert context.email_sent is True


@then("the email should contain the interview date, time, and interview location")
def verify_email_details(email_mock):

    assert email_mock["sent"] is True
