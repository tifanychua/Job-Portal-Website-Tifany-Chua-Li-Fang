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
# Publish Job Data
# ==================================================


def publish_form_data():

    return {
        "job_title": "QA Automation Engineer",
        "category": "Information Technology",
        "employment_type": "Full-time",
        "position": "Senior Engineer",
        "vacancies": 2,
        "location": "Kuala Lumpur",
        "job_desc": "Responsible for automation testing.",
        "job_responsibility": "Develop and maintain automated test scripts.",
        "job_req": "Python, Selenium, FastAPI",
        "additional_info": "Hybrid Working",
        "salaryType": "fixed",
        "salary": "6500",
        "minSalary": "",
        "maxSalary": "",
        "benefits": ["EPF", "SOCSO"],
        "other_benefit": "",
        "action": "review",
    }


# ==================================================
# Acceptance Test 1
# Employer publishes a job posting
# ==================================================


def test_publish_job_success(client):

    response = client.post("/review-job", data=publish_form_data())

    assert response.status_code == 200

    response = client.post("/publish-job-confirm", follow_redirects=False)

    assert response.status_code == 303

    print("✅ Acceptance Test Passed: Employer published the job posting successfully.")


# ==================================================
# Acceptance Test 2
# Save published job
# ==================================================


def test_save_published_job(client):

    client.post("/review-job", data=publish_form_data())

    response = client.post("/publish-job-confirm", follow_redirects=False)

    assert response.status_code == 303

    jobs = db.collection("job_list").where("job_title", "==", "QA Automation Engineer").stream()

    found = False

    for doc in jobs:

        job = doc.to_dict()

        if job["status"] == "Active":

            found = True

            break

    assert found

    print("✅ Acceptance Test Passed: Published job information saved successfully.")


# ==================================================
# Acceptance Test 3
# Job seeker views published job
# ==================================================


def test_job_seeker_view_published_job(client):

    client.post("/review-job", data=publish_form_data())

    client.post("/publish-job-confirm", follow_redirects=False)

    jobs = db.collection("job_list").where("job_title", "==", "QA Automation Engineer").stream()

    assert any(True for _ in jobs)

    print("✅ Acceptance Test Passed: Published job posting displayed successfully.")


# ==================================================
# Negative Test
# ==================================================


def test_publish_without_session(client):

    response = client.post("/publish-job-confirm", follow_redirects=False)

    assert response.status_code == 303

    print("✅ Negative Test Passed: Publishing without job information handled correctly.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/jobPublish.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Employer publishes a job posting
# ==================================================


@given("the employer has created a job posting")
def created_job(context):

    context.response = None


@when("the employer submits the job posting for publication")
def publish_job(client, context):

    client.post("/review-job", data=publish_form_data())

    context.response = client.post("/publish-job-confirm", follow_redirects=False)


@then("the job posting should be published successfully")
def verify_publish(context):

    assert context.response.status_code == 303

    print("✅ Scenario Passed: Employer published the job posting successfully.")


# ==================================================
# Scenario 2
# Save published job posting
# ==================================================


@given("the employer has published a job posting")
def published_job(client, context):

    client.post("/review-job", data=publish_form_data())

    client.post("/publish-job-confirm", follow_redirects=False)


@when("the publication process is completed")
def publication_completed(context):

    pass


@then("the job posting information should be saved in the database")
def verify_saved():

    jobs = db.collection("job_list").where("job_title", "==", "QA Automation Engineer").stream()

    found = False

    for doc in jobs:

        job = doc.to_dict()

        if job["status"] == "Active" and job["location"] == "Kuala Lumpur":
            found = True
            break

    assert found

    print("✅ Scenario Passed: Published job information saved successfully.")


# ==================================================
# Scenario 3
# Job seeker views published job
# ==================================================


@given("the employer has published a job posting")
def published_job_again(client, context):

    client.post("/review-job", data=publish_form_data())

    client.post("/publish-job-confirm", follow_redirects=False)


@when("a job seeker browses available jobs")
def browse_jobs(client, context):

    context.response = client.get("/manage-jobs")


@then("the published job posting should be displayed")
def verify_display(context):

    jobs = db.collection("job_list").where("job_title", "==", "QA Automation Engineer").stream()

    found = False

    for doc in jobs:

        job = doc.to_dict()

        if job["status"] == "Active":
            found = True
            break

    assert found

    assert context.response.status_code == 200

    print("✅ Scenario Passed: Published job posting displayed successfully.")
