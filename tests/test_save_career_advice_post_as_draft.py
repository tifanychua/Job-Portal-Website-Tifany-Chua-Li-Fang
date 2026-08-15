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

scenarios("features/save_career_advice_post_as_draft.feature")


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
    value = {
        "post_id": None,
        "post_title": None,
        "response": None,
    }
    yield value

    post_id = value.get("post_id")
    if post_id:
        db.collection("career_advice").document(post_id).delete()


@pytest.fixture
def post_id():
    value = f"TEST_SAVE_DRAFT_{uuid4().hex}"
    yield value
    db.collection("career_advice").document(value).delete()


def create_draft(post_id, complete=False):
    current_time = datetime.now(UTC)
    title = f"Saved Draft Career Advice {uuid4().hex}"

    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": "Career Development" if complete else "",
            "summary": "Completed draft summary." if complete else "",
            "content": (
                "This completed draft contains enough career advice "
                "content to satisfy every publication requirement."
                if complete
                else "Unfinished content"
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


def prepare_draft(context, post_id, complete=False):
    context["post_id"] = post_id
    context["post_title"] = create_draft(post_id, complete)


# =====================================
# SCENARIO 1
# =====================================


@given("the admin is creating a new career advice post")
def creating_new_post(context):
    context["post_title"] = f"Unfinished Advice {uuid4().hex}"


@when("the admin selects the save as draft option")
def save_as_draft(client, context):
    context["response"] = client.post(
        "/api/admin/career-advice",
        json={
            "title": context["post_title"],
            "category": "",
            "summary": "",
            "content": "Unfinished content",
            "imageUrl": "",
            "action": "draft",
        },
    )


@then('the system should save the post with a "Draft" status')
def verify_draft_saved(context):
    response = context["response"]
    assert response.status_code == 201

    result = response.json()
    assert result["success"] is True
    assert result["status"] == "Draft"
    context["post_id"] = result["id"]

    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["title"] == context["post_title"]
    assert post["status"] == "Draft"
    assert post["publicationDate"] is None


# =====================================
# SCENARIO 2
# =====================================


@given("the admin has saved one or more draft career advice posts")
def saved_drafts(context, post_id):
    prepare_draft(context, post_id)


@when("the admin accesses the career advice management section")
def access_drafts_management(client, context):
    context["response"] = client.get(
        "/admin/career-advice/drafts",
        follow_redirects=False,
    )


@then("the system should display the list of saved draft posts")
def verify_draft_list(context):
    response = context["response"]
    assert response.status_code == 200
    assert context["post_title"] in response.text


# =====================================
# SCENARIO 3
# =====================================


@given("the admin has a saved draft career advice post")
def saved_draft(context, post_id):
    prepare_draft(context, post_id)


@when("the admin selects the draft post")
def select_draft_post(client, context):
    context["response"] = client.get(
        f"/admin/career-advice/{context['post_id']}/edit",
        follow_redirects=False,
    )


@then("the system should display the draft content")
def verify_draft_content(context):
    response = context["response"]
    assert response.status_code == 200
    assert context["post_title"] in response.text
    assert "Unfinished content" in response.text


@then("allow the admin to continue editing it")
def verify_edit_page_available(context):
    response = context["response"]
    assert response.status_code == 200
    assert "<form" in response.text.lower()


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has completed editing a draft career advice post")
def completed_draft(context, post_id):
    prepare_draft(context, post_id, complete=True)


@when("the admin selects the publish option")
def publish_draft(client, context):
    context["response"] = client.post(f"/api/admin/career-advice/{context['post_id']}/publish")


@then('the system should change the post status from "Draft" to "Published"')
def verify_published_status(context):
    assert context["response"].status_code == 200
    post = db.collection("career_advice").document(context["post_id"]).get().to_dict()
    assert post is not None
    assert post["status"] == "Published"
    assert post["publicationDate"] is not None


@then("make the post available to job seekers")
def verify_available_to_job_seekers(client, context):
    response = client.get("/career-advice")
    assert response.status_code == 200
    assert context["post_title"] in response.text


# =====================================
# NORMAL TEST
# =====================================


def test_save_unfinished_post_as_draft(client):
    title = f"Normal Draft Test {uuid4().hex}"
    response = client.post(
        "/api/admin/career-advice",
        json={
            "title": title,
            "category": "",
            "summary": "",
            "content": "Unfinished",
            "imageUrl": "",
            "action": "draft",
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "Draft"

    try:
        post = db.collection("career_advice").document(result["id"]).get().to_dict()
        assert post is not None
        assert post["status"] == "Draft"
    finally:
        db.collection("career_advice").document(result["id"]).delete()


# =====================================
# NEGATIVE TEST
# =====================================


def test_save_draft_without_title(client):
    response = client.post(
        "/api/admin/career-advice",
        json={
            "title": "",
            "category": "",
            "summary": "",
            "content": "Unfinished",
            "imageUrl": "",
            "action": "draft",
        },
    )
    assert response.status_code == 422
    assert "Title is required." in response.json()["detail"]
