"""Acceptance + unit tests for the employer "New application notification" story.

POST /jobs/{job_id}/apply (job_portal_web.backend.job_apply) writes a
"notification" document for the employer as a side effect. Note: the real
route links the notification to "/applications" (the shared applications
list), not a per-applicant detail page, so "View new application
notification details" is tested against that actual link target.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import job_apply, notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
# /applications (routes/employerApplication.py) hard-codes company_id to
# "C000001" whenever PYTEST_CURRENT_TEST is set (its test-mode login
# bypass), so the seeded company/job must use that same id to line up.
COMPANY_ID = "C000001"

scenarios("features/employerNewApplicationNotification.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "verified": True})
    return db


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):
    def fake_current_job_seeker(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID, {"uid": JOB_SEEKER_ID, "name": "Jamie Lee"}

    def fake_current_user(request):
        request.session["user_type"] = "employer"
        request.session["company_id"] = COMPANY_ID
        return COMPANY_ID, "employer", {"uid": COMPANY_ID, "companyName": "TARUMT Sdn Bhd"}

    monkeypatch.setattr(job_apply, "_get_current_job_seeker", fake_current_job_seeker)
    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_job(fake_db, job_id, *, title="Software Engineer"):
    fake_db.seed(
        "job_list",
        job_id,
        {
            "job_title": title,
            "company_id": COMPANY_ID,
            "location": "Kuala Lumpur",
            "status": "Active",
        },
    )


def submit_application(client, job_id):
    return client.post(f"/jobs/{job_id}/apply", data={"cover_letter": "I'd love to join."})


def employer_notifications(fake_db):
    return [
        d.to_dict()
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == COMPANY_ID
    ]


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.job_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Receive notification when a new application is submitted
# ==================================================


@given("the employer has posted an active job vacancy")
def given_active_vacancy(fake_db, context):
    context.job_id = "JOB_APPLY_1"
    seed_job(fake_db, context.job_id, title="Backend Developer")


@when("a job seeker submits an application for the vacancy")
def submit_application_for_vacancy(client, context):
    context.response = submit_application(client, context.job_id)
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True


@then(
    "the system should display a notification to the employer indicating a new application has been received"
)
def assert_employer_notification_created(fake_db):
    notifs = employer_notifications(fake_db)
    assert len(notifs) == 1
    notif = notifs[0]
    assert notif["is_read"] is False
    assert notif["type"] == "application"
    assert "Jamie Lee" in notif["message"]
    assert "Backend Developer" in notif["message"]


# ==================================================
# Scenario: View new application notification details
# ==================================================


@given("the employer has received a new application notification")
def given_received_new_application_notification(fake_db, client, context):
    context.job_id = "JOB_APPLY_2"
    seed_job(fake_db, context.job_id, title="Mobile Developer")
    response = submit_application(client, context.job_id)
    assert response.status_code == 200


@when("the employer clicks on the notification")
def employer_clicks_notification(fake_db, client, context):
    notif = employer_notifications(fake_db)[0]
    context.response = client.get(notif["link"])


@then("the system should redirect the employer to the applications page for that applicant")
def assert_redirected_to_applications(context):
    assert context.response.status_code == 200
    assert "Mobile Developer" in context.response.text


# ==================================================
# Scenario: Notification count updates after viewing application
# ==================================================


@given("the employer has unread application notifications")
def given_unread_application_notifications(fake_db, client, context):
    context.job_id = "JOB_APPLY_3"
    seed_job(fake_db, context.job_id, title="QA Engineer")
    response = submit_application(client, context.job_id)
    assert response.status_code == 200


@when("the employer views the new application")
def employer_views_new_application(fake_db, client, context):
    context.notification_id = notif_id = [
        d.id
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == COMPANY_ID
    ][0]
    context.response = client.post(f"/api/notifications/{notif_id}/read")


@then("the system should mark the notification as read and update the notification count")
def assert_marked_read_and_count_updated(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.notification_id)["is_read"] is True
