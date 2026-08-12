import json
import os
from base64 import b64encode
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.admin_users import ensure_account_can_log_in
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/suspend_or_deactivate_user_account.feature")


@pytest.fixture
def client():
    secret_key = os.getenv("SECRET_KEY", "jobconnect-secret-key")
    session = {
        "user_type": "admin",
        "admin_id": "TEST_ADMIN",
        "user_id": "TEST_ADMIN",
    }
    encoded = b64encode(json.dumps(session).encode("utf-8"))
    signed = TimestampSigner(str(secret_key)).sign(encoded)

    with TestClient(app, base_url="http://testserver") as test_client:
        test_client.cookies.set(
            "session",
            signed.decode("utf-8"),
            domain="testserver.local",
            path="/",
        )
        yield test_client


@pytest.fixture
def context():
    return {
        "user_id": None,
        "response": None,
        "action": None,
        "reason": None,
    }


@pytest.fixture
def user_id():
    value = f"TEST_RESTRICT_USER_{uuid4().hex}"
    yield value

    db.collection("job_seeker").document(value).delete()
    audits = db.collection("account_status_audit").where("accountId", "==", value).stream()
    for document in audits:
        document.reference.delete()


def create_active_user(user_id):
    db.collection("job_seeker").document(user_id).set(
        {
            "firstName": "Test",
            "lastName": "Restricted User",
            "email": f"{user_id.lower()}@example.com",
            "accountStatus": "Active",
            "accountStatusReason": "",
            "createdAt": datetime.now(timezone.utc),
            "test": True,
        }
    )


def prepare_active_user(context, user_id):
    create_active_user(user_id)
    context["user_id"] = user_id


def change_status(client, context, status, reason):
    context["action"] = status
    context["reason"] = reason
    context["response"] = client.patch(
        f"/api/admin/users/job_seeker/{context['user_id']}/status",
        json={
            "status": status,
            "reason": reason,
        },
    )


def get_user(context):
    document = db.collection("job_seeker").document(context["user_id"]).get()
    assert document.exists
    return document.to_dict()


def verify_login_blocked(context, expected_text):
    user = get_user(context)
    assert user is not None

    with pytest.raises(HTTPException) as error:
        ensure_account_can_log_in(user)

    assert error.value.status_code == 403
    assert expected_text in str(error.value.detail).lower()


# =====================================
# COMMON GIVEN
# =====================================


@given("the admin is viewing the user management section")
def viewing_user_management(client, context, user_id):
    prepare_active_user(context, user_id)
    response = client.get(
        "/admin/users",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Test Restricted User" in response.text
    assert "Active" in response.text


# =====================================
# SCENARIO 1
# =====================================


@when("the admin selects an active user account and chooses " "the suspend option")
def suspend_account(client, context):
    change_status(
        client,
        context,
        "Suspended",
        "Repeated misuse of platform features",
    )


@then('the system should change the user\'s account status to "Suspended"')
def verify_suspended_status(context):
    assert context["response"].status_code == 200
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == "Suspended"
    assert user["accountStatusReason"] == context["reason"]


@then("restrict the user's access to the platform")
def verify_suspended_access(context):
    verify_login_blocked(context, "suspended")


# =====================================
# SCENARIO 2
# =====================================


@when("the admin selects an active user account and chooses " "the deactivate option")
def deactivate_account(client, context):
    change_status(
        client,
        context,
        "Deactivated",
        "Serious policy violation",
    )


@then('the system should change the user\'s account status to "Deactivated"')
def verify_deactivated_status(context):
    assert context["response"].status_code == 200
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == "Deactivated"
    assert user["accountStatusReason"] == context["reason"]


@then("prevent the user from accessing the platform features")
def verify_deactivated_access(context):
    verify_login_blocked(context, "deactivated")


# =====================================
# SCENARIO 3
# =====================================


@given("a user account has been suspended or deactivated")
def restricted_account(client, context, user_id):
    prepare_active_user(context, user_id)
    change_status(
        client,
        context,
        "Suspended",
        "Temporary restriction for testing",
    )
    assert context["response"].status_code == 200


@when("the admin chooses to reactivate the user account")
def reactivate_account(client, context):
    change_status(client, context, "Active", "")


@then('the system should change the account status to "Active"')
def verify_reactivated_status(context):
    assert context["response"].status_code == 200
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == "Active"
    assert user["accountStatusReason"] == ""


@then("allow the user to access the platform again")
def verify_access_restored(context):
    user = get_user(context)
    assert user is not None
    ensure_account_can_log_in(user)


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has suspended or deactivated a user account")
def admin_restricted_account(client, context, user_id):
    prepare_active_user(context, user_id)
    change_status(
        client,
        context,
        "Deactivated",
        "Policy violation recorded for testing",
    )
    assert context["response"].status_code == 200


@when("the account status is updated")
def status_is_updated(context):
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == context["action"]


@then("the system should record the account status change")
def verify_audit_created(context):
    audits = list(
        db.collection("account_status_audit").where("accountId", "==", context["user_id"]).stream()
    )
    assert len(audits) == 1


@then("the record should include the user information, action performed, " "and date of change")
def verify_audit_details(context):
    audits = list(
        db.collection("account_status_audit").where("accountId", "==", context["user_id"]).stream()
    )
    assert len(audits) == 1

    audit = audits[0].to_dict()
    assert audit is not None
    assert audit["accountId"] == context["user_id"]
    assert audit["accountType"] == "job_seeker"
    assert audit["previousStatus"] == "Active"
    assert audit["newStatus"] == "Deactivated"
    assert audit["reason"] == context["reason"]
    assert audit["changedBy"] == "TEST_ADMIN"
    assert audit["changedAt"] is not None


# =====================================
# NEGATIVE TEST
# =====================================


def test_suspend_account_without_reason(client, user_id):
    create_active_user(user_id)
    response = client.patch(
        f"/api/admin/users/job_seeker/{user_id}/status",
        json={"status": "Suspended", "reason": ""},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == ("Please provide a reason for restricting this account.")

    user = db.collection("job_seeker").document(user_id).get().to_dict()
    assert user is not None
    assert user["accountStatus"] == "Active"
