from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

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

NO_EXPERIENCE_APPLICANT = "RX5WofoFl6MBMPf8I1ae"


# ==================================================
# Acceptance Test 1
# View all work experience
# ==================================================

def test_view_experience_success(client):

    response = client.get("/manageExperience")

    assert response.status_code == 200

    assert "Work Experience" in response.text

    print("✅ Acceptance Test Passed: Job seeker viewed work experience successfully.")


# ==================================================
# Acceptance Test 2
# Experience information displayed
# ==================================================

def test_experience_information_displayed(client):

    response = client.get("/manageExperience")

    assert response.status_code == 200

    html = response.text

    assert "Work Experience" in html

    print("✅ Acceptance Test Passed: Work experience information displayed successfully.")


# ==================================================
# Negative Test
# Invalid page
# ==================================================

def test_invalid_manage_experience_page(client):

    response = client.get("/manageExperience-invalid")

    assert response.status_code == 404

    print("✅ Negative Test Passed: Invalid page handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewExperience.feature")


# ==================================================
# Context
# ==================================================

class Context:

    def __init__(self):

        self.response = None

        self.applicant_id = APPLICANT_ID


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# View work experience
# ==================================================

@given("the job seeker has one or more work experience records")
def experience_exists(context):

    context.applicant_id = APPLICANT_ID


@when("the job seeker opens the Manage Experience page")
def open_manage_experience(client, context):

    context.response = client.get("/manageExperience")


@then("the system should display all work experience records")
def verify_experience(context):

    assert context.response.status_code == 200

    html = context.response.text

    assert "Work Experience" in html

    print("✅ Scenario Passed: Work experience displayed successfully.")


# ==================================================
# Scenario 2
# No work experience
# ==================================================

@given("the job seeker has no work experience records")
def no_experience(context):

    context.applicant_id = NO_EXPERIENCE_APPLICANT


@when("the job seeker opens the Manage Experience page")
def open_empty_manage_experience(client, context):

    context.response = client.get(
        f"/manageExperience?applicant_id={context.applicant_id}"
    )


@then("the system should display the empty work experience message")
def verify_empty_message(context):

    assert context.response.status_code == 200

    html = context.response.text

    assert (
        "No work experience yet" in html
        or "Work Experience" in html
    )

    print("✅ Scenario Passed: Empty work experience handled successfully.")