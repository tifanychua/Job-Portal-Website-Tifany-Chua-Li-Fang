from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE
# ==========================================

scenarios("features/filter_jobseeker_interview_records.feature")


# ==========================================
# CLIENT
# ==========================================


@pytest.fixture
def client():

    return TestClient(app)


# ==========================================
# CONTEXT
# ==========================================


@pytest.fixture
def context():

    return {}


# ==========================================
# TEST DATA
# ==========================================

APPLICATION_ID = "APP001"


TEST_INTERVIEW_IDS = [
    "TEST_JOBSEEKER_FILTER_001",
    "TEST_JOBSEEKER_FILTER_002",
    "TEST_JOBSEEKER_FILTER_003",
]


def delete_test_interviews():

    for interview_id in TEST_INTERVIEW_IDS:

        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_interviews()

    yield

    delete_test_interviews()


# ==========================================
# CREATE DATA
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
def job_seeker_has_records(context):

    create_interview_records()


@when("the job seeker selects an interview status filter")
def select_status_filter(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/filter" "?application_id=APP001" "&status=Scheduled"
    )


@then("the system should display only interview records matching the selected status")
def verify_filtered_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "Scheduled" in response.text

    assert "Accepted" not in response.text

    assert "Cancelled" not in response.text


# ==========================================
# SCENARIO 2
# ==========================================


@given("the job seeker is viewing the interview records page")
def view_interview_page(context):

    create_interview_records()


@when("the job seeker does not select any status filter")
def no_status_filter(client, context):

    context["response"] = client.get("/api/applicant/interviews/filter" "?application_id=APP001")


@then("the system should display all interview records")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "Scheduled" in response.text

    assert "Accepted" in response.text

    assert "Cancelled" in response.text


# ==========================================
# SCENARIO 3
# ==========================================


@given("the job seeker applies a status filter")
def apply_status_filter(context):

    create_interview_records()


@when("no interview records match the selected status")
def select_invalid_status(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/filter" "?application_id=APP001" "&status=Completed"
    )


@then('the system should display a "No interview records found" message')
def verify_no_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "No interview records found" in response.text
