import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==========================================
# LOAD FEATURE
# ==========================================

scenarios("features/filter_jobseeker_interview_records.feature")


# ==========================================
# CONSTANT
# ==========================================

APPLICATION_ID = "APP001"

SECRET_KEY = "jobconnect-secret-key"


TEST_INTERVIEW_IDS = [
    "TEST_JOBSEEKER_FILTER_001",
    "TEST_JOBSEEKER_FILTER_002",
    "TEST_JOBSEEKER_FILTER_003",
]


# ==========================================
# CLIENT
# ==========================================


@pytest.fixture
def client():

    client = TestClient(app)

    mock_applicant_session(client)

    return client


# ==========================================
# CONTEXT
# ==========================================


@pytest.fixture
def context():

    return {}


# ==========================================
# CLEANUP
# ==========================================


def delete_test_interviews():

    for interview_id in TEST_INTERVIEW_IDS:
        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_interviews()

    yield

    delete_test_interviews()


# ==========================================
# CREATE APPLICANT SESSION COOKIE
# ==========================================


def mock_applicant_session(client):

    session_data = {"applicant_id": APPLICATION_ID}

    json_data = json.dumps(session_data)

    encoded = base64.b64encode(json_data.encode()).decode()

    signer = TimestampSigner(SECRET_KEY)

    signed_cookie = signer.sign(encoded.encode()).decode()

    client.cookies.set("session", signed_cookie)

    print("APPLICANT SESSION:", signed_cookie)


# ==========================================
# CREATE TEST DATA
# ==========================================


def create_interview_records():

    records = [
        {
            "id": "TEST_JOBSEEKER_FILTER_001",
            "candidateId": APPLICATION_ID,
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Scheduled",
        },
        {
            "id": "TEST_JOBSEEKER_FILTER_002",
            "candidateId": APPLICATION_ID,
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Accepted",
        },
        {
            "id": "TEST_JOBSEEKER_FILTER_003",
            "candidateId": APPLICATION_ID,
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Cancelled",
        },
    ]

    for record in records:
        db.collection("interviews").document(record["id"]).set(record)


# ==========================================
# SCENARIO 1
# ==========================================


@given("the job seeker has interview records with different statuses")
def job_seeker_has_records():

    create_interview_records()


@when("the job seeker selects an interview status filter")
def select_status_filter(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/filter",
        params={"application_id": APPLICATION_ID, "status": "Scheduled"},
    )


@then("the system should display only interview records matching the selected status")
def verify_filtered_records(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) > 0

    for item in data:
        assert item["status"] == "Scheduled"


# ==========================================
# SCENARIO 2
# ==========================================


@given("the job seeker is viewing the interview records page")
def view_interview_page():

    create_interview_records()


@when("the job seeker does not select any status filter")
def no_status_filter(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/filter", params={"application_id": APPLICATION_ID}
    )


@then("the system should display all interview records")
def verify_all_records(context):

    response = context["context"] if False else context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    statuses = [item["status"] for item in data]

    assert "Scheduled" in statuses

    assert "Accepted" in statuses

    assert "Cancelled" in statuses


# ==========================================
# SCENARIO 3
# ==========================================


@given("the job seeker applies a status filter")
def apply_status_filter():

    create_interview_records()


@when("no interview records match the selected status")
def select_invalid_status(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/filter",
        params={"application_id": APPLICATION_ID, "status": "Completed"},
    )


@then('the system should display a "No interview records found" message')
def verify_no_records(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert data == []
