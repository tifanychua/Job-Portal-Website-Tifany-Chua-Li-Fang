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
# Employer accepts applicant
# ==================================================


def test_accept_applicant_success(client):

    response = client.put(f"/application/{APPLICATION_ID}/status", json={"status": "Offered"})

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Employer accepted the applicant successfully.")


# ==================================================
# Acceptance Test 2
# Applicant status updated
# ==================================================


def test_applicant_status_updated(client):

    client.put(f"/application/{APPLICATION_ID}/status", json={"status": "Offered"})

    doc = db.collection("application").document(APPLICATION_ID).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Offered"

    print("✅ Acceptance Test Passed: Applicant status updated successfully.")


# ==================================================
# Acceptance Test 3
# Status saved in Firestore
# ==================================================


def test_offered_saved_database():

    doc = db.collection("application").document(APPLICATION_ID).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Offered"

    print("✅ Acceptance Test Passed: Accepted applicant status saved in database.")


# ==================================================
# Negative Test
# ==================================================


def test_accept_invalid_application(client):

    response = client.put("/application/INVALID_APPLICATION/status", json={"status": "Offered"})

    assert response.status_code == 404

    print("✅ Negative Test Passed: Invalid application handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/acceptApplicant.feature")


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
# Employer accepts an applicant
# ==================================================


@given("the employer has received job applications")
def received_applications(context):

    context.application_id = APPLICATION_ID


@when("the employer selects an applicant to accept")
def accept_applicant(client, context):

    context.response = client.put(
        f"/application/{context.application_id}/status", json={"status": "Offered"}
    )


@then('the applicant status should be updated to "Offered"')
def verify_offered(context):

    assert context.response.status_code == 200

    doc = db.collection("application").document(context.application_id).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Offered"

    print("✅ Scenario Passed: Applicant status updated to Offered.")


# ==================================================
# Scenario 2
# Save accepted applicant status
# ==================================================


@given("the employer has accepted an applicant")
def accepted_applicant(client, context):

    context.application_id = APPLICATION_ID

    client.put(f"/application/{context.application_id}/status", json={"status": "Offered"})


@when("the acceptance action is completed")
def acceptance_completed(context):

    pass


@then("the updated applicant status should be saved in the database")
def verify_saved(context):

    doc = db.collection("application").document(context.application_id).get()

    assert doc.exists

    application = doc.to_dict()

    assert application["status"] == "Offered"

    print("✅ Scenario Passed: Accepted applicant status saved in database.")
