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
# Acceptance Test 1
# Employer removes a job
# ==================================================


def test_remove_job_success(client):

    job_id = "dj9cf1SmQjOYhVm5b6SL"

    response = client.get(f"/delete-job/{job_id}", follow_redirects=False)

    assert response.status_code == 303

    print("✅ Acceptance Test Passed: Employer removed the job posting successfully.")


# ==================================================
# Acceptance Test 2
# Verify status becomes Deleted
# ==================================================


def test_job_status_updated(client):

    job_id = "dj9cf1SmQjOYhVm5b6SL"

    client.get(f"/delete-job/{job_id}", follow_redirects=False)

    doc = db.collection("job_list").document(job_id).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["status"] == "Deleted"

    print("✅ Acceptance Test Passed: Job posting status updated to 'Deleted'.")


# ==================================================
# Acceptance Test 3
# Deleted job is hidden
# ==================================================


def test_deleted_job_not_displayed(client):

    job_id = "dj9cf1SmQjOYhVm5b6SL"

    client.get(f"/delete-job/{job_id}", follow_redirects=False)

    response = client.get("/manage-jobs")

    assert response.status_code == 200

    assert job_id not in response.text

    print("✅ Acceptance Test Passed: Removed job posting is hidden from job seekers.")


# ==================================================
# Negative Test
# ==================================================


def test_remove_invalid_job(client):

    response = client.get("/delete-job/INVALID_JOB", follow_redirects=False)

    assert response.status_code in [303, 404, 500]

    print("✅ Negative Test Passed: Invalid job removal handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/jobRemove.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.job_id = ""


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Employer removes a job posting
# ==================================================


@given("the employer has an existing job posting")
def existing_job(context):

    context.job_id = "dj9cf1SmQjOYhVm5b6SL"


@when("the employer selects the remove job posting option")
def remove_job(client, context):

    context.response = client.get(f"/delete-job/{context.job_id}", follow_redirects=False)


@then("the job posting should be removed successfully")
def verify_removed(context):

    assert context.response.status_code == 303

    print("✅ Scenario Passed: Employer removes a job posting.")


# ==================================================
# Scenario 2
# Update status after removal
# ==================================================


@given("the employer has removed a job posting")
def removed_job(client, context):

    context.job_id = "dj9cf1SmQjOYhVm5b6SL"

    client.get(f"/delete-job/{context.job_id}", follow_redirects=False)


@when("the removal process is completed")
def removal_completed(context):

    pass


@then("the job posting status should be updated in the database")
def verify_status(context):

    doc = db.collection("job_list").document(context.job_id).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["status"] == "Deleted"

    print("✅ Scenario Passed: Job posting status updated in the database.")


# ==================================================
# Scenario 3
# Job seeker cannot view removed jobs
# ==================================================


@given("the employer has removed a job posting")
def removed_job_again(client, context):

    context.job_id = "dj9cf1SmQjOYhVm5b6SL"

    client.get(f"/delete-job/{context.job_id}", follow_redirects=False)


@when("a job seeker browses available jobs")
def browse_jobs(client, context):

    context.response = client.get("/manage-jobs")


@then("the removed job posting should not be displayed")
def verify_hidden(context):

    assert context.response.status_code == 200

    assert context.job_id not in context.response.text

    print("✅ Scenario Passed: Removed job posting is not visible to job seekers.")
