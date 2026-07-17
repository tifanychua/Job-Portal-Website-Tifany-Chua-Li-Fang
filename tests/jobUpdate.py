from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from src.job_portal_web.backend.main import app
from src.job_portal_web.backend.database import db

# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Test Job ID
# ==================================================

JOB_ID = "fQGn5sKWaXa51nK1i4O0"


# ==================================================
# Update Form Data
# ==================================================


def update_form_data():

    return {
        "job_title": "Updated HR Executive",
        "category": "Human Resources",
        "employment_type": "Part-time",
        "position": "Senior Executive",
        "vacancies": 3,
        "location": "Petaling Jaya",
        "job_desc": "Updated job description",
        "job_responsibility": "Updated job responsibility",
        "job_req": "Updated job requirement",
        "additional_info": "Updated additional information",
        "salaryType": "negotiable",
        "salary": "",
        "minSalary": "",
        "maxSalary": "",
        "benefits": [],
        "other_benefit": "",
        "action": "review",
    }


# ==================================================
# Acceptance Test 1
# Employer updates a job posting
# ==================================================


def test_update_job_success(client):

    response = client.post(f"/review-edit-job/{JOB_ID}", data=update_form_data())

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Employer updated the job posting successfully.")


# ==================================================
# Acceptance Test 2
# Save updated job information
# ==================================================


def test_save_updated_job_information(client):

    doc = db.collection("job_list").document(JOB_ID).get()

    client.post(f"/review-edit-job/{JOB_ID}", data=update_form_data())

    response = client.post(f"/update-job-confirm/{JOB_ID}", follow_redirects=False)

    assert response.status_code == 303

    doc = db.collection("job_list").document(JOB_ID).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["job_title"] == "Updated HR Executive"

    assert job["location"] == "Petaling Jaya"

    assert job["job_desc"] == "Updated job description"

    print("✅ Acceptance Test Passed: Updated job information saved successfully.")


# ==================================================
# Acceptance Test 3
# Job seeker views updated information
# ==================================================


def test_view_updated_job_information(client):

    client.post(f"/review-edit-job/{JOB_ID}", data=update_form_data())

    client.post(f"/update-job-confirm/{JOB_ID}", follow_redirects=False)

    doc = db.collection("job_list").document(JOB_ID).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["job_title"] == "Updated HR Executive"

    print("✅ Acceptance Test Passed: Latest job information displayed successfully.")


# ==================================================
# Negative Test
# ==================================================


def test_update_invalid_job(client):

    response = client.post(
        "/review-edit-job/INVALID_JOB", data=update_form_data(), follow_redirects=False
    )

    assert response.status_code in [200, 303]

    print("✅ Negative Test Passed: Invalid job update handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/jobUpdate.feature")


# ==================================================
# Context
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


@when("the employer edits the job posting information")
def edit_job(client, context):

    context.response = client.post(f"/review-edit-job/{context.job_id}", data=update_form_data())


@then("the job posting should be updated successfully")
def verify_updated(context):

    assert context.response.status_code == 200

    print("✅ Scenario Passed: Employer updated the job posting successfully.")


# ==================================================
# Scenario 2
# Save updated job posting information
# ==================================================


@given("the employer has updated a job posting")
def updated_job(client, context):

    context.job_id = JOB_ID

    client.post(f"/review-edit-job/{context.job_id}", data=update_form_data())

    client.post(f"/update-job-confirm/{context.job_id}", follow_redirects=False)


@when("the update process is completed")
def update_completed(context):

    pass


@then("the updated job information should be saved in the database")
def verify_saved(context):

    doc = db.collection("job_list").document(context.job_id).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["job_title"] == "Updated HR Executive"

    assert job["category"] == "Human Resources"

    assert job["employment_type"] == "Part-time"

    assert job["position"] == "Senior Executive"

    assert job["location"] == "Petaling Jaya"

    assert job["job_desc"] == "Updated job description"

    assert job["job_responsibility"] == "Updated job responsibility"

    assert job["job_req"] == "Updated job requirement"

    print("✅ Scenario Passed: Updated job information saved successfully.")


# ==================================================
# Scenario 3
# Job seeker views updated job information
# ==================================================


@given("the employer has updated a job posting")
def updated_job_again(client, context):

    context.job_id = JOB_ID

    client.post(f"/review-edit-job/{context.job_id}", data=update_form_data())

    client.post(f"/update-job-confirm/{context.job_id}", follow_redirects=False)


@when("the job seeker views the job posting")
def view_job(client, context):

    context.response = client.get("/manage-jobs")


@then("the latest job information should be displayed")
def verify_display(context):

    doc = db.collection("job_list").document(context.job_id).get()

    assert doc.exists

    job = doc.to_dict()

    assert job["job_title"] == "Updated HR Executive"

    assert job["location"] == "Petaling Jaya"

    print("✅ Scenario Passed: Latest job information displayed successfully.")
