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

scenarios("features/reschedule_interview_notification.feature")


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
        "date": None,
        "time": None,
        "company_address": None,
    }

    async def fake_send_reschedule_email(
        email,
        name,
        interview_data,
        company_address,
    ):
        email_context["sent"] = True
        email_context["email"] = email
        email_context["name"] = name
        email_context["date"] = interview_data.date
        email_context["time"] = interview_data.time
        email_context["company_address"] = company_address

    monkeypatch.setattr(
        interview,
        "send_interview_rescheduled_email",
        fake_send_reschedule_email,
    )

    return email_context


# ==========================================
# UNIQUE TEST DATA
# ==========================================


@pytest.fixture
def test_data():
    suffix = uuid4().hex

    data = {
        "interview_id": f"TEST_RESCHEDULE_{suffix}",
        "application_id": f"APP_{suffix}",
        "job_seeker_id": f"JS_{suffix}",
        "company_id": f"COMPANY_{suffix}",
    }

    yield data

    db.collection("interviews").document(data["interview_id"]).delete()

    db.collection("application").document(data["application_id"]).delete()

    db.collection("job_seeker").document(data["job_seeker_id"]).delete()

    db.collection("company").document(data["company_id"]).delete()


# ==========================================
# CREATE TEST DATA
# ==========================================


def create_scheduled_interview(test_data):
    interview_id = test_data["interview_id"]
    application_id = test_data["application_id"]
    job_seeker_id = test_data["job_seeker_id"]
    company_id = test_data["company_id"]

    db.collection("application").document(application_id).set(
        {
            "jobSeekerId": job_seeker_id,
        }
    )

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
            "candidateId": application_id,
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

    interview_document = db.collection("interviews").document(interview_id).get()

    application_document = db.collection("application").document(application_id).get()

    job_seeker_document = db.collection("job_seeker").document(job_seeker_id).get()

    company_document = db.collection("company").document(company_id).get()

    assert interview_document.exists
    assert application_document.exists
    assert job_seeker_document.exists
    assert company_document.exists

    return interview_id


# ==========================================
# UPDATE REQUEST
# ==========================================


def update_interview(client, interview_id):
    document = db.collection("interviews").document(interview_id).get()

    assert document.exists, f"Interview {interview_id} does not exist before update"

    existing_data = document.to_dict()

    assert existing_data is not None

    response = client.put(
        f"/api/interviews/{interview_id}",
        json={
            "stage": "Technical Interview",
            "date": "2026-08-05",
            "time": "2:00 PM",
            "duration": "60 Minutes",
            "interviewType": "online",
            "interviewer": "HR Manager",
            "meetingLink": "https://meet.google.com/new",
            "notes": "Updated schedule",
            "status": "Scheduled",
        },
    )

    assert (
        response.status_code == 200
    ), f"Update failed for {interview_id}: {response.status_code} {response.text}"

    return response


# ==================================================
# SCENARIO 1
# ==================================================


@given("the employer has rescheduled an interview")
def employer_reschedule(context, test_data):
    context["interview_id"] = create_scheduled_interview(test_data)


@when("the interview schedule is updated")
def update_schedule(client, context):
    context["response"] = update_interview(
        client,
        context["interview_id"],
    )


@then(
    "the system should send an email notification to the job seeker "
    "with the updated interview details"
)
def verify_email(context, mock_email):
    response = context["response"]

    assert response.status_code == 200
    assert response.json()["message"] == ("Interview updated successfully")

    assert mock_email["sent"] is True
    assert mock_email["email"] == "jobseeker@gmail.com"
    assert mock_email["name"] == "John Tan"
    assert mock_email["date"] == "2026-08-05"
    assert mock_email["time"] == "2:00 PM"
    assert mock_email["company_address"] == "Penang"

    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Rescheduled"
    assert data["applicantResponse"] == "Pending"
    assert data["date"] == "2026-08-05"
    assert data["time"] == "2:00 PM"


# ==================================================
# SCENARIO 2
# ==================================================


@given("the job seeker receives a rescheduled interview notification")
def receive_notification(context, test_data):
    context["interview_id"] = create_scheduled_interview(test_data)


@when("the job seeker opens the email")
def open_email(client, context):
    context["response"] = update_interview(
        client,
        context["interview_id"],
    )


@then("the system should display the new interview date, time, and other relevant details")
def verify_details(context, mock_email):
    response = context["response"]

    assert response.status_code == 200

    assert mock_email["sent"] is True
    assert mock_email["email"] == "jobseeker@gmail.com"
    assert mock_email["date"] == "2026-08-05"
    assert mock_email["time"] == "2:00 PM"
    assert mock_email["company_address"] == "Penang"

    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["date"] == "2026-08-05"
    assert data["time"] == "2:00 PM"
    assert data["meetingLink"] == ("https://meet.google.com/new")
    assert data["notes"] == "Updated schedule"


# ==================================================
# SCENARIO 3
# ==================================================


@given("the interview schedule remains unchanged")
def unchanged_schedule(context, test_data):
    context["interview_id"] = create_scheduled_interview(test_data)


@when("no rescheduling action is performed")
def no_action():
    pass


@then("the system should not send any reschedule notification email")
def verify_no_email(context, mock_email):
    assert mock_email["sent"] is False

    document = db.collection("interviews").document(context["interview_id"]).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["status"] == "Scheduled"
    assert data["date"] == "2026-07-30"
    assert data["time"] == "10:00 AM"
