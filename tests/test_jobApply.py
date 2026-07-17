from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client():
    """
    Shared FastAPI test client.
    """
    return TestClient(app)


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_job_seeker_submit_application(client: TestClient):
    """
    Acceptance test: Job seeker submits a job application

    Given the job seeker is viewing a job posting
    When the job seeker submits an application
    Then the application should be successfully created
    """

    job_id = "RqUW5tySLpBIjbcY7c1c"

    response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    if response.status_code in [200, 201]:
        print("✅ SUCCESS: Job seeker submits a job application")
    else:
        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code in [200, 201]


# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_view_saved_application_details(client: TestClient):
    """
    Acceptance test: Job seeker views submitted application details

    Given the job seeker has submitted a job application
    When the system retrieves the application
    Then the application details should be displayed
    """

    job_id = "RqUW5tySLpBIjbcY7c1c"

    create_response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    assert create_response.status_code in [200, 201]

    application_id = create_response.json().get("application_id")

    response = client.get(f"/application/{application_id}")

    if response.status_code == 200:
        print("✅ SUCCESS: Job seeker views submitted application details")
    else:
        print("❌ FAILED: Unable to retrieve application")

    assert response.status_code == 200


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/jobApply.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None
        self.application_id = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1:
# Submit Job Application
# --------------------------------------------------


@given("the job seeker is viewing a job posting")
def view_job():

    pass


@when("the job seeker submits an application")
def submit_application(client, context):

    job_id = "RqUW5tySLpBIjbcY7c1c"

    context.response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )


@then("the application should be successfully created")
def verify_application_created(context):

    if context.response.status_code in [200, 201]:

        print("✅ SUCCESS: Job application created successfully")

        data = context.response.json()

        context.application_id = data.get("application_id")

    else:

        print("❌ FAILED:", context.response.status_code, context.response.text)

    assert context.response.status_code in [200, 201]


# --------------------------------------------------
# Scenario 2:
# Save Application Details
# --------------------------------------------------


@given("the job seeker has submitted a job application")
def submitted_application(client, context):

    job_id = "RqUW5tySLpBIjbcY7c1c"

    response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    assert response.status_code in [200, 201]

    data = response.json()

    context.application_id = data.get("application_id")


@when("the application is processed")
def process_application(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the application details should be stored in the database")
def verify_saved(context):

    if context.response.status_code == 200:

        print("✅ SUCCESS: Application information stored in database")

    else:

        print("❌ FAILED: Application not found")

    assert context.response.status_code == 200
