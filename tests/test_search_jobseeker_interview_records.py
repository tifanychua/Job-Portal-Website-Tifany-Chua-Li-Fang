from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE
# ==========================================

scenarios("features/search_jobseeker_interview_records.feature")


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


TEST_IDS = ["TEST_JOBSEEKER_SEARCH_001", "TEST_JOBSEEKER_SEARCH_002", "TEST_JOBSEEKER_SEARCH_003"]


def delete_test_data():

    for interview_id in TEST_IDS:

        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_data()

    yield

    delete_test_data()


# ==========================================
# CREATE RECORDS
# ==========================================


def create_interview_records():

    records = [
        {
            "id": "TEST_JOBSEEKER_SEARCH_001",
            "candidateId": APPLICATION_ID,
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Scheduled",
        },
        {
            "id": "TEST_JOBSEEKER_SEARCH_002",
            "candidateId": APPLICATION_ID,
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "status": "Completed",
        },
        {
            "id": "TEST_JOBSEEKER_SEARCH_003",
            "candidateId": APPLICATION_ID,
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "status": "Cancelled",
        },
    ]

    for record in records:

        db.collection("interviews").document(record["id"]).set(record)


# ==========================================
# SCENARIO 1
# Search keyword
# ==========================================


@given("the job seeker has existing interview records")
def existing_records(context):

    create_interview_records()


@when("the job seeker enters a relevant keyword in the search bar")
def search_keyword(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/search" "?application_id=APP001" "&keyword=Software"
    )


@then("the system should display interview records that match the keyword")
def verify_search_result(context):

    response = context["response"]

    assert response.status_code == 200

    assert "Software Developer" in response.text

    assert "UI Designer" not in response.text


# ==========================================
# SCENARIO 2
# No result
# ==========================================


@given("the job seeker enters a keyword that does not match any interview record")
def no_matching_record(context):

    create_interview_records()


@when("the search is performed")
def perform_search(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/search" "?application_id=APP001" "&keyword=Doctor"
    )


@then('the system should display a "No interview records found" message')
def verify_no_result(context):

    response = context["response"]

    assert response.status_code == 200

    assert "No interview records found" in response.text


# ==========================================
# SCENARIO 3
# Clear search
# ==========================================


@given("the job seeker has performed an interview record search")
def previous_search(context):

    create_interview_records()


@when("the job seeker clears the search keyword")
def clear_search(client, context):

    context["response"] = client.get(
        "/api/applicant/interviews/search" "?application_id=APP001" "&keyword="
    )


@then("the system should display all interview records again")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "John Tan" in response.text

    assert "Mary Lee" in response.text

    assert "Alex Wong" in response.text
