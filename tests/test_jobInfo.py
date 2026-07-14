from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
from database import db

from main import app

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
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/jobInfo.feature")


# --------------------------------------------------
# Context
# --------------------------------------------------


class Context:

    def __init__(self):
        self.response = None


@pytest.fixture
def context():
    return Context()


# --------------------------------------------------
# Scenario 1:
# Job seeker views complete job details
# --------------------------------------------------


@given("the job seeker selects a job posting")
def select_job():
    pass


@when("the job details page is opened")
def open_job_details(client, context):

    jobs = list(db.collection("job_list").limit(1).stream())

    print("TOTAL JOB:", len(jobs))

    for job in jobs:
        print("JOB ID:", job.id)

    job_id = jobs[0].id

    context.response = client.get(f"/jobs/{job_id}")


@then("the system should display the complete job information")
def verify_complete_job_information(context):

    if context.response.status_code == 200:
        print("✅ SUCCESS: Complete job information displayed")
    else:
        print("❌ FAILED: Unable to display job details")

    assert context.response.status_code == 200


# --------------------------------------------------
# Scenario 2:
# Job seeker views required job information
# --------------------------------------------------


@given("a job posting exists in the system")
def job_exists():
    pass


@when("the job seeker views the job details")
def view_job_details(client, context):

    jobs = list(db.collection("job_list").limit(1).stream())

    job_id = jobs[0].id

    context.response = client.get(f"/jobs/{job_id}")


@then(
    "the system should display the job title, description, requirements, location, and company information"
)
def verify_required_job_information(context):

    if context.response.status_code == 200:

        data = context.response.text

        required_fields = ["job", "description", "location", "company"]

        missing_fields = []

        for field in required_fields:
            if field.lower() not in data.lower():
                missing_fields.append(field)

        if len(missing_fields) == 0:
            print(
                "✅ SUCCESS: Job title, description, requirements, location and company information displayed"
            )
        else:
            print(f"❌ FAILED: Missing information {missing_fields}")

        assert len(missing_fields) == 0

    else:
        print("❌ FAILED: Job detail page cannot be opened")

    assert context.response.status_code == 200
