from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from job_portal_web.backend.main import app
from job_portal_web.backend import job_apply


# --------------------------------------------------
# Fake Login
# --------------------------------------------------

@pytest.fixture(autouse=True)
def fake_login(monkeypatch):

    def fake_current_user(request):
        return (
            "J000001",
            {
                "uid": "J000001",
                "full_name": "Test User",
                "headline": "Software Engineer",
                "photo": "user.png",
            },
        )

    monkeypatch.setattr(
        job_apply,
        "_get_current_job_seeker",
        fake_current_user,
    )


# --------------------------------------------------
# Test Client
# --------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------
# Acceptance Test 1
# --------------------------------------------------

def test_upload_resume_success(client: TestClient):
    """
    Acceptance test:
    Job seeker uploads a resume successfully
    """

    job_id = "2TDtsBmRQSrtBIMOtbGK"

    response = client.post(
        f"/jobs/{job_id}/apply",
        data={
            "cover_letter": "I am interested in this position."
        },
        files={
            "resume": (
                "resume.pdf",
                b"test resume content",
                "application/pdf",
            )
        },
    )

    if response.status_code == 200:
        print("✅ SUCCESS: Job seeker uploads a resume successfully")
    else:
        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "application_id" in data


# --------------------------------------------------
# Acceptance Test 2
# --------------------------------------------------

def test_resume_information_saved(client: TestClient):
    """
    Acceptance test:
    Uploaded resume information is saved
    """

    job_id = "2TDtsBmRQSrtBIMOtbGK"

    upload_response = client.post(
        f"/jobs/{job_id}/apply",
        data={
            "cover_letter": "Test cover letter"
        },
        files={
            "resume": (
                "resume.pdf",
                b"test resume content",
                "application/pdf",
            )
        },
    )

    assert upload_response.status_code == 200

    application_id = upload_response.json()["application_id"]

    response = client.get(f"/application/{application_id}")

    if response.status_code == 200:
        print("✅ SUCCESS: Uploaded resume information is saved")
    else:
        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code == 200


# --------------------------------------------------
# Load Feature
# --------------------------------------------------

scenarios("features/uploadResume.feature")


# --------------------------------------------------
# Context
# --------------------------------------------------

class Context:

    def __init__(self):

        self.response = None
        self.job_id = "2TDtsBmRQSrtBIMOtbGK"
        self.application_id = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1
# --------------------------------------------------

@given("the job seeker is on the resume upload page")
def resume_upload_page(client, context):

    context.response = client.get(
        f"/jobs/{context.job_id}/apply"
    )

    assert context.response.status_code == 200


@when("the job seeker selects and uploads a resume file")
def upload_resume(client, context):

    context.response = client.post(
        f"/jobs/{context.job_id}/apply",
        data={
            "cover_letter": "I am interested in this position."
        },
        files={
            "resume": (
                "resume.pdf",
                b"test resume content",
                "application/pdf",
            )
        },
    )


@then("the resume should be uploaded successfully")
def verify_upload(context):

    assert context.response.status_code == 200

    data = context.response.json()

    assert data["success"] is True

    assert "application_id" in data

    context.application_id = data["application_id"]

    print("✅ SUCCESS: Resume uploaded successfully")


# --------------------------------------------------
# Scenario 2
# --------------------------------------------------

@given("the job seeker has uploaded a resume")
def uploaded_resume(client, context):

    response = client.post(
        f"/jobs/{context.job_id}/apply",
        data={
            "cover_letter": "Test cover letter"
        },
        files={
            "resume": (
                "resume.pdf",
                b"test resume content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    context.application_id = response.json()["application_id"]


@when("the upload process is completed")
def process_upload(client, context):

    context.response = client.get(
        f"/application/{context.application_id}"
    )


@then("the resume information should be saved in the database")
def verify_database(context):

    assert context.response.status_code == 200

    print("✅ SUCCESS: Resume information saved in database")