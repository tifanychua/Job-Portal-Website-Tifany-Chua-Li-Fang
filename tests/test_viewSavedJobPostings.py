"""Acceptance + unit tests for the "View saved job postings" story."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import savedJob
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
COMPANY_ID = "COMP001"

scenarios("features/viewSavedJobPostings.feature")


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
    def fake_job_seeker_id(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID

    monkeypatch.setattr(savedJob, "_get_current_job_seeker_id", fake_job_seeker_id)


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
            "status": "Active",
            "job_desc": "Build things.",
        },
    )


def seed_saved(fake_db, job_id):
    fake_db.seed(
        "saved_job",
        f"{JOB_SEEKER_ID}_{job_id}",
        {
            "job_seeker_id": JOB_SEEKER_ID,
            "job_id": job_id,
            "saved_at": datetime.now(timezone.utc),
        },
    )


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.job_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: View saved job postings list
# ==================================================


@given("the job seeker has saved one or more job postings")
def given_saved_postings(fake_db, context):
    context.job_id = "JOB_LIST_1"
    seed_job(fake_db, context.job_id, title="Data Analyst")
    seed_saved(fake_db, context.job_id)


@when("the job seeker accesses the saved jobs section")
def access_saved_jobs_section(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display a list of all saved job postings")
def assert_saved_list_displayed(context):
    assert context.response.status_code == 200
    assert f'data-id="{context.job_id}"' in context.response.text
    assert "Data Analyst" in context.response.text


# ==================================================
# Scenario: View details of a saved job posting
# ==================================================


@given("the job seeker is viewing the saved jobs list")
def viewing_saved_jobs_list(fake_db, client, context):
    context.job_id = "JOB_DETAIL_1"
    seed_job(fake_db, context.job_id, title="Cloud Engineer")
    seed_saved(fake_db, context.job_id)
    response = client.get("/saved-jobs")
    assert f'data-id="{context.job_id}"' in response.text


@when("the job seeker selects a saved job posting")
def select_saved_job_posting(client, context):
    context.response = client.get(f"/jobs/{context.job_id}")


@then("the system should display the complete details of the selected job posting")
def assert_job_details_displayed(context):
    assert context.response.status_code == 200
    assert "Cloud Engineer" in context.response.text
    assert "TARUMT Sdn Bhd" in context.response.text


# ==================================================
# Scenario: Saved jobs list is empty
# ==================================================


@given("the job seeker has no saved job postings")
def given_no_saved_postings(context):
    pass


@then("the system should display a message indicating that no saved job postings are available")
def assert_empty_message(context):
    page = context.response.text
    assert "No saved jobs yet" in page
    assert '<div class="saved-empty" id="savedEmpty" style="display:none">' not in page


# ==================================================
# Scenario: Access saved job postings after login
# ==================================================


@given("the job seeker has previously saved job postings")
def given_previously_saved(fake_db, context):
    context.job_id = "JOB_AFTER_LOGIN"
    seed_job(fake_db, context.job_id, title="QA Engineer")
    seed_saved(fake_db, context.job_id)


@when("the job seeker logs into the system and accesses the saved jobs section")
def login_and_access(client, context):
    # fake_login already establishes the session; a fresh request against
    # /saved-jobs is equivalent to "logging in and opening the page".
    context.response = client.get("/saved-jobs")


@then(
    "the system should retrieve and display the saved job postings associated with the job seeker's account"
)
def assert_account_scoped_retrieval(context):
    assert context.response.status_code == 200
    assert f'data-id="{context.job_id}"' in context.response.text
