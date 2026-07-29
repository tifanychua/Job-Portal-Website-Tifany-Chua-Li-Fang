from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE
# ==========================================

scenarios("features/search_interview_records.feature")


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

TEST_IDS = ["TEST_SEARCH_INTERVIEW_001", "TEST_SEARCH_INTERVIEW_002", "TEST_SEARCH_INTERVIEW_003"]


def delete_test_data():

    for interview_id in TEST_IDS:

        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_data()

    yield

    delete_test_data()


def create_interview_records():

    records = [
        {
            "id": "TEST_SEARCH_INTERVIEW_001",
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Scheduled",
        },
        {
            "id": "TEST_SEARCH_INTERVIEW_002",
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "status": "Completed",
        },
        {
            "id": "TEST_SEARCH_INTERVIEW_003",
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "status": "Cancelled",
        },
    ]

    for record in records:

        db.collection("interviews").document(record["id"]).set(
            {
                "candidateName": record["candidateName"],
                "position": record["position"],
                "status": record["status"],
            }
        )


# ==========================================
# SCENARIO 1
# Search keyword
# ==========================================


@given("the employer has existing interview records with job seekers")
def existing_records(context):

    create_interview_records()


@when("the employer enters a relevant keyword in the search bar")
def search_keyword(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=John")


@then("the system should display interview records that match the keyword")
def verify_search_result(context):

    response = context["response"]

    assert response.status_code == 200

    assert "John Tan" in response.text

    assert "Mary Lee" not in response.text


# ==========================================
# SCENARIO 2
# No result
# ==========================================


@given("the employer enters a keyword that does not match any interview record")
def no_matching_records(context):

    create_interview_records()


@when("the search is performed")
def perform_invalid_search(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=XYZ")


@then('the system should display a "No interview records found" message')
def verify_no_result(context):

    response = context["response"]

    assert response.status_code == 200

    assert "No interview records found" in response.text


# ==========================================
# SCENARIO 3
# Clear search
# ==========================================


@given("the employer has performed an interview record search")
def previous_search(context):

    create_interview_records()


@when("the employer clears the search keyword")
def clear_search(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=")


@then("the system should display all interview records again")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    assert "John Tan" in response.text

    assert "Mary Lee" in response.text

    assert "Alex Wong" in response.text
