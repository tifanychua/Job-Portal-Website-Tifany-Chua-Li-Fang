"""Acceptance + unit tests for the "Save job postings" story.

Exercises the real POST/DELETE /api/saved-jobs/{job_id} routes in
job_portal_web.backend.savedJob against an in-memory fake Firestore.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import savedJob
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
COMPANY_ID = "COMP001"

scenarios("features/saveJobPosting.feature")


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
        },
    )


def saved_doc_id(job_id):
    return f"{JOB_SEEKER_ID}_{job_id}"


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
# Scenario: Save a job posting
# ==================================================


@given("the job seeker is viewing a job posting")
def viewing_job_posting(fake_db, context):
    context.job_id = "JOB_TO_SAVE"
    seed_job(fake_db, context.job_id)


@when("the job seeker selects the save option")
def select_save_option(client, context):
    context.response = client.post(f"/api/saved-jobs/{context.job_id}")


@then("the system should add the job posting to the job seeker's saved jobs list")
def assert_added_to_saved(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["saved"] is True
    assert fake_db.exists("saved_job", saved_doc_id(context.job_id))


# ==================================================
# Scenario: View saved job postings
# ==================================================


@given("the job seeker has saved one or more job postings")
def given_saved_postings(fake_db, client, context):
    context.job_id = "JOB_VIEW_1"
    seed_job(fake_db, context.job_id, title="Data Analyst")
    client.post(f"/api/saved-jobs/{context.job_id}")


@when("the job seeker accesses the saved jobs section")
def access_saved_jobs_section(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display all saved job postings")
def assert_all_saved_displayed(context):
    assert context.response.status_code == 200
    assert f'data-id="{context.job_id}"' in context.response.text


# ==================================================
# Scenario: Remove a saved job posting
# ==================================================


@given("the job seeker has saved a job posting")
def given_a_saved_posting(fake_db, client, context):
    context.job_id = "JOB_TO_UNSAVE"
    seed_job(fake_db, context.job_id)
    client.post(f"/api/saved-jobs/{context.job_id}")
    assert fake_db.exists("saved_job", saved_doc_id(context.job_id))


@when("the job seeker selects the remove save option")
def select_remove_option(client, context):
    context.response = client.delete(f"/api/saved-jobs/{context.job_id}")


@then("the system should remove the job posting from the saved jobs list")
def assert_removed_from_saved(fake_db, context):
    assert context.response.status_code == 200
    assert context.response.json()["saved"] is False
    assert not fake_db.exists("saved_job", saved_doc_id(context.job_id))


# ==================================================
# Scenario: Prevent duplicate saved job postings
# ==================================================


@given("the job seeker has already saved a job posting")
def given_already_saved(fake_db, client, context):
    context.job_id = "JOB_DUPLICATE"
    seed_job(fake_db, context.job_id)
    client.post(f"/api/saved-jobs/{context.job_id}")


@when("the job seeker attempts to save the same job posting again")
def save_again(client, context):
    context.response = client.post(f"/api/saved-jobs/{context.job_id}")


@then("the system should prevent duplicate entries in the saved jobs list")
def assert_no_duplicate(fake_db, context):
    assert context.response.status_code == 200
    matching = [
        d
        for d in fake_db.collection("saved_job").stream()
        if d.to_dict().get("job_seeker_id") == JOB_SEEKER_ID
        and d.to_dict().get("job_id") == context.job_id
    ]
    assert len(matching) == 1
