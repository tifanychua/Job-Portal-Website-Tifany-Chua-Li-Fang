from __future__ import annotations

from datetime import datetime

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
# Test Applicant
# ==================================================

APPLICANT_ID = "applicant001"


# ==================================================
# Helper Function
# ==================================================

def create_test_experience():

    doc_ref = db.collection("job_seeker_experience").document()

    doc_ref.set({

        "applicant_id": APPLICANT_ID,

        "job_title": "Test Engineer",

        "company_name": "Test Company",

        "employment_type": "Full-Time",

        "location": "Kuala Lumpur",

        "start_date": "2024-01",

        "end_date": "",

        "currently_working": False,

        "description": "Temporary test record",

        "created_at": datetime.utcnow(),

        "updated_at": datetime.utcnow()

    })

    return doc_ref.id


# ==================================================
# Acceptance Test 1
# Delete experience successfully
# ==================================================

def test_delete_experience_success(client):

    document_id = create_test_experience()

    response = client.post(
        f"/delete-experience/{document_id}",
        follow_redirects=False
    )

    assert response.status_code == 303

    print("✅ Acceptance Test Passed: Work experience deleted successfully.")


# ==================================================
# Acceptance Test 2
# Redirect after delete
# ==================================================

def test_redirect_after_delete(client):

    document_id = create_test_experience()

    response = client.post(
        f"/delete-experience/{document_id}",
        follow_redirects=False
    )

    assert response.status_code == 303

    assert response.headers["location"] == "/manageExperience"

    print("✅ Acceptance Test Passed: Redirected to Manage Experience page.")


# ==================================================
# Negative Test
# Delete invalid experience
# ==================================================

def test_delete_invalid_experience(client):

    response = client.post(
        "/delete-experience/INVALID_DOCUMENT_ID",
        follow_redirects=False
    )

    assert response.status_code == 303

    print("✅ Negative Test Passed: Invalid work experience handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/deleteExperience.feature")


# ==================================================
# Context
# ==================================================

class Context:

    def __init__(self):

        self.response = None

        self.document_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Successfully delete experience
# ==================================================

@given("a work experience record exists for the job seeker")
def existing_record(context):

    context.document_id = create_test_experience()


@when("the job seeker deletes the work experience record")
def delete_record(client, context):

    context.response = client.post(
        f"/delete-experience/{context.document_id}",
        follow_redirects=False
    )


@then("the system should redirect the job seeker to the Manage Experience page")
def verify_redirect(context):

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/manageExperience"

    print("✅ Scenario Passed: Work experience deleted successfully.")


# ==================================================
# Scenario 2
# Delete invalid experience
# ==================================================

@given("the work experience record does not exist")
def invalid_record(context):

    context.document_id = "INVALID_DOCUMENT_ID"


@when("the job seeker attempts to delete the work experience record")
def delete_invalid(client, context):

    context.response = client.post(
        f"/delete-experience/{context.document_id}",
        follow_redirects=False
    )


@then("the system should handle the request appropriately")
def verify_invalid(context):

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/manageExperience"

    print("✅ Scenario Passed: Invalid work experience handled successfully.")