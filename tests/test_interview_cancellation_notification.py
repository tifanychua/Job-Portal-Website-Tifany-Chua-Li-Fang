from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/interview_cancellation_notification.feature")


# ==========================================
# TEST CLIENT
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


@pytest.fixture
def mock_email(monkeypatch):

    email_context = {"sent": False, "email": None}

    async def fake_send_cancel_email(email, name, position):

        email_context["sent"] = True
        email_context["email"] = email

    monkeypatch.setattr(
        "job_portal_web.backend.interview.send_interview_cancelled_email", fake_send_cancel_email
    )

    return email_context


# ==========================================
# CLEANUP
# ==========================================

TEST_INTERVIEW_ID = "TEST_INTERVIEW_CANCEL_001"


def delete_test_interview():

    db.collection("interviews").document(TEST_INTERVIEW_ID).delete()

    db.collection("application").document("APP001").delete()

    db.collection("job_seeker").document("JS001").delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_interview()

    yield

    delete_test_interview()


# ==========================================
# CREATE TEST DATA
# ==========================================


def create_cancel_test_data():

    # ------------------------------
    # Interview
    # ------------------------------

    db.collection("interviews").document(TEST_INTERVIEW_ID).set(
        {
            "candidateId": "APP001",
            "companyId": "C000001",
            "candidateName": "John Tan",
            "position": "Software Developer",
            "date": "2026-07-30",
            "time": "10:00 AM",
            "duration": "30 minutes",
            "interviewType": "online",
            "interviewer": "HR Manager",
            "meetingLink": "https://meet.google.com/test",
            "status": "Scheduled",
        }
    )

    # ------------------------------
    # Application
    # ------------------------------

    db.collection("application").document("APP001").set({"jobSeekerId": "JS001"})

    # ------------------------------
    # Job Seeker
    # ------------------------------

    db.collection("job_seeker").document("JS001").set(
        {"name": "John Tan", "email": "jobseeker@gmail.com"}
    )

    return TEST_INTERVIEW_ID


# ==========================================
# SCENARIO 1
# ==========================================


@given("the employer has cancelled a scheduled interview")
def employer_cancelled_interview(context):

    context["interview_id"] = create_cancel_test_data()


@when('the interview status is updated to "Cancelled"')
def update_interview_status(client, context, mock_email):

    context["response"] = client.put(f"/api/interviews/{context['interview_id']}/cancel")


@then("the system should send a cancellation email notification to the job seeker")
def verify_email_sent(context, mock_email):

    assert context["response"].status_code == 200

    interview_data = db.collection("interviews").document(context["interview_id"]).get().to_dict()

    assert interview_data["status"] == "Cancelled"

    assert mock_email["sent"] is True

    assert mock_email["email"] == "jobseeker@gmail.com"


# ==========================================
# SCENARIO 2
# ==========================================


@given("the job seeker has received an interview cancellation email")
def received_cancellation_email(context, client, mock_email):

    context["interview_id"] = create_cancel_test_data()

    context["response"] = client.put(f"/api/interviews/{context['interview_id']}/cancel")


@when("the job seeker opens the email")
def open_email():

    pass


@then("the system should display the cancelled interview details and cancellation information")
def verify_cancelled_email_details(context):

    cancelled_interview = (
        db.collection("interviews").document(context["interview_id"]).get().to_dict()
    )

    assert cancelled_interview["status"] == "Cancelled"

    assert cancelled_interview["date"] == "2026-07-30"

    assert cancelled_interview["time"] == "10:00 AM"

    assert cancelled_interview["position"] == "Software Developer"


# ==========================================
# SCENARIO 3
# ==========================================


@given('the interview status is not "Cancelled"')
def interview_not_cancelled(context):

    context["interview_id"] = create_cancel_test_data()


@when("no cancellation action is performed")
def no_cancellation_action():

    pass


@then("the system should not send any cancellation email notification")
def verify_no_email(mock_email):

    assert mock_email["sent"] is False
