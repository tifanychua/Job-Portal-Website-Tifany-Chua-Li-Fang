"""Acceptance + unit tests for the employer "Delete notification" story.
Mirrors test_jobSeekerDeleteNotification.py against the shared
DELETE /api/notifications/{id} route with an employer session.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import notifications
from job_portal_web.backend.main import app

COMPANY_ID = "C000001"
OTHER_COMPANY_ID = "C000002"
NOTIF_PAGE = "/employer-notifications"

scenarios("features/employerDeleteNotification.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    return db


@pytest.fixture(autouse=True)
def fake_login(monkeypatch, client, fake_db):
    def fake_current_user(request):
        request.session["user_type"] = "employer"
        request.session["company_id"] = COMPANY_ID
        return COMPANY_ID, "employer", {"uid": COMPANY_ID, "companyName": "Test Co"}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)

    # /employer-notifications checks request.session directly *before*
    # calling _get_current_user, so the session cookie needs to already
    # carry user_type=employer. Priming it via an endpoint that calls
    # _get_current_user unconditionally (and works with zero data) sets
    # that cookie on the shared TestClient for every request that follows.
    client.post("/api/notifications/mark-all-read")


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_notification(fake_db, doc_id, *, owner=COMPANY_ID, is_read=False, title="Notice"):
    fake_db.seed(
        "notification",
        doc_id,
        {
            "user_id": owner,
            "user_type": "employer",
            "is_read": is_read,
            "type": "application",
            "title": title,
            "message": "msg",
            "link": "",
            "created_at": datetime.now(timezone.utc),
        },
    )


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.notification_id = None
        self.other_id = None
        self.missing_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Delete a notification successfully
# ==================================================


@given("the employer is viewing the notification list")
def viewing_notification_list(fake_db, client, context):
    context.notification_id = "N_DELETE_ME"
    seed_notification(fake_db, context.notification_id)
    page = client.get(NOTIF_PAGE).text
    assert f'data-id="{context.notification_id}"' in page


@given("the notification belongs to the employer")
def notification_belongs_to_employer(fake_db, context):
    assert fake_db.get("notification", context.notification_id)["user_id"] == COMPANY_ID


@when("the employer selects the delete option for the notification")
def select_delete_option(context):
    context.confirm_pending = True


@when("confirms the deletion")
def confirm_deletion(client, context):
    context.response = client.delete(f"/api/notifications/{context.notification_id}")


@then("the system should remove the notification from the notification list")
def assert_removed(client, context):
    assert context.response.status_code == 200
    page = client.get(NOTIF_PAGE).text
    assert f'data-id="{context.notification_id}"' not in page


@then("display a notification-deleted success message")
def assert_success_message(context):
    body = context.response.json()
    assert body["success"] is True


# ==================================================
# Scenario: Cancel notification deletion
# ==================================================


@given("the employer has selected the delete option for a notification")
def selected_delete_option(fake_db, context):
    context.notification_id = "N_CANCEL_DELETE"
    seed_notification(fake_db, context.notification_id)


@given("the confirmation message is displayed")
def confirmation_message_displayed(context):
    context.confirm_pending = True


@when("the employer cancels the deletion")
def cancel_deletion(context):
    context.confirm_pending = False


@then("the system should not delete the notification")
def assert_not_deleted(fake_db, context):
    assert fake_db.exists("notification", context.notification_id)


@then("the notification should remain in the notification list")
def assert_remains_in_list(client, context):
    page = client.get(NOTIF_PAGE).text
    assert f'data-id="{context.notification_id}"' in page


# ==================================================
# Scenario: Deleted notification remains deleted after refresh
# ==================================================


@given("the employer has successfully deleted a notification")
def successfully_deleted_notification(fake_db, client, context):
    context.notification_id = "N_GONE"
    seed_notification(fake_db, context.notification_id)
    response = client.delete(f"/api/notifications/{context.notification_id}")
    assert response.status_code == 200


@when("the employer refreshes or revisits the notification page")
def refresh_or_revisit(client, context):
    context.response = client.get(NOTIF_PAGE)


@then("the deleted notification should not appear in the notification list")
def assert_still_gone(context):
    assert context.notification_id not in context.response.text


# ==================================================
# Scenario: Delete an unread notification
# ==================================================


@given("the employer has an unread notification")
def has_unread_notification(fake_db, context):
    context.notification_id = "N_UNREAD_DELETE"
    seed_notification(fake_db, context.notification_id, is_read=False)


@when("the employer deletes the unread notification")
def delete_unread_notification(client, context):
    context.response = client.delete(f"/api/notifications/{context.notification_id}")


@then("the notification should be removed from the notification list")
def assert_unread_removed(client, context):
    page = client.get(NOTIF_PAGE).text
    assert f'data-id="{context.notification_id}"' not in page


@then("the unread notification count should decrease by one")
def assert_unread_count_decreased(fake_db, context):
    remaining_unread = [
        d
        for d in fake_db.collection("notification").stream()
        if d.to_dict().get("user_id") == COMPANY_ID and not d.to_dict().get("is_read")
    ]
    assert remaining_unread == []


# ==================================================
# Scenario: Prevent deletion of another employer's notification
# ==================================================


@given("a notification belongs to another employer")
def notification_belongs_to_other(fake_db, context):
    context.other_id = "N_OTHER_OWNER"
    seed_notification(fake_db, context.other_id, owner=OTHER_COMPANY_ID)


@when("the employer attempts to delete that notification")
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


@when("the employer attempts to delete a notification")
def attempt_delete_nonexistent(fake_db, context):
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
