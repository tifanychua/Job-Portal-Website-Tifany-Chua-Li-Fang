from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from main import app

# Feature file location
scenarios("features/uploadResume.feature")


@pytest.fixture
def client():

    return TestClient(app)


class Context:

    def __init__(self):

        self.response = None

        # Existing job id in job_list collection
        self.job_id = "0ZWvjQqV3DMLANrbIRUs"

        # Store generated application id
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
