"""Acceptance + unit tests for the job-seeker "Interview status update
notification" story.

PUT /api/interviews/{id} (job_portal_web.backend.interview.update_interview)
is the route an employer uses to change/reschedule an interview; it writes a
"notification" document for the candidate as a side effect and (best-effort,
wrapped in try/except in the real code) sends a reschedule email. The email
send is monkeypatched out here so tests run fully offline/deterministically.
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

scenarios("features/interviewStatusNotification.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "address": "Penang"})
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

    monkeypatch.setattr(interview, "send_interview_rescheduled_email", noop)
    monkeypatch.setattr(interview, "send_interview_email", noop)
    monkeypatch.setattr(interview, "send_interview_cancelled_email", noop)


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):
    def fake_current_user(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID, "job_seeker", {"uid": JOB_SEEKER_ID, "full_name": "Jamie Lee"}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_interview(fake_db, interview_id, *, position="Backend Engineer", status="Scheduled"):
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
            "status": status,
        },
    )


def interview_notifications(fake_db):
    return [
        d.to_dict()
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == JOB_SEEKER_ID and d.to_dict().get("type") == "interview"
    ]


def notification_id_for(fake_db, predicate):
    for doc in fake_db.collection("notification").stream():
        if predicate(doc.to_dict()):
            return doc.id
    raise AssertionError("matching notification not found")


UPDATE_PAYLOAD = {
    "stage": "Final Interview",
    "date": "2026-08-25",
    "time": "14:00",
    "duration": "45 Minutes",
    "interviewType": "online",
    "interviewer": "Alex Tan",
    "meetingLink": "https://meet.example.com/xyz",
    "notes": "Bring portfolio",
}


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
# Scenario: Receive notification when interview status is updated
# ==================================================


@given("the job seeker has an ongoing interview process")
def given_ongoing_interview(fake_db, context):
    context.interview_id = "INT_ONGOING"
    seed_interview(fake_db, context.interview_id)


@when("the employer updates the interview status")
def employer_updates_interview_status(client, context):
    context.response = client.put(f"/api/interviews/{context.interview_id}", json=UPDATE_PAYLOAD)
    assert context.response.status_code == 200


@then(
    "the system should display a notification to the job seeker indicating the updated interview status"
)
def assert_status_notification_created(fake_db, context):
    notifs = interview_notifications(fake_db)
    assert len(notifs) == 1
    assert notifs[0]["is_read"] is False
    assert "rescheduled" in notifs[0]["title"].lower()
    assert notifs[0]["link"] == f"/my_interviews/detail/{context.interview_id}"


# ==================================================
# Scenario: View interview status notification details
# ==================================================


@given("the job seeker has received an interview status notification")
def given_received_status_notification(fake_db, client, context):
    context.interview_id = "INT_DETAILS"
    seed_interview(fake_db, context.interview_id, position="Cloud Engineer")
    response = client.put(f"/api/interviews/{context.interview_id}", json=UPDATE_PAYLOAD)
    assert response.status_code == 200


@when("the job seeker clicks on the notification")
def click_interview_notification(fake_db, client, context):
    notif_id = notification_id_for(
        fake_db, lambda n: n.get("user_id") == JOB_SEEKER_ID and n.get("type") == "interview"
    )
    context.notification_id = notif_id
    link = fake_db.get("notification", notif_id)["link"]
    context.response = client.get(link)


@then(
    "the system should display the interview details including company name, job position, interview date, and updated status"
)
def assert_interview_details_available(client, context):
    # The detail page itself is client-rendered; the data it fetches
    # (GET /api/applicant/interviews) is what carries company name,
    # position, date and status -- check that contract directly.
    assert context.response.status_code == 200

    interviews = client.get("/api/applicant/interviews").json()
    match = next(i for i in interviews if i["id"] == context.interview_id)

    assert match["companyName"] == "TARUMT Sdn Bhd"
    assert match["position"] == "Cloud Engineer"
    assert match["date"] == UPDATE_PAYLOAD["date"]
    assert match["status"] == "Rescheduled"


# ==================================================
# Scenario: Mark interview status notification as read
# ==================================================


@given("the job seeker has unread interview status notifications")
def given_unread_status_notifications(fake_db, client, context):
    context.interview_id = "INT_MARK_READ"
    seed_interview(fake_db, context.interview_id)
    response = client.put(f"/api/interviews/{context.interview_id}", json=UPDATE_PAYLOAD)
    assert response.status_code == 200


@when("the job seeker views the notification")
def view_interview_notification(fake_db, client, context):
    notif_id = notification_id_for(
        fake_db, lambda n: n.get("user_id") == JOB_SEEKER_ID and n.get("type") == "interview"
    )
    context.notification_id = notif_id
    context.response = client.post(f"/api/notifications/{notif_id}/read")


@then("the system should mark the notification as read and update the notification count")
def assert_marked_read_and_count(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.notification_id)["is_read"] is True


# ==================================================
# Scenario: No interview status updates available
# ==================================================


@given("the job seeker has no interview status updates")
def given_no_interview_updates(context):
    pass


@when("the job seeker accesses the notification section")
def access_notification_section(client, context):
    context.response = client.get("/notifications")


@then("the system should display a message indicating that no interview updates are available")
def assert_no_interview_updates_message(client, context):
    assert context.response.status_code == 200
    assert "No notifications yet" in context.response.text
    assert client.get("/api/applicant/interviews").json() == []
