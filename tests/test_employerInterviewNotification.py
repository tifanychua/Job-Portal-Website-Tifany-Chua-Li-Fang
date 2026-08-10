"""Acceptance + unit tests for the employer "Interview notifications" story.

In the real backend the events that write a website notification for the
*employer* side of an interview are the candidate's response routes --
PUT /api/interviews/{id}/accept and /decline (job_portal_web.backend.
interview) -- rather than the employer's own create/update routes (those
only notify the candidate). "The interview information is changed" is
exercised here via the candidate accepting the interview, which is the
real trigger for an employer-facing interview notification.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import interview, notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
COMPANY_ID = "COMP001"

scenarios("features/employerInterviewNotification.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "email": "hr@tarumt.com"})
    db.seed(
        "job_seeker",
        JOB_SEEKER_ID,
        {"name": "Jamie Lee", "email": "jamie@example.com"},
    )
    return db


@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(interview, "send_employer_interview_notification", noop)


@pytest.fixture(autouse=True)
def fake_login(monkeypatch, client, fake_db):
    def fake_current_user(request):
        request.session["user_type"] = "employer"
        request.session["company_id"] = COMPANY_ID
        return COMPANY_ID, "employer", {"uid": COMPANY_ID, "companyName": "TARUMT Sdn Bhd"}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)

    # interview.py's employer routes (/employer/interviews, /employer-
    # notifications) read request.session directly rather than going
    # through a mockable getter, so the session cookie needs to already
    # carry user_type=employer/company_id before any of those requests.
    # Priming it via an endpoint that calls _get_current_user
    # unconditionally sets that cookie on the shared TestClient.
    client.post("/api/notifications/mark-all-read")


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_interview(fake_db, interview_id, *, position="Backend Engineer"):
    fake_db.seed(
        "interviews",
        interview_id,
        {
            "candidateId": JOB_SEEKER_ID,
            "companyId": COMPANY_ID,
            "candidateName": "Jamie Lee",
            "position": position,
            "stage": "Technical Interview",
            "date": "2026-08-20",
            "time": "10:00",
            "duration": "60 Minutes",
            "interviewType": "online",
            "interviewer": "Alex Tan",
            "meetingLink": "https://meet.example.com/abc",
            "notes": "",
            "status": "Scheduled",
        },
    )


def employer_interview_notifications(fake_db):
    return [
        d.to_dict()
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == COMPANY_ID and d.to_dict().get("type") == "interview"
    ]


def notification_id_for_employer(fake_db):
    for doc in fake_db.collection("notification").stream():
        data = doc.to_dict()
        if data.get("user_id") == COMPANY_ID and data.get("type") == "interview":
            return doc.id
    raise AssertionError("no employer interview notification found")


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.interview_id = None
        self.response = None
        self.notification_id = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Receive interview notification
# ==================================================


@given("the employer has scheduled an interview with a candidate")
def given_scheduled_interview(fake_db, context):
    context.interview_id = "INT_EMP_1"
    seed_interview(fake_db, context.interview_id)


@when("the interview information is changed")
def interview_information_changed(client, context):
    context.response = client.put(f"/api/interviews/{context.interview_id}/accept")
    assert context.response.status_code == 200


@then("the system should display a notification to the employer regarding the interview update")
def assert_employer_notification_created(fake_db, context):
    notifs = employer_interview_notifications(fake_db)
    assert len(notifs) == 1
    assert notifs[0]["is_read"] is False
    assert "accepted" in notifs[0]["title"].lower()


# ==================================================
# Scenario: View interview notification details
# ==================================================


@given("the employer has received an interview notification")
def given_received_interview_notification(fake_db, client, context):
    context.interview_id = "INT_EMP_2"
    seed_interview(fake_db, context.interview_id, position="Cloud Engineer")
    response = client.put(f"/api/interviews/{context.interview_id}/accept")
    assert response.status_code == 200


@when("the employer clicks on the notification")
def employer_clicks_notification(fake_db, client, context):
    notif_id = notification_id_for_employer(fake_db)
    context.notification_id = notif_id
    link = fake_db.get("notification", notif_id)["link"]
    context.response = client.get(link)


@then(
    "the system should display the interview details including candidate information, interview date, time, and status"
)
def assert_interview_details_available(client, context):
    assert context.response.status_code == 200

    interviews = client.get("/employer/interviews").json()
    match = next(i for i in interviews if i["id"] == context.interview_id)

    assert match["candidateName"] == "Jamie Lee"
    assert match["date"] == "2026-08-20"
    assert match["time"] == "10:00"
    assert match["status"] == "Accepted"


# ==================================================
# Scenario: Mark interview notification as read
# ==================================================


@given("the employer has unread interview notifications")
def given_unread_interview_notifications(fake_db, client, context):
    context.interview_id = "INT_EMP_3"
    seed_interview(fake_db, context.interview_id)
    response = client.put(f"/api/interviews/{context.interview_id}/accept")
    assert response.status_code == 200


@when("the employer views the notification")
def employer_views_notification(fake_db, client, context):
    notif_id = notification_id_for_employer(fake_db)
    context.notification_id = notif_id
    context.response = client.post(f"/api/notifications/{notif_id}/read")


@then("the system should mark the notification as read and update the notification count")
def assert_marked_read_and_count(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.notification_id)["is_read"] is True


# ==================================================
# Scenario: No interview notifications available
# ==================================================


@given("the employer has no interview updates")
def given_no_interview_updates(context):
    pass


@when("the employer accesses the notification section")
def employer_accesses_notification_section(client, context):
    context.response = client.get("/employer-notifications")


@then(
    "the system should display a message indicating that no interview notifications are available"
)
def assert_no_interview_notifications_message(client, context):
    assert context.response.status_code == 200
    assert "No notifications yet" in context.response.text
    assert client.get("/employer/interviews").json() == []
