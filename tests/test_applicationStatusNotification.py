"""Acceptance + unit tests for the job-seeker "Application status change
notification" story.

PUT /application/{id}/status (routes/employerApplication.py) writes a
"notification" document for the applicant as a side effect. These tests
drive that real route and then the job-seeker notifications routes
(job_portal_web.backend.notifications) against an in-memory fake Firestore.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import job_application, notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
COMPANY_ID = "COMP001"

scenarios("features/applicationStatusNotification.feature")


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
        return JOB_SEEKER_ID, {"uid": JOB_SEEKER_ID, "full_name": "Test Seeker"}

    def fake_current_user(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID, "job_seeker", {"uid": JOB_SEEKER_ID, "full_name": "Test Seeker"}

    monkeypatch.setattr(job_application, "_get_current_job_seeker", fake_current_job_seeker)
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
        {"job_title": title, "company_id": COMPANY_ID},
    )


def seed_application(fake_db, app_id, job_id, *, status="Submitted"):
    fake_db.seed(
        "application",
        app_id,
        {
            "job_id": job_id,
            "job_seeker_id": JOB_SEEKER_ID,
            "status": status,
            "created_at": datetime.now(timezone.utc),
            "updated_on": datetime.now(timezone.utc),
        },
    )


def notification_for_application(fake_db, application_id):
    return [
        d.to_dict()
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("link") == f"/application/{application_id}"
    ]


def notification_id_for_application(fake_db, application_id):
    for doc in fake_db.collection("notification").stream():
        if doc.to_dict().get("link") == f"/application/{application_id}":
            return doc.id
    raise AssertionError("no notification found for application")


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.application_id = None
        self.job_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Receive notification when application status is updated
# ==================================================


@given("the job seeker has submitted a job application")
def given_submitted_application(fake_db, context):
    context.job_id = "JOB_NOTIF_1"
    context.application_id = "APP_NOTIF_1"
    seed_job(fake_db, context.job_id, title="Backend Developer")
    seed_application(fake_db, context.application_id, context.job_id)


@when("the employer updates the application status")
def employer_updates_status(client, context):
    context.response = client.put(
        f"/application/{context.application_id}/status", json={"status": "shortlisted"}
    )
    assert context.response.status_code == 200


@then(
    "the system should display a notification to the job seeker indicating the updated application status"
)
def assert_notification_created(fake_db, context):
    notifs = notification_for_application(fake_db, context.application_id)
    assert len(notifs) == 1
    notif = notifs[0]
    assert notif["user_id"] == JOB_SEEKER_ID
    assert notif["is_read"] is False
    assert "shortlisted" in notif["message"].lower()


# ==================================================
# Scenario: View application status notification details
# ==================================================


@given("the job seeker has received an application status notification")
def given_received_notification(fake_db, client, context):
    context.job_id = "JOB_NOTIF_2"
    context.application_id = "APP_NOTIF_2"
    seed_job(fake_db, context.job_id, title="Mobile Developer")
    seed_application(fake_db, context.application_id, context.job_id)
    response = client.put(
        f"/application/{context.application_id}/status", json={"status": "offered"}
    )
    assert response.status_code == 200


@when("the job seeker clicks on the notification")
def click_notification(fake_db, client, context):
    notif_id = notification_id_for_application(fake_db, context.application_id)
    link = fake_db.get("notification", notif_id)["link"]
    context.response = client.get(link)


@then(
    "the system should redirect the job seeker to the application details page showing the updated status"
)
def assert_redirected_to_details(context):
    assert context.response.status_code == 200
    assert "Offered" in context.response.text


# ==================================================
# Scenario: Mark application status notification as read
# ==================================================


@given("the job seeker has unread application status notifications")
def given_unread_status_notifications(fake_db, context):
    context.job_id = "JOB_NOTIF_3"
    context.application_id = "APP_NOTIF_3"
    seed_job(fake_db, context.job_id, title="QA Engineer")
    seed_application(fake_db, context.application_id, context.job_id)


@when("the job seeker views the notification")
def view_the_notification(fake_db, client, context):
    # Triggers the status change (and the notification it creates), then
    # the job seeker opens it, which marks it read.
    client.put(f"/application/{context.application_id}/status", json={"status": "rejected"})
    notif_id = notification_id_for_application(fake_db, context.application_id)
    context.notification_id = notif_id
    context.response = client.post(f"/api/notifications/{notif_id}/read")


@then("the system should mark the notification as read and update the notification count")
def assert_marked_read_and_count_updated(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.notification_id)["is_read"] is True
