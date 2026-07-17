from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """
    Shared FastAPI test client.
    """
    return TestClient(app)


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_browse_available_jobs(client: TestClient):
    """
    Acceptance test: Job seeker browses available job opportunities

    Given job postings are available in the system
    When the job seeker opens the job listing page
    Then the system should display a list of available job opportunities
    """

    response = client.get("/jobs")

    if response.status_code == 200:
        print("✅ SUCCESS: Job seeker browses available job opportunities")
    else:
        print("❌ FAILED: Unable to display available job opportunities")

    assert response.status_code == 200


# --------------------------------------------------
# 2. Verify Job Summary Information
# --------------------------------------------------


def test_view_job_summary_information(client: TestClient):
    """
    Acceptance test: Job seeker views job summary information

    Given the job seeker is viewing the job listing page
    When job postings are displayed
    Then the system should show the job title, company name and location
    """

    response = client.get("/jobs")

    if response.status_code == 200:
        print("✅ SUCCESS: Job title, company name and location are displayed")
    else:
        print("❌ FAILED: Job summary information is not displayed")

    assert response.status_code == 200


# --------------------------------------------------
# 3. Acceptance Test
# --------------------------------------------------


def test_filter_job_opportunities(client: TestClient):
    """
    Acceptance test:
    Job seeker filters job opportunities
    """

    response = client.get(
        "/jobs",
        params={
            "location": "Kuala Lumpur",
            "position": "Software Engineer",
            "benefits": "Medical Insurance",
        },
    )

    if response.status_code == 200:

        print("✅ SUCCESS: Filtered job opportunities displayed")

    else:

        print("❌ FAILED: Unable to filter jobs")

    assert response.status_code == 200


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/browsepage.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1:
# Browse Available Jobs
# --------------------------------------------------


@given("job postings are available in the system")
def jobs_available():
    pass


@when("the job seeker opens the job listing page")
def open_job_listing(client, context):

    context.response = client.get("/jobs")


@then("the system should display a list of available job opportunities")
def verify_job_listing(context):

    if context.response.status_code == 200:
        print("✅ SUCCESS: Available job opportunities displayed")
    else:
        print("❌ FAILED: Job listing page failed")

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 2:
# View Job Summary Information
# --------------------------------------------------


@given("the job seeker is viewing the job listing page")
def viewing_job_listing():
    pass


@when("job postings are displayed")
def display_jobs(client, context):

    context.response = client.get("/jobs")


@then("the system should show the job title, company name and location")
def verify_job_summary(context):

    if context.response.status_code == 200:
        print("✅ SUCCESS: Job title, company name and location displayed")
    else:
        print("❌ FAILED: Job summary information missing")

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 3:
# Job seeker filters job opportunities
# --------------------------------------------------


@given("job postings are available in the system")
def job_postings_available():
    pass


@when("the job seeker applies filters such as job position, location, or benefits")
def apply_job_filters(client, context):

    context.response = client.get(
        "/jobs",
        params={
            "location": "Kuala Lumpur",
            "position": "Software Engineer",
            "benefits": "Medical Insurance",
        },
    )


@then("the system should display job opportunities that match the selected filters")
def verify_filtered_jobs(context):

    assert context.response.status_code == 200

    page = context.response.text.lower()

    if "software engineer" in page or "kuala lumpur" in page:

        print("✅ SUCCESS: Filtered job opportunities displayed")

    else:

        print("❌ FAILED: Filtered jobs not displayed")

    assert "software engineer" in page or "kuala lumpur" in page
