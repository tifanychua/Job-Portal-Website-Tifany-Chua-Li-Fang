from uuid import uuid4

import pytest

from pytest_bdd import scenarios

from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db
from pytest_bdd import given, when, then, parsers

client = TestClient(app)

scenarios("features/editEducation.feature")


class TestContext:

    def __init__(self):

        self.response = None

        self.education_id = None

        self.form_data = {}

        self.message = ""


@pytest.fixture
def context():

    return TestContext()


def create_test_education():

    unique = str(uuid4())[:8]

    doc = db.collection("education").document()

    doc.set(
        {
            "applicant_id": "applicant001",
            "qualification": "Bachelor Degree",
            "institution": f"Taylor University {unique}",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
            "grade": "3.80",
            "description": "Edit Test",
        }
    )

    return doc.id


def test_successfully_update_education():

    education_id = create_test_education()

    response = client.post(
        "/update-education",
        data={
            "education_id": education_id,
            "degree": "Master Degree",
            "institution": "Taylor University",
            "field_of_study": "Software Engineering",
            "start_date": "2024-01",
            "end_date": "2025-12",
            "current_study": False,
            "grade": "4.00",
            "description": "Updated",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    doc = db.collection("education").document(education_id).get()

    assert doc.to_dict()["qualification"] == "Master Degree"

    db.collection("education").document(education_id).delete()


def test_missing_qualification():

    education_id = create_test_education()

    response = client.post(
        "/update-education",
        data={
            "education_id": education_id,
            "degree": "",
            "institution": "Taylor University",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please select your qualification."

    db.collection("education").document(education_id).delete()


def test_missing_institution():

    education_id = create_test_education()

    response = client.post(
        "/update-education",
        data={
            "education_id": education_id,
            "degree": "Bachelor Degree",
            "institution": "",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please enter your institution."

    db.collection("education").document(education_id).delete()


def test_missing_start_date():

    education_id = create_test_education()

    response = client.post(
        "/update-education",
        data={
            "education_id": education_id,
            "degree": "Bachelor Degree",
            "institution": "Taylor University",
            "field_of_study": "Software Engineering",
            "start_date": "",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please select your start date."

    db.collection("education").document(education_id).delete()


def test_missing_end_date():

    education_id = create_test_education()

    response = client.post(
        "/update-education",
        data={
            "education_id": education_id,
            "degree": "Bachelor Degree",
            "institution": "Taylor University",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    assert response.json()["message"] == "Please select your end date."

    db.collection("education").document(education_id).delete()


@given("the job seeker has an existing education record")
def existing_education(context):

    context.education_id = create_test_education()


@given("the job seeker is not currently studying")
def not_currently_studying(context):

    context.form_data["current_study"] = False


@given("another identical education record already exists")
def duplicate_record(context):

    context.education_id = create_test_education()

    unique = str(uuid4())[:8]

    doc = db.collection("education").document()

    doc.set(
        {
            "applicant_id": "applicant001",
            "qualification": "Master Degree",
            "institution": f"Taylor University {unique}",
            "field_of_study": "Software Engineering",
            "start_date": "2024-01",
            "end_date": "2025-12",
            "current_study": False,
            "grade": "4.00",
            "description": "Duplicate Record",
        }
    )

    context.duplicate_id = doc.id

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Master Degree",
        "institution": f"Taylor University {unique}",
        "field_of_study": "Software Engineering",
        "start_date": "2024-01",
        "end_date": "2025-12",
        "current_study": False,
        "grade": "4.00",
        "description": "Duplicate Record",
    }


@given("the education record does not exist")
def education_not_found(context):

    context.education_id = "INVALID_ID"

    context.form_data = {
        "education_id": "INVALID_ID",
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker enters valid updated education information")
def valid_update(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Master Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2024-01",
        "end_date": "2025-12",
        "current_study": False,
        "grade": "4.00",
        "description": "Updated",
    }


@when("the job seeker clears the qualification")
def clear_qualification(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker clears the institution")
def clear_institution(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Bachelor Degree",
        "institution": "",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker clears the start date")
def clear_start_date(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker clears the end date")
def clear_end_date(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "",
        "current_study": False,
    }


@when("the job seeker enters an end date earlier than the start date")
def invalid_period(context):

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2025-01",
        "end_date": "2024-01",
        "current_study": False,
    }


@when("the job seeker enters duplicate education information")
def duplicate_information(context):

    pass


@when("submits the edit education form")
@when("the job seeker submits the edit education form")
def submit_update(context):

    context.response = client.post("/update-education", data=context.form_data)


@then("the education record should be updated successfully")
def updated(context):

    assert context.response.status_code == 200

    body = context.response.json()

    assert body["success"] is True

    doc = db.collection("education").document(context.education_id).get()

    assert doc.to_dict()["qualification"] == "Master Degree"

    db.collection("education").document(context.education_id).delete()


@then("the system should redirect to the Manage Education page")
def redirect(context):

    body = context.response.json()

    assert body["redirect"] == "/manage-education"


@then(parsers.parse('the system should display "{message}"'))
def display_error(context, message):

    assert context.response.status_code in (400, 404, 409)

    body = context.response.json()

    assert body["success"] is False

    assert body["message"] == message


@then("the education record should remain unchanged")
def unchanged(context):

    doc = db.collection("education").document(context.education_id).get()

    assert doc.exists

    db.collection("education").document(context.education_id).delete()

    if hasattr(context, "duplicate_id"):

        db.collection("education").document(context.duplicate_id).delete()
