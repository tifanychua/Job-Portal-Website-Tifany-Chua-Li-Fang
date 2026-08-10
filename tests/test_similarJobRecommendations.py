"""Acceptance + unit tests for the "Similar job recommendations" story.

Exercises the real GET /jobs/{job_id} route (job_portal_web.backend.
job_information), whose `similar_jobs` context variable is scored by
matching category / job_title / location against other Active jobs.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend.main import app

COMPANY_ID = "COMP001"

scenarios("features/similarJobRecommendations.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "verified": True})
    return db


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_job(fake_db, job_id, *, title, category, location, status="Active"):
    fake_db.seed(
        "job_list",
        job_id,
        {
            "job_title": title,
            "category": category,
            "location": location,
            "company_id": COMPANY_ID,
            "status": status,
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
# Scenario: Display similar job recommendations
# ==================================================


@given("the job seeker is viewing a job posting")
def viewing_job_posting(fake_db, context):
    context.job_id = "JOB_MAIN"
    seed_job(fake_db, context.job_id, title="Backend Engineer", category="IT", location="KL")
    fake_db.seed(
        "job_list",
        "JOB_SIMILAR_1",
        {
            "job_title": "Backend Developer",
            "category": "IT",
            "location": "Penang",
            "company_id": COMPANY_ID,
            "status": "Active",
        },
    )


@when("the job details page is loaded")
def job_details_page_loaded(client, context):
    context.response = client.get(f"/jobs/{context.job_id}")


@then(
    "the system should display a list of similar job recommendations based on the selected job posting"
)
def assert_similar_jobs_displayed(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert 'href="/jobs/JOB_SIMILAR_1"' in page
    assert "Backend Developer" in page


# ==================================================
# Scenario: Recommend jobs based on job attributes
# ==================================================


@when("the system generates job recommendations")
def system_generates_recommendations(client, context):
    context.response = client.get(f"/jobs/{context.job_id}")


@then(
    "the system should recommend jobs with similar attributes such as job position, category or location"
)
def assert_recommendations_match_attributes(context):
    assert context.response.status_code == 200
    page = context.response.text
    # Matches on category ("IT") pulled in JOB_SIMILAR_1 even though the
    # location and exact title differ -- confirming the score is attribute
    # based rather than an exact-job match.
    assert 'href="/jobs/JOB_SIMILAR_1"' in page


# ==================================================
# Scenario: View details of recommended jobs
# ==================================================


@given("the system has displayed similar job recommendations")
def similar_jobs_displayed(fake_db, client, context):
    context.job_id = "JOB_MAIN_2"
    seed_job(fake_db, context.job_id, title="Data Analyst", category="Data", location="KL")
    context.recommended_id = "JOB_SIMILAR_2"
    seed_job(
        fake_db, context.recommended_id, title="Data Scientist", category="Data", location="Johor"
    )

    response = client.get(f"/jobs/{context.job_id}")
    assert f'href="/jobs/{context.recommended_id}"' in response.text


@when("the job seeker selects a recommended job posting")
def select_recommended_job(client, context):
    context.response = client.get(f"/jobs/{context.recommended_id}")


@then("the system should display the details of the selected job posting")
def assert_recommended_job_details(context):
    assert context.response.status_code == 200
    assert "Data Scientist" in context.response.text


# ==================================================
# Scenario: No similar jobs available
# ==================================================


@given("the job seeker is viewing a job posting with no matching opportunities")
def viewing_job_with_no_matches(fake_db, context):
    context.job_id = "JOB_LONELY"
    seed_job(fake_db, context.job_id, title="Unique Role", category="Niche", location="Sabah")


@then("the system should display a message indicating that no similar jobs are currently available")
def assert_no_similar_jobs_message(context):
    assert context.response.status_code == 200
    assert "No similar jobs found." in context.response.text
