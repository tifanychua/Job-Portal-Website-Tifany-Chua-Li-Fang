import json
import os
from base64 import b64encode
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.admin_users import ensure_account_can_log_in
from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/reactivate_user_account.feature")


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
        "previous_status": None,
    }


@pytest.fixture
def user_id():
    value = f"TEST_REACTIVATE_USER_{uuid4().hex}"
    yield value

    db.collection("job_seeker").document(value).delete()

    audit_documents = db.collection("account_status_audit").where("accountId", "==", value).stream()
    for document in audit_documents:
        document.reference.delete()


def create_restricted_user(user_id, status):
    db.collection("job_seeker").document(user_id).set(
        {
            "firstName": "Test",
            "lastName": "Job Seeker",
            "email": f"{user_id.lower()}@example.com",
            "accountStatus": status,
            "accountStatusReason": "Test restriction reason",
            "createdAt": datetime.now(UTC),
            "test": True,
        }
    )


def prepare_user(context, user_id, status):
    create_restricted_user(user_id, status)
    context["user_id"] = user_id
    context["previous_status"] = status


def reactivate(client, context):
    context["response"] = client.patch(
        f"/api/admin/users/job_seeker/{context['user_id']}/status",
        json={
            "status": "Active",
            "reason": "",
        },
    )


def get_user(context):
    document = db.collection("job_seeker").document(context["user_id"]).get()
    assert document.exists
    return document.to_dict()


# =====================================
# SCENARIO 1
# =====================================


@given("the admin is viewing a suspended user account")
def viewing_suspended_account(client, context, user_id):
    prepare_user(context, user_id, "Suspended")
    response = client.get(
        "/admin/users",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Test Job Seeker" in response.text
    assert "Suspended" in response.text


@when("the admin selects the reactivate option")
def select_reactivate(client, context):
    reactivate(client, context)


@then('the system should change the user\'s account status to "Active"')
def verify_active_status(context):
    assert context["response"].status_code == 200
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == "Active"
    assert user["accountStatusReason"] == ""


@then("restore the user's access to the platform")
def verify_access_restored(context):
    user = get_user(context)
    assert user is not None
    ensure_account_can_log_in(user)


# =====================================
# SCENARIO 2
# =====================================


@given("the admin is viewing a deactivated user account")
def viewing_deactivated_account(client, context, user_id):
    prepare_user(context, user_id, "Deactivated")
    response = client.get(
        "/admin/users",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Test Job Seeker" in response.text
    assert "Deactivated" in response.text


@then("allow the user to log in again")
def verify_login_allowed(context):
    user = get_user(context)
    assert user is not None
    ensure_account_can_log_in(user)


# =====================================
# SCENARIO 3
# =====================================


@given("the admin has selected a user account for reactivation")
def selected_account(context, user_id):
    prepare_user(context, user_id, "Suspended")


@when("the reactivation process is completed successfully")
def complete_reactivation(client, context):
    reactivate(client, context)
    assert context["response"].status_code == 200


@then(
    "the system should display a confirmation message indicating "
    "that the user account has been successfully reactivated"
)
def verify_confirmation_message(context):
    result = context["response"].json()
    assert result["success"] is True
    assert result["status"] == "Active"
    assert result["message"] == "Account reactivated successfully."


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has reactivated a user account")
def reactivated_account(client, context, user_id):
    prepare_user(context, user_id, "Suspended")
    reactivate(client, context)
    assert context["response"].status_code == 200


@when("the account status is updated")
def account_status_updated(context):
    user = get_user(context)
    assert user is not None
    assert user["accountStatus"] == "Active"


@then("the system should record the reactivation activity")
def verify_reactivation_audit_exists(context):
    audits = list(
        db.collection("account_status_audit").where("accountId", "==", context["user_id"]).stream()
    )
    assert len(audits) == 1


@then("the record should include the user information, admin action, and date of change")
def verify_audit_details(context):
    audits = list(
        db.collection("account_status_audit").where("accountId", "==", context["user_id"]).stream()
    )
    assert len(audits) == 1

    audit = audits[0].to_dict()
    assert audit is not None
    assert audit["accountId"] == context["user_id"]
    assert audit["accountType"] == "job_seeker"
    assert audit["previousStatus"] == context["previous_status"]
    assert audit["newStatus"] == "Active"
    assert audit["reason"] == ""
    assert audit["changedBy"] == "TEST_ADMIN"
    assert audit["changedAt"] is not None


# =====================================
# NORMAL TEST
# =====================================


def test_reactivate_suspended_user(client, user_id):
    create_restricted_user(user_id, "Suspended")
    response = client.patch(
        f"/api/admin/users/job_seeker/{user_id}/status",
        json={"status": "Active", "reason": ""},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Active"

    user = db.collection("job_seeker").document(user_id).get().to_dict()
    assert user is not None
    assert user["accountStatus"] == "Active"


# =====================================
# NEGATIVE TEST
# =====================================


def test_reactivate_invalid_user(client):
    invalid_user_id = f"INVALID_USER_{uuid4().hex}"
    response = client.patch(
        f"/api/admin/users/job_seeker/{invalid_user_id}/status",
        json={"status": "Active", "reason": ""},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User account was not found."
