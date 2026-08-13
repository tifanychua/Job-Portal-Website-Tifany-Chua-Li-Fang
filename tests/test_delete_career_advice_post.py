import json
import os
from base64 import b64encode
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# =====================================
# LOAD FEATURE
# =====================================

scenarios("features/delete_career_advice_post.feature")


# =====================================
# CLIENT
# =====================================


@pytest.fixture
def client():
    secret_key = os.getenv(
        "SECRET_KEY",
        "jobconnect-secret-key",
    )

    session_data = {
        "user_type": "admin",
        "userType": "admin",
        "admin_id": "TEST_ADMIN",
        "user_id": "TEST_ADMIN",
        "userId": "TEST_ADMIN",
    }

    encoded_session = b64encode(json.dumps(session_data).encode("utf-8"))

    signed_session = TimestampSigner(str(secret_key)).sign(encoded_session)

    with TestClient(
        app,
        base_url="http://testserver",
    ) as test_client:
        test_client.cookies.set(
            "session",
            signed_session.decode("utf-8"),
            domain="testserver.local",
            path="/",
        )

        yield test_client


# =====================================
# CONTEXT
# =====================================


@pytest.fixture
def context():
    return {
        "post_id": None,
        "post_title": None,
        "response": None,
        "delete_cancelled": False,
    }


# =====================================
# TEST DATA FIXTURE
# =====================================


@pytest.fixture
def post_id():
    test_post_id = f"TEST_DELETE_CAREER_ADVICE_{uuid4().hex}"

    yield test_post_id

    document_reference = db.collection("career_advice").document(test_post_id)

    document = document_reference.get()

    if document.exists:
        data = document.to_dict()

        if data and data.get("test") is True:
            document_reference.delete()


# =====================================
# CREATE CAREER ADVICE DATA
# =====================================


def create_career_advice_post(post_id):
    current_time = datetime.now(UTC)
    title = f"Career Advice Delete Test {uuid4().hex}"

    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": "Career Development",
            "summary": "A test post that can be safely deleted.",
            "content": (
                "This test career advice post contains enough content "
                "to satisfy the publication validation requirements."
            ),
            "imageUrl": "",
            "status": "Published",
            "createdAt": current_time,
            "updatedAt": current_time,
            "publicationDate": current_time,
            "createdBy": "TEST_ADMIN",
            "updatedBy": "TEST_ADMIN",
            "test": True,
        }
    )

    return title


def prepare_post(context, post_id):
    context["post_id"] = post_id
    context["post_title"] = create_career_advice_post(post_id)


# =====================================
# SCENARIO 1
# =====================================


@given("the admin is viewing the career advice management section")
def viewing_career_advice_management(client, context, post_id):
    prepare_post(context, post_id)

    response = client.get(
        "/admin/career-advice",
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert context["post_title"] in response.text


@when("the admin selects a career advice post and chooses the delete option")
def choose_delete_option(client, context):
    context["response"] = client.delete(f"/api/admin/career-advice/{context['post_id']}")


@then("the system should remove the selected career advice post from the system")
def verify_post_removed(context):
    response = context["response"]

    assert response.status_code == 200

    document = db.collection("career_advice").document(context["post_id"]).get()

    assert not document.exists


# =====================================
# SCENARIO 2
# =====================================


@given("the admin has selected a career advice post for deletion")
def selected_post_for_deletion(context, post_id):
    prepare_post(context, post_id)


@when("the admin confirms the delete action")
def confirm_delete_action(client, context):
    context["response"] = client.delete(f"/api/admin/career-advice/{context['post_id']}")


@then("the system should delete the selected post")
def verify_selected_post_deleted(context):
    response = context["response"]

    assert response.status_code == 200

    document = db.collection("career_advice").document(context["post_id"]).get()

    assert not document.exists


@then("display a confirmation message indicating that the post has been successfully deleted")
def verify_deletion_confirmation(context):
    result = context["response"].json()

    assert result["success"] is True
    assert result["message"] == "Career advice post deleted successfully."


# =====================================
# SCENARIO 3
# =====================================


@when("the admin cancels the delete action")
def cancel_delete_action(context):
    # Cancelling occurs in the browser, so no DELETE request is sent.
    context["delete_cancelled"] = True


@then("the system should keep the career advice post unchanged")
def verify_post_unchanged(context):
    assert context["delete_cancelled"] is True

    document = db.collection("career_advice").document(context["post_id"]).get()

    assert document.exists

    post = document.to_dict()

    assert post is not None
    assert post["title"] == context["post_title"]
    assert post["status"] == "Published"


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has successfully deleted a career advice post")
def successfully_deleted_post(client, context, post_id):
    prepare_post(context, post_id)

    response = client.delete(f"/api/admin/career-advice/{context['post_id']}")

    assert response.status_code == 200


@when("a job seeker accesses the career advice section")
def job_seeker_accesses_career_advice(client, context):
    context["response"] = client.get("/career-advice")


@then("the deleted post should no longer be displayed")
def verify_deleted_post_unavailable(context):
    response = context["response"]

    assert response.status_code == 200
    assert context["post_title"] not in response.text

    document = db.collection("career_advice").document(context["post_id"]).get()

    assert not document.exists


# =====================================
# NORMAL TEST
# =====================================


def test_delete_career_advice_post(client, post_id):
    create_career_advice_post(post_id)

    response = client.delete(f"/api/admin/career-advice/{post_id}")

    assert response.status_code == 200

    result = response.json()

    assert result["success"] is True
    assert result["message"] == "Career advice post deleted successfully."

    document = db.collection("career_advice").document(post_id).get()

    assert not document.exists


# =====================================
# NEGATIVE TEST
# =====================================


def test_delete_invalid_career_advice_post(client):
    invalid_post_id = f"INVALID_POST_{uuid4().hex}"

    response = client.delete(f"/api/admin/career-advice/{invalid_post_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Career advice post not found."
