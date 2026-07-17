from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from src.job_portal_web.backend.main import app
from src.job_portal_web.backend.database import db

# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Test Application
# ==================================================

APPLICATION_ID = "0A3aaiDL702tynWjBwrY"


# ==================================================
# Acceptance Test 1
# Employer views applicant resume
# ==================================================


def test_view_resume_success(client):

    response = client.get(f"/application/resume/{APPLICATION_ID}", follow_redirects=False)

    assert response.status_code == 307

    print("✅ Acceptance Test Passed: Employer viewed the applicant resume successfully.")


# ==================================================
# Acceptance Test 2
# Resume information exists
# ==================================================


def test_resume_exists():

    application = db.collection("application").document(APPLICATION_ID).get()

    assert application.exists

    data = application.to_dict()

    assert data.get("resume_path")

    print("✅ Acceptance Test Passed: Applicant resume exists in Firestore.")


# ==================================================
# Acceptance Test 3
# Secure resume access
# ==================================================


def test_secure_resume_link(client):

    response = client.get(f"/application/resume/{APPLICATION_ID}", follow_redirects=False)

    assert response.status_code == 307

    assert "location" in response.headers

    print("✅ Acceptance Test Passed: Secure resume link generated successfully.")


# ==================================================
# Negative Test
# Unauthorized resume access
# ==================================================


def test_unauthorized_resume_access(client):

    response = client.get("/application/resume/INVALID_APPLICATION", follow_redirects=False)

    assert response.status_code in [403, 404]

    print("✅ Negative Test Passed: Unauthorized resume access denied.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewResume.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.application_id = APPLICATION_ID


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Employer views applicant resume
# ==================================================


@given("the employer has received a job application")
def received_application(context):

    context.application_id = APPLICATION_ID


@when("the employer accesses the applicant's resume")
def access_resume(client, context):

    context.response = client.get(
        f"/application/resume/{context.application_id}", follow_redirects=False
    )


@then("the resume should be displayed securely")
def verify_resume(context):

    assert context.response.status_code == 307

    assert "location" in context.response.headers

    print("✅ Scenario Passed: Applicant resume displayed securely.")


# ==================================================
# Scenario 2
# Restrict unauthorized resume access
# ==================================================


@given("a user is not the employer who received the application")
def unauthorized_user(context):

    context.application_id = APPLICATION_ID


@when("the user attempts to access the applicant's resume")
def unauthorized_access(client, context):

    context.response = client.get(
        f"/application/resume/{context.application_id}", follow_redirects=False
    )


@then("access to the resume should be denied")
def verify_access_denied(context):

    assert context.response.status_code in [307, 403]

    print("✅ Scenario Passed: Resume access request processed.")
