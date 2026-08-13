import json
import os
from base64 import b64encode
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/save_career_advice_post.feature")


@pytest.fixture
def job_seeker_id():
    return f"TEST_JOB_SEEKER_{uuid4().hex}"


@pytest.fixture
def client(job_seeker_id):
    secret_key = os.getenv("SECRET_KEY", "jobconnect-secret-key")
    session = {
        "user_type": "job_seeker",
        "applicant_id": job_seeker_id,
        "job_seeker_id": job_seeker_id,
        "user_id": job_seeker_id,
    }
    encoded = b64encode(json.dumps(session).encode("utf-8"))
    signed = TimestampSigner(str(secret_key)).sign(encoded)

    db.collection("job_seeker").document(job_seeker_id).set(
        {
            "name": "Test Job Seeker",
            "email": f"{job_seeker_id.lower()}@example.com",
            "test": True,
        }
    )

    with TestClient(app, base_url="http://testserver") as test_client:
        test_client.cookies.set(
            "session",
            signed.decode("utf-8"),
            domain="testserver.local",
            path="/",
        )
        yield test_client

    db.collection("job_seeker").document(job_seeker_id).delete()


@pytest.fixture
def context():
    return {
        "post_id": None,
        "post_title": None,
        "saved_id": None,
        "response": None,
    }


@pytest.fixture
def post_id():
    value = f"TEST_SAVE_ADVICE_{uuid4().hex}"
    yield value
    db.collection("career_advice").document(value).delete()


def saved_document_id(job_seeker_id, post_id):
    return sha256(f"{job_seeker_id}:{post_id}".encode()).hexdigest()


def create_published_post(post_id):
    current_time = datetime.now(UTC)
    title = f"Save Career Advice Test {uuid4().hex}"
    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": "Career Development",
            "summary": "Useful saved career advice.",
            "content": (
                "This published career advice post contains enough "
                "content for the job seeker save feature test."
            ),
            "imageUrl": "",
            "status": "Published",
            "createdAt": current_time,
            "updatedAt": current_time,
            "publicationDate": current_time,
            "test": True,
        }
    )
    return title


def prepare_post(context, post_id, job_seeker_id):
    context["post_id"] = post_id
    context["post_title"] = create_published_post(post_id)
    context["saved_id"] = saved_document_id(job_seeker_id, post_id)


def save_post(client, context):
    context["response"] = client.post(f"/api/career-advice/{context['post_id']}/save")


def remove_saved_record(context):
    if context.get("saved_id"):
        db.collection("saved_career_advice").document(context["saved_id"]).delete()


# =====================================
# SCENARIO 1
# =====================================


@given("the job seeker is viewing a career advice post")
def viewing_post(client, context, post_id, job_seeker_id):
    prepare_post(context, post_id, job_seeker_id)
    response = client.get(f"/career-advice/{post_id}")
    assert response.status_code == 200
    assert context["post_title"] in response.text


@when("the job seeker selects the save option")
def select_save(client, context):
    save_post(client, context)


@then("the system should save the selected post to the job seeker's saved posts list")
def verify_post_saved(context, job_seeker_id):
    try:
        assert context["response"].status_code == 201
        document = db.collection("saved_career_advice").document(context["saved_id"]).get()
        assert document.exists
        saved = document.to_dict()
        assert saved is not None
        assert saved["jobSeekerId"] == job_seeker_id
        assert saved["careerAdviceId"] == context["post_id"]
    finally:
        remove_saved_record(context)


# =====================================
# SCENARIO 2
# =====================================


@given("the job seeker has selected a career advice post to save")
def selected_post(context, post_id, job_seeker_id):
    prepare_post(context, post_id, job_seeker_id)


@when("the save action is completed successfully")
def complete_save(client, context):
    save_post(client, context)
    assert context["response"].status_code == 201


@then(
    "the system should display a confirmation message indicating "
    "that the post has been saved successfully"
)
def verify_save_confirmation(context):
    try:
        result = context["response"].json()
        assert result["success"] is True
        assert result["saved"] is True
        assert result["message"] == "Career advice saved successfully."
    finally:
        remove_saved_record(context)


# =====================================
# SCENARIO 3
# =====================================


@given("the job seeker has saved one or more career advice posts")
def has_saved_posts(client, context, post_id, job_seeker_id):
    prepare_post(context, post_id, job_seeker_id)
    save_post(client, context)
    assert context["response"].status_code == 201


@when("the job seeker accesses the saved posts section")
def access_saved_posts(client, context):
    # The current backend marks saved articles on this page.
    context["response"] = client.get("/career-advice")


@then("the system should display a list of all saved career advice posts")
def verify_saved_posts_displayed(context):
    try:
        assert context["response"].status_code == 200
        assert context["post_title"] in context["response"].text
        assert db.collection("saved_career_advice").document(context["saved_id"]).get().exists
    finally:
        remove_saved_record(context)


# =====================================
# SCENARIO 4
# =====================================


@given("the job seeker has already saved a career advice post")
def already_saved(client, context, post_id, job_seeker_id):
    prepare_post(context, post_id, job_seeker_id)
    save_post(client, context)
    assert context["response"].status_code == 201


@when("the job seeker selects the save option for the same post again")
def save_same_post_again(client, context):
    save_post(client, context)


@then("the system should prevent a duplicate entry from being created")
def verify_no_duplicate(context, job_seeker_id):
    records = [
        document
        for document in (
            db.collection("saved_career_advice").where("jobSeekerId", "==", job_seeker_id).stream()
        )
        if (document.to_dict() or {}).get("careerAdviceId") == context["post_id"]
    ]
    assert len(records) == 1


@then("indicate that the post has already been saved")
def verify_already_saved_message(context):
    try:
        assert context["response"].status_code == 200
        result = context["response"].json()
        assert result["saved"] is True
        assert result["message"] == "Career advice is already saved."
    finally:
        remove_saved_record(context)


# =====================================
# NEGATIVE TEST
# =====================================


def test_save_invalid_career_advice_post(client):
    invalid_post_id = f"INVALID_POST_{uuid4().hex}"
    response = client.post(f"/api/career-advice/{invalid_post_id}/save")
    assert response.status_code == 404
    assert response.json()["detail"] == "Career advice post not found."
