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


def test_upload_resume_success(client: TestClient):
    """
    Acceptance test: Job seeker uploads a resume successfully

    Given the job seeker is applying for a job
    When the job seeker uploads a resume file
    Then the resume should be uploaded successfully
    """

    job_id = "RqUW5tySLpBIjbcY7c1c"

    response = client.post(
        f"/jobs/{job_id}/apply",
        data={"cover_letter": "I am interested in this position."},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    if response.status_code == 200:
        print("✅ SUCCESS: Job seeker uploads a resume successfully")
    else:
        print("❌ FAILED: Resume upload failed")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "application_id" in data


# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_resume_information_saved(client: TestClient):
    """
    Acceptance test: Uploaded resume information is saved

    Given the job seeker has uploaded a resume
    When the system retrieves the application information
    Then the resume information should be stored
    """

    job_id = "RqUW5tySLpBIjbcY7c1c"

    upload_response = client.post(
        f"/jobs/{job_id}/apply",
        data={"cover_letter": "Test cover letter"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    assert upload_response.status_code == 200

    application_id = upload_response.json()["application_id"]

    response = client.get(f"/application/{application_id}")

    if response.status_code == 200 and "resume" in response.text.lower():

        print("✅ SUCCESS: Uploaded resume information is saved")

    else:

        print("❌ FAILED: Resume information not saved")

    assert response.status_code == 200
    assert "resume" in response.text.lower()


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/uploadResume.feature")


# --------------------------------------------------
# Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None

        self.job_id = "RqUW5tySLpBIjbcY7c1c"

        self.application_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1:
# Job seeker uploads a resume
# ==================================================


@given("the job seeker is on the resume upload page")
def resume_upload_page(client, context):

    context.response = client.get(f"/jobs/{context.job_id}/apply")

    assert context.response.status_code == 200


@when("the job seeker selects and uploads a resume file")
def upload_resume(client, context):

    context.response = client.post(
        f"/jobs/{context.job_id}/apply",
        data={"cover_letter": "I am interested in this position."},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )


@then("the resume should be uploaded successfully")
def verify_upload(context):

    assert context.response.status_code == 200

    data = context.response.json()

    assert data["success"] is True

    assert "application_id" in data

    context.application_id = data["application_id"]

    print("✅ SUCCESS: Resume uploaded successfully")


# ==================================================
# Scenario 2:
# Store uploaded resume information
# ==================================================


@given("the job seeker has uploaded a resume")
def uploaded_resume(client, context):

    response = client.post(
        f"/jobs/{context.job_id}/apply",
        data={"cover_letter": "Test cover letter"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    assert response.status_code == 200

    data = response.json()

    context.application_id = data["application_id"]


@when("the upload process is completed")
def process_upload(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the resume information should be saved in the database")
def verify_database(context):

    assert context.response.status_code == 200

    page = context.response.text.lower()

    assert "resume" in page

    print("✅ SUCCESS: Resume information saved in database")
