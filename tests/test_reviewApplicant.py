from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Test Application
# ==================================================

APPLICATION_ID = "F2oXK9MYudHaFzREkgxD"


# ==================================================
# Acceptance Test 1
# Employer reviews applicant
# ==================================================


def test_review_applicant_success(client):

    response = client.put(f"/application/{APPLICATION_ID}/status", json={"status": "Reviewed"})

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Employer marked the application as Reviewed successfully.")


# ==================================================
# Acceptance Test 2
# Applicant status updated
# ==================================================


def test_applicant_status_updated(client):

    client.put(f"/application/{APPLICATION_ID}/status", json={"status": "Reviewed"})

    doc = db.collection("application").document(APPLICATION_ID).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Reviewed"

    print("✅ Acceptance Test Passed: Applicant status updated to Reviewed successfully.")


# ==================================================
# Acceptance Test 3
# Status saved in Firestore
# ==================================================


def test_reviewed_saved_database():

    doc = db.collection("application").document(APPLICATION_ID).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Reviewed"

    print("✅ Acceptance Test Passed: Reviewed applicant status saved in database.")


# ==================================================
# Negative Test
# ==================================================


def test_review_invalid_application(client):

    response = client.put("/application/INVALID_APPLICATION/status", json={"status": "Reviewed"})

    assert response.status_code == 404

    print("✅ Negative Test Passed: Invalid application handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/reviewApplicant.feature")


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
# Employer marks an application as Reviewed
# ==================================================


@given("the employer has received job applications")
def received_applications(context):

    context.application_id = APPLICATION_ID


@when("the employer marks an application as Reviewed")
def review_application(client, context):

    context.response = client.put(
        f"/application/{context.application_id}/status", json={"status": "Reviewed"}
    )


@then('the application status should be updated to "Reviewed"')
def verify_reviewed(context):

    assert context.response.status_code == 200

    doc = db.collection("application").document(context.application_id).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Reviewed"

    print("✅ Scenario Passed: Application status updated to Reviewed.")


# ==================================================
# Scenario 2
# Save reviewed application status
# ==================================================


@given("the employer has marked an application as Reviewed")
def reviewed_application(client, context):

    context.application_id = APPLICATION_ID

    client.put(f"/application/{context.application_id}/status", json={"status": "Reviewed"})


@when("the update process is completed")
def update_completed(context):

    pass


@then("the updated application status should be saved in the database")
def verify_saved(context):

    doc = db.collection("application").document(context.application_id).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Reviewed"

    print("✅ Scenario Passed: Reviewed application status saved in database.")
