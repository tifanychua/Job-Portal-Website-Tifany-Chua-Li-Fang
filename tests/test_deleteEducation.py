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
# Test Applicant
# ==================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ==================================================
# Helper Function
# ==================================================


def create_test_education():

    doc_ref = db.collection("education").document()

    doc_ref.set(
        {
            "applicant_id": APPLICANT_ID,
            "qualification": "Bachelor of Computer Science",
            "institution": "UTAR",
            "field_of_study": "Software Engineering",
            "start_date": "2021-01",
            "end_date": "2024-12",
            "current_study": False,
            "grade": "3.80",
            "description": "Temporary education record",
        }
    )

    return doc_ref.id


# ==================================================
# Acceptance Test 1
# Delete education successfully
# ==================================================


def test_delete_education_success(client):

    education_id = create_test_education()

    response = client.post(f"/delete-education/{education_id}", follow_redirects=False)

    assert response.status_code == 303

    print("✅ Acceptance Test Passed: Education deleted successfully.")


# ==================================================
# Acceptance Test 2
# Redirect after delete
# ==================================================


def test_redirect_after_delete(client):

    education_id = create_test_education()

    response = client.post(f"/delete-education/{education_id}", follow_redirects=False)

    assert response.status_code == 303

    assert response.headers["location"] == "/manage-education"

    print("✅ Acceptance Test Passed: Redirected to Manage Education page.")


# ==================================================
# Negative Test
# ==================================================


def test_delete_invalid_education(client):

    response = client.post("/delete-education/INVALID_DOCUMENT_ID", follow_redirects=False)

    assert response.status_code == 303

    print("✅ Negative Test Passed: Invalid education handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/deleteEducation.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None
        self.education_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Delete education successfully
# ==================================================


@given("an education record exists for the job seeker")
def existing_record(context):

    context.education_id = create_test_education()


@when("the job seeker deletes the education record")
def delete_record(client, context):

    context.response = client.post(
        f"/delete-education/{context.education_id}", follow_redirects=False
    )


@then("the system should redirect the job seeker to the Manage Education page")
def verify_redirect(context):

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/manage-education"

    print("✅ Scenario Passed: Education deleted successfully.")


# ==================================================
# Scenario 2
# Delete invalid education
# ==================================================


@given("the education record does not exist")
def invalid_record(context):

    context.education_id = "INVALID_DOCUMENT_ID"


@when("the job seeker attempts to delete the education record")
def delete_invalid(client, context):

    context.response = client.post(
        f"/delete-education/{context.education_id}", follow_redirects=False
    )


@then("the system should handle the request appropriately")
def verify_invalid(context):

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/manage-education"

    print("✅ Scenario Passed: Invalid education handled successfully.")
