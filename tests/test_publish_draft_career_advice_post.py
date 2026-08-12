import json
import os
from base64 import b64encode
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/publish_draft_career_advice_post.feature")


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
        "post_id": None,
        "post_title": None,
        "response": None,
    }


@pytest.fixture
def post_id():
    value = f"TEST_PUBLISH_DRAFT_{uuid4().hex}"
    yield value

    reference = db.collection("career_advice").document(value)
    document = reference.get()
    if document.exists:
        data = document.to_dict()
        if data and data.get("test") is True:
            reference.delete()


def create_draft(post_id, complete=True):
    current_time = datetime.now(timezone.utc)
    title = f"Draft Career Advice {uuid4().hex}"

    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": "Career Development" if complete else "",
            "summary": "Useful career guidance." if complete else "",
            "content": (
                "This completed draft contains enough useful career "
                "guidance to satisfy all publication requirements."
                if complete
                else ""
            ),
            "imageUrl": "",
            "status": "Draft",
            "createdAt": current_time,
            "updatedAt": current_time,
            "publicationDate": None,
            "createdBy": "TEST_ADMIN",
            "updatedBy": "TEST_ADMIN",
            "test": True,
        }
    )
    return title


def prepare_draft(context, post_id, complete=True):
    context["post_id"] = post_id
    context["post_title"] = create_draft(post_id, complete)


def publish(client, context):
    context["response"] = client.post(f"/api/admin/career-advice/{context['post_id']}/publish")


# =====================================
# SCENARIO 1
# =====================================


@given("the admin has a completed draft career advice post")
def completed_draft(context, post_id):
    prepare_draft(context, post_id)


@when("the admin selects the publish option")
def select_publish(client, context):
    publish(client, context)


@then('the post status should be updated from "Draft" to "Published"')
def verify_status_updated(context):
    assert context["response"].status_code == 200
    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["status"] == "Published"
    assert post["publicationDate"] is not None


# =====================================
# SCENARIO 2
# =====================================


@given("the admin has published a valid draft career advice post")
def published_valid_draft(client, context, post_id):
    prepare_draft(context, post_id)
    publish(client, context)


@when("the system processes the publishing request")
def process_publishing_request(context):
    assert context["response"] is not None
    assert context["response"].status_code == 200


@then("the updated post status should be saved in the database")
def verify_status_saved(context):
    document = db.collection("career_advice").document(context["post_id"]).get()
    assert document.exists
    post = document.to_dict()
    assert post is not None
    assert post["status"] == "Published"
    assert post["publicationDate"] is not None
    assert post["updatedBy"] == "TEST_ADMIN"


# =====================================
# SCENARIO 3
# =====================================


@given("the career advice post has been successfully published")
def successfully_published(client, context, post_id):
    prepare_draft(context, post_id)
    publish(client, context)
    assert context["response"].status_code == 200


@when("a job seeker accesses the career advice section")
def access_career_advice(client, context):
    context["response"] = client.get("/career-advice")


@then("the published post should be displayed and available for viewing")
def verify_post_available(context):
    assert context["response"].status_code == 200
    assert context["post_title"] in context["response"].text


# =====================================
# SCENARIO 4
# =====================================


@given("the admin is attempting to publish a draft career advice post")
def attempting_to_publish(context, post_id):
    prepare_draft(context, post_id, complete=False)


@when("the draft is missing required information")
def publish_incomplete_draft(client, context):
    publish(client, context)


@then("the system should display a validation message")
def verify_validation_message(context):
    response = context["response"]
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert "Category is required before publishing." in errors
    assert "Summary is required before publishing." in errors
    assert "Content is required before publishing." in errors


@then('the post should remain in "Draft" status')
def verify_post_remains_draft(context):
    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["status"] == "Draft"
    assert post["publicationDate"] is None


# =====================================
# SCENARIO 5
# =====================================


@given("the admin has selected the publish option for a valid draft")
def selected_publish_for_valid_draft(context, post_id):
    prepare_draft(context, post_id)


@when("the publishing process is completed successfully")
def complete_publishing(client, context):
    publish(client, context)
    assert context["response"].status_code == 200


@then("the system should display a successful publication confirmation message")
def verify_confirmation(context):
    result = context["response"].json()
    assert result["success"] is True
    assert result["message"] == "Draft published successfully."


# =====================================
# NORMAL TEST
# =====================================


def test_publish_valid_draft(client, post_id):
    create_draft(post_id)
    response = client.post(f"/api/admin/career-advice/{post_id}/publish")
    assert response.status_code == 200
    assert response.json()["success"] is True

    post = db.collection("career_advice").document(post_id).get().to_dict()
    assert post is not None
    assert post["status"] == "Published"


# =====================================
# NEGATIVE TEST
# =====================================


def test_publish_invalid_draft(client):
    invalid_post_id = f"INVALID_POST_{uuid4().hex}"
    response = client.post(f"/api/admin/career-advice/{invalid_post_id}/publish")
    assert response.status_code == 404
    assert response.json()["detail"] == "Career advice post not found."
