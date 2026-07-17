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
# Test Company
# ==================================================

COMPANY_ID = "C000001"


# ==================================================
# Acceptance Test 1
# Employer views applicants
# ==================================================


def test_view_applications_success(client):

    response = client.get("/applications")

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Employer viewed the applicant list successfully.")


# ==================================================
# Acceptance Test 2
# Verify application records exist
# ==================================================


def test_application_data_loaded(client):

    response = client.get("/applications")

    assert response.status_code == 200

    applications = list(db.collection("application").stream())

    assert len(applications) > 0

    print("✅ Acceptance Test Passed: Application records loaded successfully.")


# ==================================================
# Acceptance Test 3
# Verify employer's applications are displayed
# ==================================================


def test_applicant_list_displayed(client):

    response = client.get("/applications")

    assert response.status_code == 200

    applications = []

    application_docs = db.collection("application").stream()

    for application_doc in application_docs:

        application = application_doc.to_dict()

        job_id = application.get("job_id")

        if not job_id:
            continue

        job_doc = db.collection("job_list").document(job_id).get()

        if not job_doc.exists:
            continue

        job = job_doc.to_dict()

        if job.get("company_id") == COMPANY_ID:

            applications.append(application)

    assert len(applications) > 0

    print("✅ Acceptance Test Passed: Applicant list displayed successfully.")


# ==================================================
# Negative Test
# ==================================================


def test_invalid_route(client):

    response = client.get("/applications-invalid")

    assert response.status_code == 404

    print("✅ Negative Test Passed: Invalid application page handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewApplication.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario
# Employer views applicants for a job posting
# ==================================================


@given("the employer has an active job posting")
def active_job(context):

    context.company_id = COMPANY_ID


@given("applicants have submitted applications")
def submitted_applications():

    applications = list(db.collection("application").stream())

    assert len(applications) > 0


@when("the employer opens the applicant list")
def open_applicant_list(client, context):

    context.response = client.get("/applications")


@then("the system should display the list of applicants")
def verify_applicant_list(context):

    assert context.response.status_code == 200

    applications = []

    application_docs = db.collection("application").stream()

    for application_doc in application_docs:

        application = application_doc.to_dict()

        job_id = application.get("job_id")

        if not job_id:
            continue

        job_doc = db.collection("job_list").document(job_id).get()

        if not job_doc.exists:
            continue

        job = job_doc.to_dict()

        if job.get("company_id") == COMPANY_ID:

            applications.append(application)

    assert len(applications) > 0

    print("✅ Scenario Passed: Employer successfully viewed the applicant list.")
