"""Acceptance + unit tests for the employer "Unread notifications" story.

Mirrors test_jobSeekerUnreadNotifications.py but against the employer-styled
/employer-notifications page (job_portal_web.backend.notifications), which
shares the same is_read / data-read data contract.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from html_helpers import item_block, tab_count
from job_portal_web.backend import notifications
from job_portal_web.backend.main import app

COMPANY_ID = "C000001"

scenarios("features/employerUnreadNotifications.feature")


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


def seed_notification(fake_db, doc_id, *, is_read, title="Notice", message="msg"):
    fake_db.seed(
        "notification",
        doc_id,
        {
            "user_id": COMPANY_ID,
            "user_type": "employer",
            "is_read": is_read,
            "type": "application",
            "title": title,
            "message": message,
            "link": "",
            "created_at": datetime.now(timezone.utc),
        },
    )


def notif_block(page_html: str, doc_id: str) -> str:
    return item_block(page_html, doc_id, item_class="notif-item")


def unread_tab_count(page_html: str) -> int:
    return tab_count(page_html, "unreadTabCount")


NOTIF_PAGE = "/employer-notifications"


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


@given("the employer has both read and unread notifications")
def given_mixed_notifications(fake_db, context):
    context.read_id = "N_READ"
    context.unread_id = "N_UNREAD"
    seed_notification(fake_db, context.read_id, is_read=True, title="Old update")
    seed_notification(fake_db, context.unread_id, is_read=False, title="New update")


@when("the employer opens the All section")
def open_all_section(client, context):
    context.response = client.get(NOTIF_PAGE)


@then("the system should display both read and unread notifications")
def assert_all_displayed(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert f'data-id="{context.read_id}"' in page
    assert f'data-id="{context.unread_id}"' in page


# ==================================================
# Scenario: View unread notifications
# ==================================================


@when("the employer opens the Unread section")
def open_unread_section(client, context):
    context.response = client.get(NOTIF_PAGE)


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


@given("the employer is viewing the notification list")
def viewing_notification_list(fake_db, context):
    context.read_id = "N_READ2"
    context.unread_id = "N_UNREAD2"
    seed_notification(fake_db, context.read_id, is_read=True)
    seed_notification(fake_db, context.unread_id, is_read=False)


@when("the list contains unread notifications")
def list_contains_unread(client, context):
    context.response = client.get(NOTIF_PAGE)


@then("the unread notifications should be visually distinguishable from read notifications")
def assert_visually_distinguishable(context):
    page = context.response.text

    unread_block = notif_block(page, context.unread_id)
    read_block = notif_block(page, context.read_id)

    assert "notif-item unread" in unread_block
    assert "notif-dot" in unread_block

    assert "notif-dot" not in read_block


# ==================================================
# Scenario: Mark an unread notification as read
# ==================================================


@given("the employer is viewing the Unread section")
def viewing_unread_section(fake_db, context):
    context.unread_id = "N_TO_READ"
    seed_notification(fake_db, context.unread_id, is_read=False, title="New application received")


@given("an unread notification is displayed")
def unread_notification_displayed(client, context):
    response = client.get(NOTIF_PAGE)
    assert f'data-id="{context.unread_id}"' in response.text
    assert notif_block(response.text, context.unread_id).count('data-read="false"') == 1


@when("the employer opens the notification")
def open_the_notification(client, context):
    context.response = client.post(f"/api/notifications/{context.unread_id}/read")


@then("the system should mark the notification as read")
def assert_marked_read(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["success"] is True
    assert fake_db.get("notification", context.unread_id)["is_read"] is True


@then("remove it from the Unread section")
def assert_removed_from_unread(client, context):
    page = client.get(NOTIF_PAGE).text
    assert notif_block(page, context.unread_id).count('data-read="true"') == 1


@then("keep it available in the All section")
def assert_kept_in_all(client, context):
    page = client.get(NOTIF_PAGE).text
    assert f'data-id="{context.unread_id}"' in page


# ==================================================
# Scenario: Update unread notification count
# ==================================================


@given("the employer has unread notifications")
def given_unread_notifications(fake_db, context):
    context.unread_id = "N_COUNT_1"
    seed_notification(fake_db, "N_COUNT_2", is_read=False)
    seed_notification(fake_db, context.unread_id, is_read=False)


@when("an unread notification is marked as read")
def mark_one_as_read(client, context):
    context.count_before = unread_tab_count(client.get(NOTIF_PAGE).text)
    client.post(f"/api/notifications/{context.unread_id}/read")
    context.count_after = unread_tab_count(client.get(NOTIF_PAGE).text)


@then("the unread notification count should decrease by one")
def assert_count_decreased(context):
    assert context.count_after == context.count_before - 1


# ==================================================
# Scenario: Preserve notification status after refresh
# ==================================================


@given("the employer has opened an unread notification")
def opened_unread_notification(fake_db, context):
    context.unread_id = "N_PERSIST"
    seed_notification(fake_db, context.unread_id, is_read=False)


@given("the notification has been marked as read")
def notification_marked_as_read(client, context):
    response = client.post(f"/api/notifications/{context.unread_id}/read")
    assert response.json()["success"] is True


@when("the employer refreshes the notification page")
def refresh_notification_page(client, context):
    context.response = client.get(NOTIF_PAGE)


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


@given("the employer has no unread notifications")
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


@given("the employer has received a new notification")
def prep_new_notification_count(fake_db, client, context):
    context.count_before = unread_tab_count(client.get(NOTIF_PAGE).text)


@when("the notification appears in the system")
def notification_appears(fake_db, context):
    context.new_id = "N_NEW"
    seed_notification(fake_db, context.new_id, is_read=False, title="New candidate applied")


@then("the notification should initially be marked as unread")
def assert_new_is_unread(client, context):
    page = client.get(NOTIF_PAGE).text
    assert notif_block(page, context.new_id).count('data-read="false"') == 1
    context.response = client.get(NOTIF_PAGE)


@then("the unread notification count should increase by one")
def assert_count_increased(client, context):
    count_after = unread_tab_count(client.get(NOTIF_PAGE).text)
    assert count_after == context.count_before + 1
