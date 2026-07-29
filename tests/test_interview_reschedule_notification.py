from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend import interview
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/reschedule_interview_notification.feature")


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
# MOCK EMAIL
# ==========================================


@pytest.fixture(autouse=True)
def mock_email(monkeypatch, request):

    request.node.email_context = {"sent": False, "email": None, "date": None, "time": None}

    async def fake_send_reschedule_email(email, name, interview_data, company_address):

        request.node.email_context["sent"] = True

        request.node.email_context["email"] = email

        request.node.email_context["date"] = interview_data.date

        request.node.email_context["time"] = interview_data.time

    monkeypatch.setattr(interview, "send_interview_rescheduled_email", fake_send_reschedule_email)

    return request.node.email_context


# ==========================================
# CLEANUP
# ==========================================

TEST_INTERVIEW_ID = "TEST_RESCHEDULE_INTERVIEW_001"


def delete_test_data():

    db.collection("interviews").document(TEST_INTERVIEW_ID).delete()

    db.collection("application").document("APP001").delete()

    db.collection("job_seeker").document("JS001").delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_data()

    yield

    delete_test_data()


# ==========================================
# CREATE DATA
# ==========================================


def create_scheduled_interview():

    db.collection("interviews").document(TEST_INTERVIEW_ID).set(
        {
            "candidateId": "APP001",
            "companyId": "C000001",
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
        }
    )

    db.collection("application").document("APP001").set({"jobSeekerId": "JS001"})

    db.collection("job_seeker").document("JS001").set(
        {"name": "John Tan", "email": "jobseeker@gmail.com"}
    )

    db.collection("company").document("C000001").set(
        {"companyName": "ABC Technology", "address": "Penang"}
    )

    return TEST_INTERVIEW_ID


# ==========================================
# UPDATE REQUEST
# ==========================================


def update_interview(client, interview_id):

    return client.put(
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


# ==================================================
# SCENARIO 1
# ==================================================


@given("the employer has rescheduled an interview")
def employer_reschedule(context):

    context["interview_id"] = create_scheduled_interview()


@when("the interview schedule is updated")
def update_schedule(client, context):

    context["response"] = update_interview(client, context["interview_id"])


@then(
    "the system should send an email notification to the job seeker with the updated interview details"
)
def verify_email(context, mock_email):

    assert context["response"].status_code == 200

    assert mock_email["sent"] is True

    assert mock_email["email"] == "jobseeker@gmail.com"


# ==================================================
# SCENARIO 2
# ==================================================


@given("the job seeker receives a rescheduled interview notification")
def receive_notification(context):

    context["interview_id"] = create_scheduled_interview()


@when("the job seeker opens the email")
def open_email(client, context):

    context["response"] = update_interview(client, context["interview_id"])


@then("the system should display the new interview date, time, and other relevant details")
def verify_details(context, mock_email):

    assert context["response"].status_code == 200

    assert mock_email["sent"] is True

    assert mock_email["date"] == "2026-08-05"

    assert mock_email["time"] == "2:00 PM"


# ==================================================
# SCENARIO 3
# ==================================================


@given("the interview schedule remains unchanged")
def unchanged_schedule():

    create_scheduled_interview()


@when("no rescheduling action is performed")
def no_action():

    pass


@then("the system should not send any reschedule notification email")
def verify_no_email(mock_email):

    assert mock_email["sent"] is False
