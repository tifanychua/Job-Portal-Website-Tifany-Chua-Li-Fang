from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import interview
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/interview_cancellation_notification.feature")


# ==========================================
# CLIENT
# ==========================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==========================================
# CONTEXT
# ==========================================


@pytest.fixture
def context():
    return {}


# ==========================================
# MOCK EMAIL
# ==========================================


@pytest.fixture(autouse=True)
def mock_email(monkeypatch):
    email_context = {
        "sent": False,
        "email": None,
        "name": None,
        "position": None,
    }

    async def fake_send_cancelled_email(email, name, position):
        email_context["sent"] = True
        email_context["email"] = email
        email_context["name"] = name
        email_context["position"] = position

    monkeypatch.setattr(
        interview,
        "send_interview_cancelled_email",
        fake_send_cancelled_email,
    )

    return email_context


# ==========================================
# TEST DATA
# ==========================================


@pytest.fixture
def test_data():
    suffix = uuid4().hex

    data = {
        "interview_id": f"TEST_CANCEL_NOTIFICATION_{suffix}",
        "job_seeker_id": f"JS_CANCEL_{suffix}",
        "company_id": f"COMPANY_CANCEL_{suffix}",
    }

    yield data

    db.collection("interviews").document(data["interview_id"]).delete()
    db.collection("job_seeker").document(data["job_seeker_id"]).delete()
    db.collection("company").document(data["company_id"]).delete()


# ==========================================
# CREATE DATA
# ==========================================


def create_cancel_test_data(test_data):
    interview_id = test_data["interview_id"]
    job_seeker_id = test_data["job_seeker_id"]
    company_id = test_data["company_id"]

    db.collection("job_seeker").document(job_seeker_id).set(
        {
            "name": "John Tan",
            "email": "jobseeker@gmail.com",
        }
    )

    db.collection("company").document(company_id).set(
        {
            "companyName": "ABC Technology",
            "email": "hr@abc.com",
            "address": "Penang",
        }
    )

    db.collection("interviews").document(interview_id).set(
        {
            # The cancel endpoint directly uses candidateId
            # to retrieve the job_seeker document.
            "candidateId": job_seeker_id,
            "companyId": company_id,
            "candidateName": "John Tan",
            "position": "Software Developer",
            "stage": "Technical Interview",
            "date": "2026-07-30",
            "time": "10:00 AM",
            "duration": "30 minutes",
            "interviewType": "online",
            "interviewer": "HR Manager",
            "meetingLink": "https://meet.google.com/test",
            "notes": "",
            "status": "Scheduled",
            "applicantResponse": "Pending",
        }
    )

    return interview_id


# ==========================================
# SCENARIO 1
# ==========================================


@given("the employer has cancelled a scheduled interview")
def employer_cancelled_interview(context, test_data):
    context["interview_id"] = create_cancel_test_data(test_data)


@when('the interview status is updated to "Cancelled"')
def update_status(client, context):
    context["response"] = client.put(f"/api/interviews/{context['interview_id']}/cancel")


@then("the system should send a cancellation email notification to the job seeker")
def verify_email_notification(context, mock_email):
    response = context["response"]

    assert response.status_code == 200
    assert response.json()["message"] == "Interview cancelled successfully"

    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    interview_data = document.to_dict()

    assert interview_data is not None
    assert interview_data["status"] == "Cancelled"
    assert interview_data["applicantResponse"] == "Cancelled"

    assert mock_email["sent"] is True
    assert mock_email["email"] == "jobseeker@gmail.com"
    assert mock_email["name"] == "John Tan"
    assert mock_email["position"] == "Software Developer"


# ==========================================
# SCENARIO 2
# ==========================================


@given("the job seeker has received an interview cancellation email")
def received_email(context, client, test_data):
    context["interview_id"] = create_cancel_test_data(test_data)

    context["response"] = client.put(f"/api/interviews/{context['interview_id']}/cancel")

    assert context["response"].status_code == 200


@when("the job seeker opens the email")
def open_email():
    pass


@then("the system should display the cancelled interview details and cancellation information")
def verify_email_details(context, mock_email):
    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    interview_data = document.to_dict()

    assert interview_data is not None
    assert interview_data["status"] == "Cancelled"
    assert interview_data["date"] == "2026-07-30"
    assert interview_data["time"] == "10:00 AM"
    assert interview_data["position"] == "Software Developer"

    assert mock_email["sent"] is True
    assert mock_email["email"] == "jobseeker@gmail.com"
    assert mock_email["position"] == "Software Developer"


# ==========================================
# SCENARIO 3
# ==========================================


@given('the interview status is not "Cancelled"')
def interview_not_cancelled(context, test_data):
    context["interview_id"] = create_cancel_test_data(test_data)


@when("no cancellation action is performed")
def no_action():
    pass


@then("the system should not send any cancellation email notification")
def verify_no_email(context, mock_email):
    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    interview_data = document.to_dict()

    assert interview_data is not None
    assert interview_data["status"] == "Scheduled"
    assert mock_email["sent"] is False
