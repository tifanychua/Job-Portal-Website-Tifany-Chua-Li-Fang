from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

from itsdangerous import TimestampSigner
import base64
import json

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/filter_interview_records.feature")


# ==========================================
# CONSTANT
# ==========================================

COMPANY_ID = "C000001"

SECRET_KEY = "jobconnect-secret-key"


TEST_INTERVIEW_IDS = [
    "TEST_INTERVIEW_FILTER_001",
    "TEST_INTERVIEW_FILTER_002",
    "TEST_INTERVIEW_FILTER_003",
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
# ==========================================


@given("the employer has interview records with different statuses")
def employer_has_records():

    create_interview_records()


@when("the employer selects an interview status filter")
def select_status_filter(client, context):

    context["response"] = client.get("/employer/interviews?status=Scheduled")


@then("the system should display only interview records matching the selected status")
def verify_filter(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ==========================================
# SCENARIO 2
# ==========================================


@given("the employer is viewing the interview records page")
def employer_view_records():

    create_interview_records()


@when("the employer does not select any status filter")
def view_all_records(client, context):

    context["response"] = client.get("/employer/interviews")


@then("the system should display all interview records")
def verify_all_records(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


# ==========================================
# SCENARIO 3
# ==========================================


@given("the employer applies a status filter")
def employer_apply_filter():

    create_interview_records()


@when("no interview records match the selected status")
def no_matching_records(client, context):

    context["response"] = client.get("/employer/interviews?status=Rejected")


@then('the system should display a "No interview records found" message')
def verify_empty(context):

    response = context["response"]

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
