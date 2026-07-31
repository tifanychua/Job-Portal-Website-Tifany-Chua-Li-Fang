from uuid import uuid4

import pytest
from pytest_bdd import scenarios
from pytest_bdd import given, when, then, parsers
from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)

scenarios("features/editExperience.feature")


class TestContext:

    def __init__(self):

        self.response = None
        self.experience_id = None
        self.duplicate_id = None
        self.form_data = {}


@pytest.fixture
def context():
    return TestContext()


# ============================================================
# Helper
# ============================================================


def create_test_experience():

    unique = str(uuid4())[:8]

    doc = db.collection("job_seeker_experience").document()

    doc.set(
        {
            "applicant_id": "applicant001",
            "job_title": "Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
            "currently_working": False,
            "description": "Edit Test",
        }
    )

    return doc.id


# ============================================================
# Helper
# ============================================================


def valid_form():

    return {
        "job_title": "Software Engineer",
        "company_name": "ABC Company",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
        "description": "Test",
    }


# ============================================================
# Acceptance Tests
# ============================================================


def test_successfully_update_experience():

    experience_id = create_test_experience()

    response = client.post(
        f"/edit-experience/{experience_id}",
        data={
            "job_title": "Senior Software Engineer",
            "company_name": "ABC Company",
            "employment_type": "Full-Time",
            "location": "Penang",
            "start_date": "2021-01",
            "end_date": "2025-01",
            "currently_working": False,
            "description": "Updated",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    doc = db.collection("job_seeker_experience").document(experience_id).get()

    assert doc.to_dict()["job_title"] == "Senior Software Engineer"

    doc.reference.delete()


def test_missing_job_title():

    experience_id = create_test_experience()

    response = client.post(
        f"/edit-experience/{experience_id}",
        data={
            "job_title": "",
            "company_name": "ABC Company",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please enter your job title."

    db.collection("job_seeker_experience").document(experience_id).delete()


def test_missing_company_name():

    experience_id = create_test_experience()

    response = client.post(
        f"/edit-experience/{experience_id}",
        data={
            "job_title": "Software Engineer",
            "company_name": "",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please enter your company name."

    db.collection("job_seeker_experience").document(experience_id).delete()


def test_missing_start_date():

    experience_id = create_test_experience()

    response = client.post(
        f"/edit-experience/{experience_id}",
        data={
            "job_title": "Software Engineer",
            "company_name": "ABC Company",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "",
            "end_date": "2024-01",
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please select your start date."

    db.collection("job_seeker_experience").document(experience_id).delete()


def test_missing_end_date():

    experience_id = create_test_experience()

    response = client.post(
        f"/edit-experience/{experience_id}",
        data={
            "job_title": "Software Engineer",
            "company_name": "ABC Company",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "",
            "currently_working": False,
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please select your end date."

    db.collection("job_seeker_experience").document(experience_id).delete()


# ============================================================
# BDD
# ============================================================


@given("the job seeker has an existing experience record")
def existing_experience(context):

    context.experience_id = create_test_experience()


@given("the job seeker is not currently working")
def not_currently_working(context):

    context.form_data["currently_working"] = False


@given("another identical experience record already exists")
def duplicate_record(context):

    context.experience_id = create_test_experience()

    unique = str(uuid4())[:8]

    doc = db.collection("job_seeker_experience").document()

    doc.set(
        {
            "applicant_id": "applicant001",
            "job_title": "Senior Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Penang",
            "start_date": "2021-01",
            "end_date": "2025-01",
            "currently_working": False,
            "description": "Duplicate",
        }
    )

    context.duplicate_id = doc.id

    context.form_data = {
        "job_title": "Senior Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Penang",
        "start_date": "2021-01",
        "end_date": "2025-01",
        "currently_working": False,
        "description": "Duplicate",
    }


@given("the experience record does not exist")
def not_found(context):

    context.experience_id = "INVALID_ID"

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": "ABC Company",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
    }


@when("the job seeker enters valid updated experience information")
def valid_update(context):

    context.form_data = {
        "job_title": "Senior Software Engineer",
        "company_name": "ABC Company",
        "employment_type": "Full-Time",
        "location": "Penang",
        "start_date": "2021-01",
        "end_date": "2025-01",
        "currently_working": False,
        "description": "Updated",
    }


@when("the job seeker clears the job title")
def clear_job_title(context):

    context.form_data = valid_form()

    context.form_data["job_title"] = ""


@when("the job seeker clears the company name")
def clear_company(context):

    context.form_data = valid_form()

    context.form_data["company_name"] = ""


@when("the job seeker clears the employment type")
def clear_type(context):

    context.form_data = valid_form()

    context.form_data["employment_type"] = ""


@when("the job seeker clears the location")
def clear_location(context):

    context.form_data = valid_form()

    context.form_data["location"] = ""


@when("the job seeker clears the start date")
def clear_start(context):

    context.form_data = valid_form()

    context.form_data["start_date"] = ""


@when("the job seeker clears the end date")
def clear_end(context):

    context.form_data = valid_form()

    context.form_data["end_date"] = ""


@when("the job seeker enters an end date earlier than the start date")
def invalid_period(context):

    context.form_data = valid_form()

    context.form_data["start_date"] = "2025-01"

    context.form_data["end_date"] = "2024-01"


@when("the job seeker enters duplicate experience information")
def duplicate_information(context):

    pass


@when("submits the edit experience form")
@when("the job seeker submits the edit experience form")
def submit(context):

    context.response = client.post(
        f"/edit-experience/{context.experience_id}", data=context.form_data
    )


@then("the experience record should be updated successfully")
def updated(context):

    assert context.response.status_code == 200

    assert context.response.json()["success"] is True

    db.collection("job_seeker_experience").document(context.experience_id).delete()


@then("the system should redirect to the Manage Experience page")
def redirect(context):

    assert context.response.json()["redirect"] == "/manage-experience"


@then(parsers.parse('the system should display "{message}"'))
def display_error(context, message):

    assert context.response.status_code in (400, 404, 409)

    body = context.response.json()

    assert body["success"] is False

    assert body["message"] == message


@then("the experience record should remain unchanged")
def unchanged(context):

    doc = db.collection("job_seeker_experience").document(context.experience_id).get()

    assert doc.exists

    doc.reference.delete()

    if context.duplicate_id:

        db.collection("job_seeker_experience").document(context.duplicate_id).delete()
