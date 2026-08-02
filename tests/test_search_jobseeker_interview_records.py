import base64
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# UNIQUE TEST DATA
# ==================================================


@pytest.fixture
def test_data():
    suffix = uuid4().hex

    data = {
        "company_id": f"TEST_SEARCH_COMPANY_{suffix}",
        "interview_ids": [
            f"TEST_SEARCH_INTERVIEW_1_{suffix}",
            f"TEST_SEARCH_INTERVIEW_2_{suffix}",
            f"TEST_SEARCH_INTERVIEW_3_{suffix}",
        ],
    }

    yield data

    for interview_id in data["interview_ids"]:
        db.collection("interviews").document(interview_id).delete()

    db.collection("company").document(data["company_id"]).delete()


# ==================================================
# AUTHENTICATED CLIENT
# ==================================================


@pytest.fixture
def authenticated_client(client, test_data):
    session_data = {
        "user_type": "employer",
        "company_id": test_data["company_id"],
    }

    encoded_session = base64.b64encode(json.dumps(session_data).encode())

    signer = TimestampSigner("jobconnect-secret-key")
    signed_session = signer.sign(encoded_session)

    client.cookies.set(
        "session",
        signed_session.decode(),
    )

    return client


# ==================================================
# CREATE DATA
# ==================================================


def create_interview_records(test_data):
    company_id = test_data["company_id"]
    interview_ids = test_data["interview_ids"]

    db.collection("company").document(company_id).set(
        {
            "companyName": "Search Test Company",
            "email": "search-test@example.com",
            "status": "Verified",
            "test": True,
        }
    )

    records = [
        {
            "candidateId": f"CANDIDATE_1_{uuid4().hex}",
            "candidateName": "John Tan",
            "position": "Software Developer",
            "stage": "Interview",
            "status": "Scheduled",
            "companyId": company_id,
            "date": "2026-08-10",
            "time": "10:00",
        },
        {
            "candidateId": f"CANDIDATE_2_{uuid4().hex}",
            "candidateName": "Mary Lee",
            "position": "UI Designer",
            "stage": "Interview",
            "status": "Completed",
            "companyId": company_id,
            "date": "2026-08-11",
            "time": "11:00",
        },
        {
            "candidateId": f"CANDIDATE_3_{uuid4().hex}",
            "candidateName": "Alex Wong",
            "position": "Backend Developer",
            "stage": "Technical",
            "status": "Cancelled",
            "companyId": company_id,
            "date": "2026-08-12",
            "time": "14:00",
        },
    ]

    for interview_id, record in zip(
        interview_ids,
        records,
        strict=True,
    ):
        db.collection("interviews").document(interview_id).set(record)

    created_documents = [
        db.collection("interviews").document(interview_id).get() for interview_id in interview_ids
    ]

    assert all(document.exists for document in created_documents)


# ==================================================
# TEST 1: SEARCH MATCHING KEYWORD
# ==================================================


def test_search_interview_records_by_keyword(
    authenticated_client,
    test_data,
):
    create_interview_records(test_data)

    response = authenticated_client.get(
        "/employer/interviews/search",
        params={"keyword": "Software"},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1, data
    assert data[0]["candidateName"] == "John Tan"
    assert data[0]["position"] == "Software Developer"


# ==================================================
# TEST 2: SEARCH NO RESULT
# ==================================================


def test_search_interview_records_with_no_matching_results(
    authenticated_client,
    test_data,
):
    create_interview_records(test_data)

    response = authenticated_client.get(
        "/employer/interviews/search",
        params={"keyword": "Doctor"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == []


# ==================================================
# TEST 3: CLEAR SEARCH
# ==================================================


def test_clear_interview_search(
    authenticated_client,
    test_data,
):
    create_interview_records(test_data)

    response = authenticated_client.get(
        "/employer/interviews/search",
        params={"keyword": ""},
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 3, data

    names = {item["candidateName"] for item in data}

    assert names == {
        "John Tan",
        "Mary Lee",
        "Alex Wong",
    }
