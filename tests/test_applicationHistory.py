"""Acceptance + unit tests for the job-seeker "Application history" story.

Exercises GET /application, GET /application/{id} (job_application.py) and,
for the status-tracking scenario, the employer-side
PUT /application/{id}/status route (routes/employerApplication.py) that
updates the same Firestore "application" document.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import job_application
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
COMPANY_ID = "COMP001"

scenarios("features/applicationHistory.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "verified": True})
    return db


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):
    def fake_current_job_seeker(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID, {"uid": JOB_SEEKER_ID, "full_name": "Test Seeker"}

    # job_application.py imports `_get_current_job_seeker` from job_apply, so
    # the name lives in job_application's own module namespace.
    monkeypatch.setattr(job_application, "_get_current_job_seeker", fake_current_job_seeker)


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_job(fake_db, job_id, *, title="Software Engineer"):
    fake_db.seed(
        "job_list",
        job_id,
        {
            "job_title": title,
            "company_id": COMPANY_ID,
            "location": "Kuala Lumpur",
            "employment_type": "Full-time",
            "category": "IT",
        },
    )


def seed_application(fake_db, app_id, job_id, *, status="Submitted"):
    fake_db.seed(
        "application",
        app_id,
        {
            "job_id": job_id,
            "job_seeker_id": JOB_SEEKER_ID,
            "status": status,
            "resume_filename": "resume.pdf",
            "resume_path": "resumes/resume.pdf",
            "cover_letter": "",
            "answers": {},
            "created_at": datetime.now(timezone.utc),
            "updated_on": datetime.now(timezone.utc),
        },
    )


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.application_id = None
        self.job_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: View submitted job applications
# ==================================================


@given("the job seeker has submitted one or more job applications")
def given_submitted_applications(fake_db, context):
    context.job_id = "JOB_HIST_1"
    context.application_id = "APP_HIST_1"
    seed_job(fake_db, context.job_id, title="Backend Developer")
    seed_application(fake_db, context.application_id, context.job_id)


@when("the job seeker accesses the application history section")
def access_application_history(client, context):
    context.response = client.get("/application")


@then("the system should display a list of all submitted job applications")
def assert_applications_listed(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert "Backend Developer" in page
    assert f'/application/{context.application_id}' in page
    assert "Submitted" in page


# ==================================================
# Scenario: View application status details
# ==================================================


@given("the job seeker is viewing the application history list")
def viewing_application_history_list(fake_db, client, context):
    context.job_id = "JOB_HIST_2"
    context.application_id = "APP_HIST_2"
    seed_job(fake_db, context.job_id, title="Mobile Developer")
    seed_application(fake_db, context.application_id, context.job_id)
    response = client.get("/application")
    assert f'/application/{context.application_id}' in response.text


@when("the job seeker selects a specific application")
def select_specific_application(client, context):
    context.response = client.get(f"/application/{context.application_id}")


@then(
    "the system should display the application details including job position, "
    "company information, submission date, and current application status"
)
def assert_application_details(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert "Mobile Developer" in page
    assert "TARUMT Sdn Bhd" in page
    assert "Submitted" in page


# ==================================================
# Scenario: Track application progress
# ==================================================


@given("the job seeker has submitted a job application")
def given_submitted_application(fake_db, context):
    context.job_id = "JOB_HIST_3"
    context.application_id = "APP_HIST_3"
    seed_job(fake_db, context.job_id, title="DevOps Engineer")
    seed_application(fake_db, context.application_id, context.job_id, status="Submitted")


@when("the employer updates the application status")
def employer_updates_status(client, context):
    context.response = client.put(
        f"/application/{context.application_id}/status", json={"status": "shortlisted"}
    )
    assert context.response.status_code == 200


@then(
    "the system should update and display the latest application status "
    "in the job seeker's application history"
)
def assert_status_updated(client, context):
    detail_response = client.get(f"/application/{context.application_id}")
    assert detail_response.status_code == 200
    assert "Shortlisted" in detail_response.text


# ==================================================
# Scenario: No application history available
# ==================================================


@given("the job seeker has not submitted any job applications")
def given_no_applications(context):
    pass


@then("the system should display a message indicating that no application records are available")
def assert_no_applications_message(context):
    assert context.response.status_code == 200
    assert "No Applications Found" in context.response.text
