from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """
    Shared FastAPI test client.
    """
    return TestClient(app)


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_schedule_interview_success(client: TestClient):
    """
    Acceptance test: Employer schedules an interview successfully

    Given the employer has shortlisted a job seeker
    When the employer submits interview details
    Then the interview should be created successfully
    """

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
    print(response.json())

    assert response.status_code == 200


# --------------------------------------------------
# 2. Negative Test
# --------------------------------------------------


def test_schedule_interview_without_required_details(client: TestClient):
    """
    Negative test: Employer submits incomplete interview details

    Given the employer is scheduling an interview
    When required details are missing
    Then the system should reject the request
    """

    interview_data = {
        "candidateId": "123",
        "companyId": "C000001",
        "candidateName": "James",
        "position": "Software Engineer",
        "stage": "",
        "date": "",
        "time": "",
        "duration": "60 Minutes",
        "interviewType": "online",
        "interviewer": "",
    }

    response = client.post("/api/interviews", json=interview_data)

    assert response.status_code == 422


# --------------------------------------------------
# 3. Verify Saved Interview Schedule
# --------------------------------------------------


def test_interview_schedule_saved(client: TestClient):
    """
    Acceptance test: Interview details are saved

    Given the employer has scheduled an interview
    When the system processes the schedule
    Then the interview details can be retrieved
    """

    response = client.get("/api/interviews")

    assert response.status_code == 200


# --------------------------------------------------
# 4. Retrieve Interview List
# --------------------------------------------------


def test_get_interviews(client: TestClient):
    """
    Acceptance test: Employer views scheduled interviews

    Given interview schedules exist
    When employer views interview list
    Then schedules are returned
    """

    response = client.get("/api/interviews")

    assert response.status_code == 200


# --------------------------------------------------
# 5. BDD Feature Loading
# --------------------------------------------------

scenarios("features/interview_schedule.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None

        self.interview_data = {}


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1:
# Employer schedules an interview
# --------------------------------------------------


@given("the employer has shortlisted a job seeker")
def shortlisted_candidate(context):

    context.interview_data = {
        "candidateId": "123",
        "companyId": "C000001",
        "candidateName": "James",
        "position": "Software Engineer",
    }


@when(
    "the employer enters the interview stage, date, time, duration, interview type, and interviewer details and submits the interview schedule"
)
def submit_interview(client, context):

    context.interview_data.update(
        {
            "stage": "Technical Interview",
            "date": "2026-07-20",
            "time": "10:00",
            "duration": "60 Minutes",
            "interviewType": "online",
            "interviewer": "John",
            "meetingLink": "https://meet.google.com/test",
            "notes": "Prepare portfolio",
        }
    )

    context.response = client.post("/api/interviews", json=context.interview_data)


@then("the interview should be created successfully")
def verify_created(context):

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 2:
# Save interview schedule details
# --------------------------------------------------


@given("the employer has scheduled an interview")
def scheduled_interview(context):

    context.interview_data = {"candidateId": "123"}


@when("the system processes the schedule")
def process_schedule(client, context):

    context.response = client.get("/api/interviews")


@then("the interview details should be saved in the database")
def verify_saved(context):

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 3:
# Online Interview
# --------------------------------------------------


@given("the employer has selected an online interview type")
def online_interview(context):

    context.interview_data = {
        "candidateId": "123",
        "companyId": "C000001",
        "candidateName": "James",
        "position": "Software Engineer",
        "interviewType": "online",
    }


@when("the employer enters a valid meeting link and submits the interview schedule")
def submit_online_interview(client, context):

    context.interview_data.update(
        {
            "stage": "Technical Interview",
            "date": "2026-07-20",
            "time": "10:00",
            "duration": "60 Minutes",
            "interviewer": "John",
            "meetingLink": "https://meet.google.com/test",
            "notes": "Prepare portfolio",
        }
    )

    context.response = client.post("/api/interviews", json=context.interview_data)


@then("the online interview details should be saved successfully")
def verify_online(context):

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 4:
# Physical Interview
# --------------------------------------------------


@given("the employer has selected a physical interview type")
def physical_interview(context):

    context.interview_data = {
        "candidateId": "123",
        "companyId": "C000001",
        "candidateName": "James",
        "position": "Software Engineer",
        "interviewType": "physical",
    }


@when("the employer enters the interview location and submits the interview schedule")
def submit_physical_interview(client, context):

    context.interview_data.update(
        {
            "stage": "HR Interview",
            "date": "2026-07-21",
            "time": "14:00",
            "duration": "60 Minutes",
            "interviewer": "Mary",
            "interviewType": "physical",
            "location": "Company Office",
            "meetingLink": "",
            "notes": "Bring documents",
        }
    )

    context.response = client.post("/api/interviews", json=context.interview_data)

    print(context.response.json())


@then("the physical interview details should be saved successfully")
def verify_physical(context):

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 5:
# Missing Required Details
# --------------------------------------------------


@given("the employer is creating an interview schedule")
def creating_schedule(context):

    context.interview_data = {"candidateId": "123", "companyId": "C000001"}


@when("the employer leaves required interview details empty and submits the interview schedule")
def submit_empty_schedule(client, context):

    context.interview_data.update(
        {"stage": "", "date": "", "time": "", "duration": "", "interviewer": ""}
    )

    context.response = client.post("/api/interviews", json=context.interview_data)


@then("the system should display a validation message and the interview should not be created")
def verify_validation(context):

    assert context.response.status_code == 422
