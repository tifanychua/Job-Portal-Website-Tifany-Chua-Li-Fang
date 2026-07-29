from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/filter_interview_records.feature")


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

TEST_INTERVIEW_IDS = [
    "TEST_INTERVIEW_FILTER_001",
    "TEST_INTERVIEW_FILTER_002",
    "TEST_INTERVIEW_FILTER_003",
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

    interviews = [
        {
            "id": "TEST_INTERVIEW_FILTER_001",
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Scheduled",
        },
        {
            "id": "TEST_INTERVIEW_FILTER_002",
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "status": "Completed",
        },
        {
            "id": "TEST_INTERVIEW_FILTER_003",
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "status": "Cancelled",
        },
    ]

    for interview in interviews:

        db.collection("interviews").document(interview["id"]).set(
            {
                "candidateName": interview["candidateName"],
                "position": interview["position"],
                "status": interview["status"],
            }
        )


# ==========================================
# SCENARIO 1
# Filter by status
# ==========================================


@given("the employer has interview records with different statuses")
def employer_has_interview_records(context):

    create_interview_records()


@when("the employer selects an interview status filter")
def select_status_filter(client, context):

    context["response"] = client.get("/employer/interviews?status=Scheduled")


@then("the system should display only interview records matching the selected status")
def verify_filtered_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "John Tan" in response.text

    assert "Mary Lee" not in response.text

    assert "Alex Wong" not in response.text


# ==========================================
# SCENARIO 2
# View all records
# ==========================================


@given("the employer is viewing the interview records page")
def employer_view_page(context):

    create_interview_records()


@when("the employer does not select any status filter")
def no_filter(client, context):

    context["response"] = client.get("/employer/interviews")


@then("the system should display all interview records")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "John Tan" in response.text

    assert "Mary Lee" in response.text

    assert "Alex Wong" in response.text


# ==========================================
# SCENARIO 3
# No matching records
# ==========================================


@given("the employer applies a status filter")
def apply_invalid_filter(context):

    create_interview_records()


@when("no interview records match the selected status")
def select_no_match_filter(client, context):

    context["response"] = client.get("/employer/interviews?status=Rejected")


@then('the system should display a "No interview records found" message')
def verify_no_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "No interview records found" in response.text
