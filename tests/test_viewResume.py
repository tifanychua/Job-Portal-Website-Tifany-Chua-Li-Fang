from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from firebase_admin import storage
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewResume.feature")


# ==================================================
# Test Constants
# ==================================================

TEST_RESUME_PATH = "resumes/test-resume.pdf"
TEST_SIGNED_URL = "https://example.com/signed-test-resume.pdf"


# ==================================================
# Fake Firebase Storage
# ==================================================


class FakeBlob:
    def __init__(self, name: str):
        self.name = name

    def exists(self, *args, **kwargs) -> bool:
        return self.name == TEST_RESUME_PATH

    def generate_signed_url(self, *args, **kwargs) -> str:
        return TEST_SIGNED_URL


class FakeBucket:
    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(name)


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def mock_firebase_storage(monkeypatch):
    fake_bucket = FakeBucket()

    monkeypatch.setattr(
        storage,
        "bucket",
        lambda *args, **kwargs: fake_bucket,
    )


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.application_id = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Test Application Fixture
# ==================================================


@pytest.fixture
def application_id():
    test_application_id = f"TEST_RESUME_APPLICATION_{uuid4().hex}"

    document_reference = db.collection("application").document(test_application_id)

    document_reference.set(
        {
            "application_id": test_application_id,
            "resume_path": TEST_RESUME_PATH,
            "applicant_id": "TEST_APPLICANT_RESUME",
            "company_id": "TEST_COMPANY_RESUME",
            "status": "Submitted",
            "test": True,
        }
    )

    yield test_application_id

    if document_reference.get().exists:
        document_reference.delete()


# ==================================================
# Acceptance Test 1
# Employer Views Applicant Resume
# ==================================================


def test_view_resume_success(client, application_id):
    response = client.get(
        f"/application/resume/{application_id}",
        follow_redirects=False,
    )

    assert response.status_code in (302, 307), response.text
    assert "location" in response.headers
    assert response.headers["location"] == TEST_SIGNED_URL


# ==================================================
# Acceptance Test 2
# Resume Information Exists
# ==================================================


def test_resume_exists(application_id):
    application = db.collection("application").document(application_id).get()

    assert application.exists

    data = application.to_dict()

    assert data is not None
    assert data.get("resume_path") == TEST_RESUME_PATH


# ==================================================
# Acceptance Test 3
# Secure Resume Access
# ==================================================


def test_secure_resume_link(client, application_id):
    response = client.get(
        f"/application/resume/{application_id}",
        follow_redirects=False,
    )

    assert response.status_code in (302, 307), response.text
    assert "location" in response.headers
    assert response.headers["location"] == TEST_SIGNED_URL


# ==================================================
# Negative Test
# Invalid Resume Access
# ==================================================


def test_unauthorized_resume_access(client):
    invalid_application_id = f"INVALID_APPLICATION_{uuid4().hex}"

    response = client.get(
        f"/application/resume/{invalid_application_id}",
        follow_redirects=False,
    )

    assert response.status_code in (403, 404)


# ==================================================
# Scenario 1
# Employer Views Applicant Resume
# ==================================================


@given("the employer has received a job application")
def received_application(context, application_id):
    context.application_id = application_id


@when("the employer accesses the applicant's resume")
def access_resume(client, context):
    context.response = client.get(
        f"/application/resume/{context.application_id}",
        follow_redirects=False,
    )


@then("the resume should be displayed securely")
def verify_resume(context):
    response = context.response

    assert response.status_code in (302, 307), response.text
    assert "location" in response.headers
    assert response.headers["location"] == TEST_SIGNED_URL


# ==================================================
# Scenario 2
# Restrict Unauthorized Resume Access
# ==================================================


@given("a user is not the employer who received the application")
def unauthorized_user(context):
    context.application_id = f"INVALID_APPLICATION_{uuid4().hex}"


@when("the user attempts to access the applicant's resume")
def unauthorized_access(client, context):
    context.response = client.get(
        f"/application/resume/{context.application_id}",
        follow_redirects=False,
    )


@then("access to the resume should be denied")
def verify_access_denied(context):
    assert context.response.status_code in (403, 404)
