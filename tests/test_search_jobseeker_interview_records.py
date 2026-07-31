import sys
import base64
import json

from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from itsdangerous import TimestampSigner
from job_portal_web.backend.main import app
from job_portal_web.backend.database import db
# ==================================================
# IMPORT PROJECT
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))




# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# AUTHENTICATED CLIENT
# ==================================================


@pytest.fixture
def authenticated_client(client):

    session_data = {"user_type": "employer", "company_id": "company123"}

    encoded = base64.b64encode(json.dumps(session_data).encode())

    signer = TimestampSigner("jobconnect-secret-key")

    signed_session = signer.sign(encoded)

    client.cookies.set("session", signed_session.decode())

    return client


# ==================================================
# TEST DATA
# ==================================================

TEST_INTERVIEW_IDS = [
    "TEST_SEARCH_INTERVIEW_001",
    "TEST_SEARCH_INTERVIEW_002",
    "TEST_SEARCH_INTERVIEW_003",
]


def delete_test_data():

    for interview_id in TEST_INTERVIEW_IDS:

        db.collection("interviews").document(interview_id).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_data()

    yield

    delete_test_data()


# ==================================================
# CREATE DATA
# ==================================================


def create_interview_records():

    records = [
        {
            "candidateId": "candidate001",
            "candidateName": "John Tan",
            "position": "Software Developer",
            "stage": "Interview",
            "status": "Scheduled",
            "companyId": "company123",
        },
        {
            "candidateId": "candidate002",
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "stage": "Interview",
            "status": "Completed",
            "companyId": "company123",
        },
        {
            "candidateId": "candidate003",
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "stage": "Technical",
            "status": "Cancelled",
            "companyId": "company123",
        },
    ]

    for index, record in enumerate(records):

        db.collection("interviews").document(TEST_INTERVIEW_IDS[index]).set(record)


# ==================================================
# TEST 1
# SEARCH MATCHING KEYWORD
# ==================================================


def test_search_interview_records_by_keyword(authenticated_client):

    create_interview_records()

    response = authenticated_client.get(
        "/employer/interviews/search", params={"keyword": "Software"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["candidateName"] == "John Tan"


# ==================================================
# TEST 2
# SEARCH NO RESULT
# ==================================================


def test_search_interview_records_with_no_matching_results(authenticated_client):

    create_interview_records()

    response = authenticated_client.get("/employer/interviews/search", params={"keyword": "Doctor"})

    assert response.status_code == 200

    data = response.json()

    assert data == []


# ==================================================
# TEST 3
# CLEAR SEARCH
# ==================================================


def test_clear_interview_search(authenticated_client):

    create_interview_records()

    response = authenticated_client.get(
        "/employer/interviews/search",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    names = [item["candidateName"] for item in data]

    assert "John Tan" in names

    assert "Mary Lee" in names

    assert "Alex Wong" in names
