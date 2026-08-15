"""Acceptance + unit tests for the job-seeker "Delete notification" story.

The Delete button on notifications.html calls
`DELETE /api/notifications/{id}` via fetch and, on success, removes the row
from the DOM and shows a toast; on failure it shows `alert("Could not delete
this notification. Please try again.")` (see notifications.html). These
tests exercise the real `job_portal_web.backend.notifications` DELETE route
against an in-memory fake Firestore.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fakes import FakeFirestore, patch_db_everywhere
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
OTHER_JOB_SEEKER_ID = "J000002"

scenarios("features/jobSeekerDeleteNotification.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    return db


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):
    def fake_current_user(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID, "job_seeker", {"uid": JOB_SEEKER_ID, "full_name": "Test Seeker"}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_notification(fake_db, doc_id, *, owner=JOB_SEEKER_ID, is_read=False, title="Notice"):
    fake_db.seed(
        "notification",
        doc_id,
        {
            "user_id": owner,
            "user_type": "job_seeker",
            "is_read": is_read,
            "type": "system",
            "title": title,
            "message": "msg",
            "link": "",
            "created_at": datetime.now(UTC),
        },
    )


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.notification_id = None
        self.other_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Delete a notification successfully
# ==================================================


@given("the job seeker is viewing the notification list")
def viewing_notification_list(fake_db, client, context):
    context.notification_id = "N_DELETE_ME"
    seed_notification(fake_db, context.notification_id)
    page = client.get("/notifications").text
    assert f'data-id="{context.notification_id}"' in page


@given("the notification belongs to the job seeker")
def notification_belongs_to_seeker(fake_db, context):
    assert fake_db.get("notification", context.notification_id)["user_id"] == JOB_SEEKER_ID


@when("the job seeker selects the delete option for the notification")
def select_delete_option(context):
    # Selecting "delete" just opens the confirmation dialog client-side;
    # nothing is sent to the server until the user confirms.
    context.confirm_pending = True


@when("confirms the deletion")
def confirm_deletion(client, context):
    context.response = client.delete(f"/api/notifications/{context.notification_id}")


@then("the system should remove the notification from the notification list")
def assert_removed(client, context):
    assert context.response.status_code == 200
    page = client.get("/notifications").text
    assert f'data-id="{context.notification_id}"' not in page


@then("display a notification-deleted success message")
def assert_success_message(context):
    body = context.response.json()
    assert body["success"] is True


# ==================================================
# Scenario: Cancel notification deletion
# ==================================================


@given("the job seeker has selected the delete option for a notification")
def selected_delete_option(fake_db, context):
    context.notification_id = "N_CANCEL_DELETE"
    seed_notification(fake_db, context.notification_id)


@given("the confirmation message is displayed")
def confirmation_message_displayed(context):
    context.confirm_pending = True


@when("the job seeker cancels the deletion")
def cancel_deletion(context):
    # Cancelling means the DELETE request is never issued.
    context.confirm_pending = False


@then("the system should not delete the notification")
def assert_not_deleted(fake_db, context):
    assert fake_db.exists("notification", context.notification_id)


@then("the notification should remain in the notification list")
def assert_remains_in_list(client, context):
    page = client.get("/notifications").text
    assert f'data-id="{context.notification_id}"' in page


# ==================================================
# Scenario: Deleted notification remains deleted after refresh
# ==================================================


@given("the job seeker has successfully deleted a notification")
def successfully_deleted_notification(fake_db, client, context):
    context.notification_id = "N_GONE"
    seed_notification(fake_db, context.notification_id)
    response = client.delete(f"/api/notifications/{context.notification_id}")
    assert response.status_code == 200


@when("the job seeker refreshes or revisits the notification page")
def refresh_or_revisit(client, context):
    context.response = client.get("/notifications")


@then("the deleted notification should not appear in the notification list")
def assert_still_gone(context):
    assert context.notification_id not in context.response.text


# ==================================================
# Scenario: Delete an unread notification
# ==================================================


@given("the job seeker has an unread notification")
def has_unread_notification(fake_db, context):
    context.notification_id = "N_UNREAD_DELETE"
    seed_notification(fake_db, context.notification_id, is_read=False)


@when("the job seeker deletes the unread notification")
def delete_unread_notification(client, context):
    context.response = client.delete(f"/api/notifications/{context.notification_id}")


@then("the notification should be removed from the notification list")
def assert_unread_removed(client, context):
    page = client.get("/notifications").text
    assert f'data-id="{context.notification_id}"' not in page


@then("the unread notification count should decrease by one")
def assert_unread_count_decreased(fake_db, context):
    # Only the one seeded (now-deleted) unread notification existed, so the
    # count for this job seeker should be back to zero.
    remaining_unread = [
        d
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == JOB_SEEKER_ID and not d.to_dict().get("is_read")
    ]
    assert remaining_unread == []


# ==================================================
# Scenario: Prevent deletion of another job seeker's notification
# ==================================================


@given("a notification belongs to another job seeker")
def notification_belongs_to_other(fake_db, context):
    context.other_id = "N_OTHER_OWNER"
    seed_notification(fake_db, context.other_id, owner=OTHER_JOB_SEEKER_ID)


@when("the current job seeker attempts to delete that notification")
def attempt_delete_other(client, context):
    context.response = client.delete(f"/api/notifications/{context.other_id}")


@then("the system should reject the request")
def assert_rejected(context):
    assert context.response.status_code == 404


@then("the notification should not be deleted")
def assert_other_not_deleted(fake_db, context):
    assert fake_db.exists("notification", context.other_id)


# ==================================================
# Scenario: Notification deletion fails
# ==================================================


@when("the job seeker attempts to delete a notification")
def attempt_delete_nonexistent(fake_db, context):
    # A notification that no longer exists server-side (e.g. already
    # removed elsewhere) represents a failed deletion attempt. Keep a real,
    # untouched notification around too so "remains in the list" is
    # meaningful (reuses the same context.notification_id the Cancel
    # scenario's shared @then step already checks).
    context.missing_id = "N_ALREADY_GONE"
    context.notification_id = "N_STILL_HERE"
    seed_notification(fake_db, context.notification_id)


@when("the deletion request fails")
def deletion_request_fails(client, context):
    context.response = client.delete(f"/api/notifications/{context.missing_id}")


@then("the system should display an appropriate error message")
def assert_error_message(context):
    assert context.response.status_code == 404
    assert "detail" in context.response.json()
