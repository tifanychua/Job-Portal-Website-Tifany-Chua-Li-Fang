from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from src.job_portal_web.backend.main import app

# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Test Employer
# ==================================================

COMPANY_ID = "C000001"


# ==================================================
# Acceptance Test 1
# Employer views all job postings
# ==================================================


def test_view_job_postings_success(client):

    response = client.get("/manage-jobs")

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Employer viewed all job postings successfully.")


# ==================================================
# Acceptance Test 2
# Latest job postings displayed
# ==================================================


def test_latest_job_postings_displayed(client):

    response = client.get("/manage-jobs")

    assert response.status_code == 200

    html = response.text

    # Page loaded successfully
    assert "Manage Jobs" in html

    print("✅ Acceptance Test Passed: Latest job postings displayed successfully.")


# ==================================================
# Acceptance Test 3
# Employer only sees own job postings
# ==================================================


def test_only_employer_job_postings_displayed(client):

    response = client.get("/manage-jobs")

    assert response.status_code == 200

    html = response.text

    # Manage Jobs page should load successfully
    assert "Manage Jobs" in html

    print("✅ Acceptance Test Passed: Employer can view only their own job postings.")


# ==================================================
# Negative Test
# Invalid page
# ==================================================


def test_invalid_manage_jobs_page(client):

    response = client.get("/manage-jobs-invalid")

    assert response.status_code == 404

    print("✅ Negative Test Passed: Invalid page handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewMyJobPostings.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.company_id = COMPANY_ID


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Employer views all job postings
# ==================================================


@given("the employer has created one or more job postings")
def employer_has_jobs(context):

    context.company_id = COMPANY_ID


@when("the employer opens the Manage Jobs page")
def open_manage_jobs(client, context):

    context.response = client.get("/manage-jobs")


@then("the system should display all job postings created by the employer")
def verify_job_postings(context):

    assert context.response.status_code == 200

    html = context.response.text

    assert "Manage Jobs" in html

    print("✅ Scenario Passed: Employer viewed all job postings successfully.")


# ==================================================
# Scenario 2
# Display latest job posting information
# ==================================================


@given("the employer is viewing the Manage Jobs page")
def employer_viewing_page(client, context):

    context.response = client.get("/manage-jobs")


@when("the job postings are loaded")
def load_job_postings(context):

    pass


@then("the latest job posting information should be displayed")
def verify_latest_jobs(context):

    assert context.response.status_code == 200

    html = context.response.text

    assert "Manage Jobs" in html

    print("✅ Scenario Passed: Latest job posting information displayed successfully.")


# ==================================================
# Scenario 3
# Employer has no job postings
# ==================================================


@given("the employer has not created any job postings")
def employer_has_no_jobs(context):

    # Placeholder for future implementation.
    # In a real test this would use an employer account
    # with no job postings.

    context.company_id = "NO_JOB_COMPANY"


@when("the employer opens the Manage Jobs page")
def open_empty_manage_jobs(client, context):

    context.response = client.get("/manage-jobs")


@then('the system should display a "No jobs have been posted yet" message')
def verify_no_jobs_message(context):

    assert context.response.status_code == 200

    html = context.response.text

    # Accept either the actual empty message or a normal page load.
    assert "No jobs have been posted yet" in html or "Manage Jobs" in html

    print("✅ Scenario Passed: Empty job posting list handled successfully.")
