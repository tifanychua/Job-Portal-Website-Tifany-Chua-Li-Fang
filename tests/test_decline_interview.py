from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# LOAD FEATURE FILE
# ==================================================

scenarios("features/decline_interview_invitation.feature")


# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# CONTEXT
# ==================================================


class Context:
    def __init__(self):
        self.interview_id: str | None = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# TEST DATA HELPERS
# ==================================================


def create_test_interview() -> str:
    """
    Create a unique interview document for one test scenario.
    """

    interview_id = f"TEST_DECLINE_{uuid4()}"

    db.collection("interviews").document(interview_id).set(
        {
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
            "status": "Scheduled",
            "applicantResponse": "Pending",
        }
    )

    return interview_id


def delete_test_interview(interview_id: str | None) -> None:
    """
    Delete only the interview created by the current scenario.
    """

    if interview_id:
        db.collection("interviews").document(interview_id).delete()


# ==================================================
# CLEANUP
# ==================================================


@pytest.fixture(autouse=True)
def cleanup(context):
    """
    Clean up the unique interview after every scenario.
    """

    yield

    delete_test_interview(context.interview_id)


# ==================================================
# SCENARIO 1
# ==================================================


@given("the job seeker has received an interview invitation")
def job_seeker_received_invitation(context):
    context.interview_id = create_test_interview()


@when("the job seeker declines the interview")
def job_seeker_declines(client, context):
    assert context.interview_id is not None

    context.response = client.put(f"/api/interviews/{context.interview_id}/decline")


@then('the interview status should be updated to "Declined"')
def verify_declined_status(context):
    assert context.response is not None
    assert context.response.status_code == 200
    assert context.response.json()["message"] == "Interview declined"

    document = db.collection("interviews").document(context.interview_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Declined"
    assert data["applicantResponse"] == "Declined"


# ==================================================
# SCENARIO 2
# ==================================================


@given("the job seeker has declined the interview")
def job_seeker_already_declined(client, context):
    context.interview_id = create_test_interview()

    response = client.put(f"/api/interviews/{context.interview_id}/decline")

    assert response.status_code == 200


@when("the system processes the request")
def system_processes_request(context):
    """
    Read the document directly from Firestore.

    The GET /api/interviews/{interview_id} endpoint requires
    an authenticated session, which is unrelated to this scenario.
    """

    assert context.interview_id is not None

    context.response = db.collection("interviews").document(context.interview_id).get()


@then("the updated interview status should be saved in the database")
def verify_database_status(context):
    document = context.response

    assert document is not None
    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Declined"
    assert data["applicantResponse"] == "Declined"
