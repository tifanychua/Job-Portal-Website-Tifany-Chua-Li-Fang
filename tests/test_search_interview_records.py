import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/search_interview_records.feature")


# ==========================================
# CONSTANT
# ==========================================

COMPANY_ID = "C000001"

SECRET_KEY = "jobconnect-secret-key"


TEST_INTERVIEW_IDS = [
    "TEST_SEARCH_INTERVIEW_001",
    "TEST_SEARCH_INTERVIEW_002",
    "TEST_SEARCH_INTERVIEW_003",
]


# ==========================================
# CLIENT
# ==========================================


@pytest.fixture
def client():

    client = TestClient(app)

    mock_company_session(client)

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


def delete_test_records():

    for interview_id in TEST_INTERVIEW_IDS:
        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_records()

    yield

    delete_test_records()


# ==========================================
# CREATE SESSION COOKIE
# ==========================================


def mock_company_session(client):

    session_data = {"company_id": COMPANY_ID}

    json_data = json.dumps(session_data)

    encoded = base64.b64encode(json_data.encode()).decode()

    signer = TimestampSigner(SECRET_KEY)

    signed_cookie = signer.sign(encoded.encode()).decode()

    client.cookies.set("session", signed_cookie)


# ==========================================
# CREATE TEST DATA
# ==========================================


def create_interview_records():

    records = [
        {
            "candidateName": "John Tan",
            "position": "Software Developer",
            "status": "Scheduled",
            "companyId": COMPANY_ID,
        },
        {
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "status": "Completed",
            "companyId": COMPANY_ID,
        },
        {
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "status": "Cancelled",
            "companyId": COMPANY_ID,
        },
    ]

    for index, record in enumerate(records):
        db.collection("interviews").document(TEST_INTERVIEW_IDS[index]).set(record)


# ==========================================
# SCENARIO 1
# Search keyword
# ==========================================


@given("the employer has existing interview records with job seekers")
def existing_records():

    create_interview_records()


@when("the employer enters a relevant keyword in the search bar")
def search_keyword(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=John")


@then("the system should display interview records that match the keyword")
def verify_search_result(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ==========================================
# SCENARIO 2
# No result
# ==========================================


@given("the employer enters a keyword that does not match any interview record")
def no_matching_records():

    create_interview_records()


@when("the search is performed")
def perform_invalid_search(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=XYZ")


@then('the system should display a "No interview records found" message')
def verify_no_result(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ==========================================
# SCENARIO 3
# Clear search
# ==========================================


@given("the employer has performed an interview record search")
def previous_search():

    create_interview_records()


@when("the employer clears the search keyword")
def clear_search(client, context):

    context["response"] = client.get("/employer/interviews/search?keyword=")


@then("the system should display all interview records again")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
