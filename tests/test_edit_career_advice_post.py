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

scenarios("features/edit_career_advice_post.feature")


@pytest.fixture
def client():
    secret_key = os.getenv("SECRET_KEY", "jobconnect-secret-key")
    session_data = {
        "user_type": "admin",
        "userType": "admin",
        "admin_id": "TEST_ADMIN",
        "user_id": "TEST_ADMIN",
        "userId": "TEST_ADMIN",
    }
    encoded_session = b64encode(json.dumps(session_data).encode("utf-8"))
    signed_session = TimestampSigner(str(secret_key)).sign(encoded_session)

    with TestClient(app, base_url="http://testserver") as test_client:
        test_client.cookies.set(
            "session",
            signed_session.decode("utf-8"),
            domain="testserver.local",
            path="/",
        )
        yield test_client


@pytest.fixture
def context():
    return {
        "post_id": None,
        "original_title": None,
        "updated_title": None,
        "updated_content": None,
        "response": None,
    }


@pytest.fixture
def post_id():
    test_post_id = f"TEST_EDIT_CAREER_ADVICE_{uuid4().hex}"
    yield test_post_id

    reference = db.collection("career_advice").document(test_post_id)
    document = reference.get()

    if document.exists:
        data = document.to_dict()
        if data and data.get("test") is True:
            reference.delete()


def create_published_post(post_id):
    current_time = datetime.now(timezone.utc)
    title = f"Original Career Advice {uuid4().hex}"

    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": "Career Development",
            "summary": "Original career advice summary.",
            "content": (
                "This is the original career advice content with "
                "enough characters to satisfy publication validation."
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
    context["original_title"] = create_published_post(post_id)
    context["updated_title"] = f"Updated Career Advice {uuid4().hex}"
    context["updated_content"] = (
        "This is the latest updated career advice information "
        "that is available for job seekers to read and understand."
    )


def valid_update_payload(context):
    return {
        "title": context["updated_title"],
        "category": "Interview Tips",
        "summary": "Updated career advice summary.",
        "content": context["updated_content"],
        "imageUrl": "",
        "action": "publish",
    }


# =====================================
# SCENARIO 1
# =====================================


@given("the admin is viewing the career advice management section")
def viewing_management_section(client, context, post_id):
    prepare_post(context, post_id)
    response = client.get(
        "/admin/career-advice",
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert context["original_title"] in response.text


@when("the admin selects an existing career advice post and " "updates its information")
def update_existing_post(client, context):
    context["response"] = client.put(
        f"/api/admin/career-advice/{context['post_id']}",
        json=valid_update_payload(context),
    )


@then("the system should save the updated career advice post details")
def verify_updated_details_saved(context):
    assert context["response"].status_code == 200

    document = db.collection("career_advice").document(context["post_id"]).get()
    assert document.exists

    post = document.to_dict()
    assert post is not None
    assert post["title"] == context["updated_title"]
    assert post["category"] == "Interview Tips"
    assert post["summary"] == "Updated career advice summary."
    assert post["content"] == context["updated_content"]


# =====================================
# SCENARIO 2
# =====================================


@given("the admin has selected a published career advice post")
def selected_published_post(context, post_id):
    prepare_post(context, post_id)


@when("the admin modifies and saves the post content")
def modify_published_content(client, context):
    context["response"] = client.put(
        f"/api/admin/career-advice/{context['post_id']}",
        json=valid_update_payload(context),
    )


@then("the system should update the published post with the latest " "information")
def verify_published_post_updated(context):
    assert context["response"].status_code == 200

    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["status"] == "Published"
    assert post["content"] == context["updated_content"]


@then("make the updated information available to job seekers")
def verify_update_available_to_job_seekers(client, context):
    response = client.get(f"/career-advice/{context['post_id']}")
    assert response.status_code == 200
    assert context["updated_title"] in response.text
    assert context["updated_content"] in response.text


# =====================================
# SCENARIO 3
# =====================================


@given("the admin is editing a career advice post")
def editing_career_advice_post(context, post_id):
    prepare_post(context, post_id)


@when("the admin submits the changes without the required information")
def submit_invalid_changes(client, context):
    context["response"] = client.put(
        f"/api/admin/career-advice/{context['post_id']}",
        json={
            "title": "",
            "category": "",
            "summary": "",
            "content": "",
            "imageUrl": "",
            "action": "publish",
        },
    )


@then("the system should display a validation message requesting " "the missing details")
def verify_validation_message(context):
    response = context["response"]
    assert response.status_code == 422

    errors = response.json()["detail"]
    assert "Title is required." in errors
    assert "Category is required before publishing." in errors
    assert "Summary is required before publishing." in errors
    assert "Content is required before publishing." in errors


@then("the changes should not be saved")
def verify_invalid_changes_not_saved(context):
    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["title"] == context["original_title"]
    assert post["category"] == "Career Development"
    assert post["status"] == "Published"


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has entered valid changes to a career advice post")
def entered_valid_changes(context, post_id):
    prepare_post(context, post_id)


@when("the changes are saved successfully")
def save_valid_changes(client, context):
    context["response"] = client.put(
        f"/api/admin/career-advice/{context['post_id']}",
        json=valid_update_payload(context),
    )
    assert context["response"].status_code == 200


@then(
    "the system should display a confirmation message indicating "
    "that the post has been updated successfully"
)
def verify_update_confirmation(context):
    result = context["response"].json()
    assert result["success"] is True
    assert result["status"] == "Published"
    assert result["message"] == "Career advice post updated successfully."


# =====================================
# NORMAL TEST
# =====================================


def test_edit_career_advice_post(client, post_id):
    original_title = create_published_post(post_id)
    updated_title = f"Normal Updated Advice {uuid4().hex}"

    response = client.put(
        f"/api/admin/career-advice/{post_id}",
        json={
            "title": updated_title,
            "category": "Job Search",
            "summary": "Updated test summary.",
            "content": (
                "This is valid updated content containing enough "
                "characters for a published career advice post."
            ),
            "imageUrl": "",
            "action": "publish",
        },
    )

    assert response.status_code == 200

    post = db.collection("career_advice").document(post_id).get().to_dict()
    assert post is not None
    assert post["title"] != original_title
    assert post["title"] == updated_title
    assert post["status"] == "Published"


# =====================================
# NEGATIVE TEST
# =====================================


def test_edit_invalid_career_advice_post(client):
    invalid_post_id = f"INVALID_POST_{uuid4().hex}"

    response = client.put(
        f"/api/admin/career-advice/{invalid_post_id}",
        json={
            "title": "Updated title",
            "category": "Career Development",
            "summary": "Updated summary",
            "content": (
                "This content is sufficiently long for publication "
                "validation and should still return not found."
            ),
            "imageUrl": "",
            "action": "publish",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Career advice post not found."
