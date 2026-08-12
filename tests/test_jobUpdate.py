from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# Test Configuration
# ==================================================

SOURCE_JOB_ID = "WZrfzhFDQq7B0vgL63WY"
JOB_ID = f"TEST_JOB_UPDATE_{uuid4().hex}"
INVALID_JOB_ID = f"INVALID_JOB_{uuid4().hex}"


# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# Firestore Test Data
# ==================================================


@pytest.fixture(scope="module", autouse=True)
def setup_test_job():
    source_reference = db.collection("job_list").document(SOURCE_JOB_ID)

    source_document = source_reference.get()

    assert source_document.exists, f"Source job {SOURCE_JOB_ID} does not exist"

    # Copy an existing valid job so all required fields are available.
    test_job_data = source_document.to_dict()

    test_job_data["id"] = JOB_ID
    test_job_data["job_id"] = JOB_ID
    test_job_data["jobId"] = JOB_ID

    test_reference = db.collection("job_list").document(JOB_ID)

    test_reference.set(test_job_data)

    yield

    # Delete only test records.
    test_reference.delete()

    (db.collection("job_list").document(INVALID_JOB_ID).delete())


# ==================================================
# Update Form Data
# ==================================================


def update_form_data():
    return {
        "job_title": "Updated HR Executive",
        "category": "Human Resources",
        "employment_type": "Part-time",
        "position": "Senior Executive",
        "vacancies": "3",
        "location": "Petaling Jaya",
        "job_desc": "Updated job description",
        "job_responsibility": "Updated job responsibility",
        "job_req": "Updated job requirement",
        "additional_info": "Updated additional information",
        "salaryType": "negotiable",
        "salary": "",
        "minSalary": "",
        "maxSalary": "",
        "benefits": "",
        "other_benefit": "",
        "action": "review",
    }


# ==================================================
# Helper: Submit Update
# ==================================================


def submit_job_update(
    client: TestClient,
    job_id: str,
):
    response = client.post(
        f"/review-edit-job/{job_id}",
        data=update_form_data(),
        follow_redirects=False,
    )

    assert response.status_code == 303, (
        f"Expected 303 but received "
        f"{response.status_code}. "
        f"Redirect: {response.headers.get('location')}. "
        f"Body: {response.text}"
    )

    return response


# ==================================================
# Helper: Verify Saved Information
# ==================================================


def get_updated_job(job_id: str):
    document = db.collection("job_list").document(job_id).get()

    assert document.exists, f"Job {job_id} does not exist"

    return document.to_dict()


# ==================================================
# Acceptance Test 1
# Employer updates a job posting
# ==================================================


def test_update_job_success(client: TestClient):
    document = db.collection("job_list").document(JOB_ID).get()

    assert document.exists

    response = submit_job_update(client, JOB_ID)

    assert response.status_code == 303
    assert response.headers.get("location") is not None

    print("Acceptance Test Passed: " "Employer submitted the updated job successfully.")


# ==================================================
# Acceptance Test 2
# Save updated job information
# ==================================================


def test_save_updated_job_information(
    client: TestClient,
):
    submit_job_update(client, JOB_ID)

    job = get_updated_job(JOB_ID)

    assert job["job_title"] == "Updated HR Executive"
    assert job["location"] == "Petaling Jaya"
    assert job["job_desc"] == "Updated job description"

    print("Acceptance Test Passed: " "Updated job information was saved.")


# ==================================================
# Acceptance Test 3
# Job seeker views updated information
# ==================================================


def test_view_updated_job_information(
    client: TestClient,
):
    submit_job_update(client, JOB_ID)

    job = get_updated_job(JOB_ID)

    assert job["job_title"] == "Updated HR Executive"
    assert job["location"] == "Petaling Jaya"

    print("Acceptance Test Passed: " "Latest job information is available.")


# ==================================================
# Negative Test
# Invalid Job ID
# ==================================================


def test_update_invalid_job(
    client: TestClient,
):
    response = client.post(
        f"/review-edit-job/{INVALID_JOB_ID}",
        data=update_form_data(),
        follow_redirects=False,
    )

    assert response.status_code in (303, 404), response.text

    invalid_document = db.collection("job_list").document(INVALID_JOB_ID).get()

    assert not invalid_document.exists

    print("Negative Test Passed: " "Invalid job was not created or updated.")


# ==================================================
# Load BDD Feature
# ==================================================

scenarios("features/jobUpdate.feature")


# ==================================================
# BDD Context
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.job_id = JOB_ID


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario 1
# Employer updates a job posting
# ==================================================


@given("the employer has an existing job posting")
def existing_job(context):
    context.job_id = JOB_ID

    document = db.collection("job_list").document(context.job_id).get()

    assert document.exists


@when("the employer edits the job posting information")
def edit_job(client, context):
    context.response = submit_job_update(
        client,
        context.job_id,
    )


@then("the job posting should be updated successfully")
def verify_updated(context):
    assert context.response is not None
    assert context.response.status_code == 303

    print("Scenario Passed: " "Employer updated the job posting.")


# ==================================================
# Shared Step for Scenarios 2 and 3
# ==================================================


@given("the employer has updated a job posting")
def updated_job(client, context):
    context.job_id = JOB_ID

    context.response = submit_job_update(
        client,
        context.job_id,
    )


# ==================================================
# Scenario 2
# Save Updated Job Information
# ==================================================


@when("the update process is completed")
def update_completed(context):
    assert context.response is not None
    assert context.response.status_code == 303


@then("the updated job information " "should be saved in the database")
def verify_saved(context):
    job = get_updated_job(context.job_id)

    assert job["job_title"] == "Updated HR Executive"
    assert job["category"] == "Human Resources"
    assert job["employment_type"] == "Part-time"
    assert job["position"] == "Senior Executive"
    assert job["location"] == "Petaling Jaya"

    assert job["job_desc"] == "Updated job description"

    assert job["job_responsibility"] == "Updated job responsibility"

    assert job["job_req"] == "Updated job requirement"

    print("Scenario Passed: " "Updated job information was saved.")


# ==================================================
# Scenario 3
# View Updated Job Information
# ==================================================


@when("the job seeker views the job posting")
def view_job(client, context):
    context.response = client.get(
        "/manage-jobs",
        follow_redirects=False,
    )


@then("the latest job information should be displayed")
def verify_display(context):
    job = get_updated_job(context.job_id)

    assert job["job_title"] == "Updated HR Executive"
    assert job["location"] == "Petaling Jaya"

    print("Scenario Passed: " "Latest job information is available.")
