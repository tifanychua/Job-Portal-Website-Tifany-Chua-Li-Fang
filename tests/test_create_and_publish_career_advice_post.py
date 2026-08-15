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

scenarios("features/create_and_publish_career_advice_post.feature")


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
    }


# =====================================
# TEST DATA FIXTURE
# =====================================


@pytest.fixture
def post_id():
    test_post_id = f"TEST_CAREER_ADVICE_{uuid4().hex}"

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


def create_career_advice_post(
    post_id,
    status="Draft",
):
    current_time = datetime.now(UTC)

    db.collection("career_advice").document(post_id).set(
        {
            "title": "How to Prepare for an Interview",
            "category": "Interview Tips",
            "summary": ("Useful preparation tips for job interviews."),
            "content": (
                "Preparing for an interview requires research, "
                "practice, confidence, and appropriate communication."
            ),
            "imageUrl": "",
            "status": status,
            "createdAt": current_time,
            "updatedAt": current_time,
            "publicationDate": (current_time if status == "Published" else None),
            "createdBy": "TEST_ADMIN",
            "updatedBy": "TEST_ADMIN",
            "test": True,
        }
    )

    return post_id


# =====================================
# ADMIN SESSION
# =====================================


@given("the admin is logged into the admin dashboard")
def admin_logged_in(client):
    assert client.cookies.get("session") is not None


# =====================================
# SCENARIO 1
# =====================================


@when("the admin enters the career advice post details and submits the form")
def submit_career_advice_post(client, context):
    context["post_title"] = f"Career Advice Test {uuid4().hex}"

    context["response"] = client.post(
        "/api/admin/career-advice",
        json={
            "title": context["post_title"],
            "category": "Career Development",
            "summary": ("Useful career development advice for job seekers."),
            "content": (
                "This career advice post provides useful guidance "
                "to help job seekers develop their careers successfully."
            ),
            "imageUrl": "",
            "action": "publish",
        },
    )


@then("the system should create a new career advice post")
def verify_career_advice_created(context):
    response = context["response"]

    assert response.status_code == 201

    result = response.json()

    assert result["success"] is True
    assert result["status"] == "Published"
    assert "id" in result

    context["post_id"] = result["id"]


@then("save the post information in the database")
def verify_post_saved_in_database(context):
    document = db.collection("career_advice").document(context["post_id"]).get()

    assert document.exists

    post = document.to_dict()

    assert post is not None
    assert post["title"] == context["post_title"]
    assert post["category"] == "Career Development"
    assert post["status"] == "Published"
    assert post["publicationDate"] is not None

    # Remove the post created by the API.
    document.reference.delete()


# =====================================
# SCENARIO 2
# =====================================


@given("the admin has created a career advice post")
def existing_career_advice_post(context, post_id):
    context["post_id"] = create_career_advice_post(
        post_id,
        status="Draft",
    )


@when("the admin selects the publish option")
def publish_career_advice_post(client, context):
    context["response"] = client.post(f"/api/admin/career-advice/{context['post_id']}/publish")


@then('the system should update the post status to "Published"')
def verify_published_status(context):
    response = context["response"]

    assert response.status_code == 200

    result = response.json()

    assert result["success"] is True
    assert result["message"] == "Draft published successfully."

    document = db.collection("career_advice").document(context["post_id"]).get()

    assert document.exists

    post = document.to_dict()

    assert post is not None
    assert post["status"] == "Published"
    assert post["publicationDate"] is not None


@then("make the post available for job seekers to view")
def verify_post_available_to_job_seekers(client, context):
    response = client.get("/career-advice")

    assert response.status_code == 200
    assert "How to Prepare for an Interview" in response.text


# =====================================
# SCENARIO 3
# =====================================


@given("the admin is creating a career advice post")
def admin_creating_post(context):
    context["post_title"] = f"Invalid Career Advice {uuid4().hex}"


@when("the admin submits the post without the required information")
def submit_invalid_post(client, context):
    context["response"] = client.post(
        "/api/admin/career-advice",
        json={
            "title": context["post_title"],
            "category": "",
            "summary": "",
            "content": "",
            "imageUrl": "",
            "action": "publish",
        },
    )


@then("the system should display a validation message requesting the missing details")
def verify_validation_message(context):
    response = context["response"]

    assert response.status_code == 422

    result = response.json()

    assert "detail" in result
    assert "Category is required before publishing." in result["detail"]
    assert "Summary is required before publishing." in result["detail"]
    assert "Content is required before publishing." in result["detail"]


@then("the career advice post should not be published")
def verify_invalid_post_not_published(context):
    documents = db.collection("career_advice").where("title", "==", context["post_title"]).stream()

    matching_posts = list(documents)

    assert len(matching_posts) == 0


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has successfully published a career advice post")
def published_career_advice_post(context, post_id):
    context["post_id"] = create_career_advice_post(
        post_id,
        status="Published",
    )


@when("the admin accesses the career advice management section")
def access_career_advice_management(client, context):
    context["response"] = client.get(
        "/admin/career-advice",
        follow_redirects=False,
    )


@then("the system should display the published post with its current status")
def verify_published_post_displayed(context):
    response = context["response"]

    assert response.status_code == 200
    assert "How to Prepare for an Interview" in response.text
    assert "Published" in response.text


# =====================================
# NORMAL TEST
# =====================================


def test_create_and_publish_career_advice(client):
    unique_title = f"Career Advice {uuid4().hex}"

    response = client.post(
        "/api/admin/career-advice",
        json={
            "title": unique_title,
            "category": "Career Development",
            "summary": "Useful advice for career development.",
            "content": (
                "This post contains sufficient career advice "
                "content for job seekers to read and understand."
            ),
            "imageUrl": "",
            "action": "publish",
        },
    )

    assert response.status_code == 201

    result = response.json()

    assert result["success"] is True
    assert result["status"] == "Published"

    document = db.collection("career_advice").document(result["id"]).get()

    assert document.exists

    post = document.to_dict()

    assert post is not None
    assert post["title"] == unique_title
    assert post["status"] == "Published"

    document.reference.delete()


# =====================================
# NEGATIVE TEST
# =====================================


def test_publish_invalid_career_advice_post(client):
    invalid_post_id = f"INVALID_POST_{uuid4().hex}"

    response = client.post(f"/api/admin/career-advice/{invalid_post_id}/publish")

    assert response.status_code == 404
    assert response.json()["detail"] == "Career advice post not found."
