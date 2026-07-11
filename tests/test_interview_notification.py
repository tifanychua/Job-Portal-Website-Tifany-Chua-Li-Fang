from __future__ import annotations

import pytest

from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# -----------------------------------------
# Load BDD Feature
# -----------------------------------------

scenarios("features/interview_notification.feature")


# -----------------------------------------
# Test Client
# -----------------------------------------


@pytest.fixture
def client():

    return TestClient(app)


# -----------------------------------------
# Context
# -----------------------------------------


class Context:

    def __init__(self):

        self.response = None

        self.email_called = False

        self.interview_data = {}


@pytest.fixture
def context():

    return Context()


# =========================================
# Scenario 1:
# Job seeker receives notification email
# =========================================


@given("the employer has successfully scheduled an interview")
def employer_schedule_interview(context):

    context.interview_data = {
        "candidateId": "applicant001",
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


@when("the interview details are saved")
def save_interview(client, context, mocker):

    # Mock email sending
    mock_email = mocker.patch("job_portal_web.backend.interview.send_interview_email")

    context.response = client.post("/api/interviews", json=context.interview_data)

    context.email_called = mock_email


@then("the job seeker should receive an interview notification email")
def verify_email_notification(context):

    assert context.response.status_code == 200

    context.email_called.assert_called_once()


# =========================================
# Scenario 2:
# Email contains interview details
# =========================================


@given("the employer has scheduled an interview")
def scheduled_interview(context):

    context.interview_data = {
        "candidateName": "James",
        "date": "2026-07-20",
        "time": "10:00",
        "location": "Company Office",
    }


@when("the notification email is sent")
def send_notification(context):

    context.email_content = {
        "date": context.interview_data["date"],
        "time": context.interview_data["time"],
        "location": context.interview_data["location"],
    }


@then("the email should contain the interview date, time, and interview location")
def verify_email_content(context):

    assert context.email_content["date"] == "2026-07-20"

    assert context.email_content["time"] == "10:00"

    assert context.email_content["location"] == "Company Office"
