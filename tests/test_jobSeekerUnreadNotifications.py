"""Acceptance + unit tests for the job-seeker "Unread notifications" story.

The All/Unread tabs on notifications.html are filtered client-side by JS
based on the `data-read="true|false"` attribute the server renders on each
`.notif-item`, and the "Unread" tab badge count comes straight from the
server-computed `unread_count`. These tests exercise the real FastAPI routes
in job_portal_web.backend.notifications against an in-memory fake Firestore
(see tests/fakes.py) and assert on that server-rendered data contract, since
that is what the client-side tab filtering depends on.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fakes import FakeFirestore, patch_db_everywhere
from fastapi.testclient import TestClient
from html_helpers import item_block, tab_count
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"

scenarios("features/jobSeekerUnreadNotifications.feature")


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


def seed_notification(fake_db, doc_id, *, is_read, minutes_ago=0, title="Notice", message="msg"):
    fake_db.seed(
        "notification",
        doc_id,
        {
            "user_id": JOB_SEEKER_ID,
            "user_type": "job_seeker",
            "is_read": is_read,
            "type": "system",
            "title": title,
            "message": message,
            "link": "",
            "created_at": datetime.now(UTC),
        },
    )


def notif_block(page_html: str, doc_id: str) -> str:
    return item_block(page_html, doc_id, item_class="notif-item")


def unread_tab_count(page_html: str) -> int:
    return tab_count(page_html, "unreadTabCount")


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.unread_id = None
        self.read_id = None
        self.count_before = None
        self.count_after = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: View all notifications
# ==================================================


@given("the job seeker has both read and unread notifications")
def given_mixed_notifications(fake_db, context):
    context.read_id = "N_READ"
    context.unread_id = "N_UNREAD"
    seed_notification(fake_db, context.read_id, is_read=True, title="Old update")
    seed_notification(fake_db, context.unread_id, is_read=False, title="New update")


@when("the job seeker opens the All section")
def open_all_section(client, context):
    context.response = client.get("/notifications")


@then("the system should display both read and unread notifications")
def assert_all_displayed(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert f'data-id="{context.read_id}"' in page
    assert f'data-id="{context.unread_id}"' in page


# ==================================================
# Scenario: View unread notifications
# ==================================================


@when("the job seeker opens the Unread section")
def open_unread_section(client, context):
    # The Unread tab reuses the same server response and filters
    # client-side on data-read; loading the list is the same request.
    context.response = client.get("/notifications")


@then("the system should display only unread notifications")
def assert_unread_flagged(context):
    page = context.response.text
    assert f'data-id="{context.unread_id}"' in page
    assert notif_block(page, context.unread_id).count('data-read="false"') == 1


@then("read notifications should not appear in the Unread section")
def assert_read_excluded(context):
    page = context.response.text
    assert notif_block(page, context.read_id).count('data-read="true"') == 1


# ==================================================
# Scenario: Display unread notifications clearly
# ==================================================


@given("the job seeker is viewing the notification list")
def viewing_notification_list(fake_db, context):
    context.read_id = "N_READ2"
    context.unread_id = "N_UNREAD2"
    seed_notification(fake_db, context.read_id, is_read=True)
    seed_notification(fake_db, context.unread_id, is_read=False)


@when("the list contains unread notifications")
def list_contains_unread(client, context):
    context.response = client.get("/notifications")


@then("unread notifications should be visually distinguishable from read notifications")
def assert_visually_distinguishable(context):
    page = context.response.text

    unread_block = notif_block(page, context.unread_id)
    read_block = notif_block(page, context.read_id)

    # Unread items get the "unread" CSS class + a notif-dot indicator;
    # read items get neither -- this is what the stylesheet keys off of.
    assert "notif-item unread" in unread_block
    assert "notif-dot" in unread_block

    assert "notif-item " in read_block or 'notif-item"' in read_block
    assert "notif-dot" not in read_block


# ==================================================
# Scenario: Mark an unread notification as read
# ==================================================


@given("the job seeker is viewing the Unread section")
def viewing_unread_section(fake_db, context):
    context.unread_id = "N_TO_READ"
    seed_notification(fake_db, context.unread_id, is_read=False, title="Interview scheduled")


@given("an unread notification is displayed")
def unread_notification_displayed(client, context):
    response = client.get("/notifications")
    assert f'data-id="{context.unread_id}"' in response.text
    assert notif_block(response.text, context.unread_id).count('data-read="false"') == 1


@when("the job seeker opens the notification")
def open_the_notification(client, context):
    context.response = client.post(f"/api/notifications/{context.unread_id}/read")


@then("the system should mark the notification as read")
def assert_marked_read(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.unread_id)["is_read"] is True


@then("remove it from the Unread section")
def assert_removed_from_unread(client, context):
    page = client.get("/notifications").text
    assert notif_block(page, context.unread_id).count('data-read="true"') == 1


@then("keep it available in the All section")
def assert_kept_in_all(client, context):
    page = client.get("/notifications").text
    assert f'data-id="{context.unread_id}"' in page


# ==================================================
# Scenario: Update unread notification count
# ==================================================


@given("the job seeker has unread notifications")
def given_unread_notifications(fake_db, context):
    context.unread_id = "N_COUNT_1"
    seed_notification(fake_db, "N_COUNT_2", is_read=False)
    seed_notification(fake_db, context.unread_id, is_read=False)


@when("an unread notification is marked as read")
def mark_one_as_read(client, context):
    context.count_before = unread_tab_count(client.get("/notifications").text)
    client.post(f"/api/notifications/{context.unread_id}/read")
    context.count_after = unread_tab_count(client.get("/notifications").text)


@then("the unread notification count should decrease by one")
def assert_count_decreased(context):
    assert context.count_after == context.count_before - 1


# ==================================================
# Scenario: Preserve notification status after refresh
# ==================================================


@given("the job seeker has opened an unread notification")
def opened_unread_notification(fake_db, context):
    context.unread_id = "N_PERSIST"
    seed_notification(fake_db, context.unread_id, is_read=False)


@given("the notification has been marked as read")
def notification_marked_as_read(client, context):
    response = client.post(f"/api/notifications/{context.unread_id}/read")
    assert response.json()["success"] is True


@when("the job seeker refreshes the notification page")
def refresh_notification_page(client, context):
    context.response = client.get("/notifications")


@then("the notification should remain marked as read")
def assert_still_read(context):
    page = context.response.text
    assert notif_block(page, context.unread_id).count('data-read="true"') == 1


@then("it should not reappear in the Unread section")
def assert_not_in_unread_again(context):
    page = context.response.text
    assert notif_block(page, context.unread_id).count('data-read="false"') == 0


# ==================================================
# Scenario: No unread notifications available
# ==================================================


@given("the job seeker has no unread notifications")
def no_unread_notifications(fake_db, context):
    seed_notification(fake_db, "N_ALL_READ", is_read=True)


@then("the system should display a message indicating that there are no unread notifications")
def assert_no_unread_message(context):
    page = context.response.text
    assert unread_tab_count(page) == 0
    assert "No unread notifications" in page


# ==================================================
# Scenario: Receive a new unread notification
# ==================================================


@given("the job seeker has received a new notification")
def prep_new_notification_count(fake_db, client, context):
    context.count_before = unread_tab_count(client.get("/notifications").text)


@when("the notification appears in the system")
def notification_appears(fake_db, context):
    context.new_id = "N_NEW"
    seed_notification(fake_db, context.new_id, is_read=False, title="Welcome!")


@then("the notification should initially be marked as unread")
def assert_new_is_unread(client, context):
    page = client.get("/notifications").text
    assert notif_block(page, context.new_id).count('data-read="false"') == 1
    context.response = client.get("/notifications")


@then("the unread notification count should increase by one")
def assert_count_increased(client, context):
    count_after = unread_tab_count(client.get("/notifications").text)
    assert count_after == context.count_before + 1
