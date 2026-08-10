"""Acceptance + unit tests for the "Remove saved job postings" story.

The last scenario ("Attempt to remove a job posting that is not saved")
exercises DELETE /api/saved-jobs/{job_id} in job_portal_web.backend.
savedJob, which now returns 404 with a "not saved" message instead of
silently succeeding when the job wasn't actually on the job seeker's
saved list.
"""

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

scenarios("features/removeSavedJobPosting.feature")


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
# Scenario: Remove a saved job posting
# ==================================================


@given("the job seeker has saved one or more job postings")
def given_saved_postings(fake_db, context):
    context.job_id = "JOB_REMOVE_1"
    seed_job(fake_db, context.job_id)
    seed_saved(fake_db, context.job_id)


@when("the job seeker selects the remove option for a saved job posting")
def select_remove_option(client, context):
    context.response = client.delete(f"/api/saved-jobs/{context.job_id}")


@then("the system should remove the selected job posting from the saved jobs list")
def assert_removed(fake_db, context):
    assert context.response.status_code == 200
    assert not fake_db.exists("saved_job", saved_doc_id(context.job_id))


# ==================================================
# Scenario: Confirm removal of saved job posting
# ==================================================


@given("the job seeker has selected a saved job posting to remove")
def selected_job_to_remove(fake_db, context):
    context.job_id = "JOB_REMOVE_2"
    seed_job(fake_db, context.job_id)
    seed_saved(fake_db, context.job_id)


@when("the removal action is completed")
def removal_action_completed(client, context):
    context.response = client.delete(f"/api/saved-jobs/{context.job_id}")


@then("the system should display a confirmation message indicating that the job posting has been removed")
def assert_confirmation_message(context):
    body = context.response.json()
    assert body["success"] is True
    assert body["saved"] is False
    assert body["message"]


# ==================================================
# Scenario: View updated saved jobs list after removal
# ==================================================


@given("the job seeker has removed a saved job posting")
def removed_a_saved_posting(fake_db, client, context):
    context.job_id = "JOB_REMOVE_3"
    seed_job(fake_db, context.job_id)
    seed_saved(fake_db, context.job_id)
    response = client.delete(f"/api/saved-jobs/{context.job_id}")
    assert response.status_code == 200


@when("the job seeker accesses the saved jobs section")
def access_saved_jobs_section(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display the updated list without the removed job posting")
def assert_updated_list(context):
    assert context.response.status_code == 200
    assert f'data-id="{context.job_id}"' not in context.response.text


# ==================================================
# Scenario: Attempt to remove a job posting that is not saved
# ==================================================


@given("the job seeker has not saved the selected job posting")
def job_not_saved(fake_db, context):
    context.job_id = "JOB_NEVER_SAVED"
    seed_job(fake_db, context.job_id)
    assert not fake_db.exists("saved_job", saved_doc_id(context.job_id))


@when("the job seeker attempts to remove the job posting from saved jobs")
def attempt_remove_unsaved(client, context):
    context.response = client.delete(f"/api/saved-jobs/{context.job_id}")


@then("the system should prevent the removal action and display an appropriate message")
def assert_removal_prevented(context):
    body = context.response.json()
    assert context.response.status_code == 404 or "not saved" in body.get("message", "").lower()
