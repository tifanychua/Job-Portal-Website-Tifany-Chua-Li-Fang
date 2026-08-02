from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# Load Feature File
# ==================================================

scenarios("features/editEducation.feature")


# ==================================================
# Test Constants
# ==================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# Context
# ==================================================


class TestContext:
    def __init__(self):
        self.response = None
        self.education_id = None
        self.duplicate_id = None
        self.form_data = {}
        self.message = ""


@pytest.fixture
def context():
    return TestContext()


# ==================================================
# Helper Functions
# ==================================================


def create_test_education():
    unique = uuid4().hex[:8]

    document_reference = db.collection("education").document()

    document_reference.set(
        {
            "applicant_id": APPLICANT_ID,
            "qualification": "Bachelor Degree",
            "institution": f"Taylor University {unique}",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
            "grade": "3.80",
            "description": f"Edit Test {unique}",
        }
    )

    return document_reference.id


def delete_test_education(document_id):
    if not document_id:
        return

    document_reference = db.collection("education").document(document_id)

    if document_reference.get().exists:
        document_reference.delete()


# ==================================================
# Automatic Cleanup
# ==================================================


@pytest.fixture(autouse=True)
def cleanup_education_records(context):
    yield

    delete_test_education(context.education_id)
    delete_test_education(context.duplicate_id)


# ==================================================
# Normal Tests
# ==================================================


def test_successfully_update_education(client):
    education_id = create_test_education()
    unique = uuid4().hex[:8]

    try:
        response = client.post(
            "/update-education",
            data={
                "education_id": education_id,
                "degree": "Master Degree",
                "institution": (f"Taylor University Updated {unique}"),
                "field_of_study": "Software Engineering",
                "start_date": "2024-01",
                "end_date": "2025-12",
                "current_study": False,
                "grade": "4.00",
                "description": f"Updated {unique}",
            },
        )

        assert response.status_code == 200, response.text

        body = response.json()

        assert body["success"] is True

        document = db.collection("education").document(education_id).get()

        assert document.exists

        data = document.to_dict()

        assert data is not None
        assert data["qualification"] == "Master Degree"
        assert data["institution"] == (f"Taylor University Updated {unique}")
    finally:
        delete_test_education(education_id)


def test_missing_qualification(client):
    education_id = create_test_education()

    try:
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
    finally:
        delete_test_education(education_id)


def test_missing_institution(client):
    education_id = create_test_education()

    try:
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
    finally:
        delete_test_education(education_id)


def test_missing_start_date(client):
    education_id = create_test_education()

    try:
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
    finally:
        delete_test_education(education_id)


def test_missing_end_date(client):
    education_id = create_test_education()

    try:
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
    finally:
        delete_test_education(education_id)


# ==================================================
# Given Steps
# ==================================================


@given("the job seeker has an existing education record")
def existing_education(context):
    context.education_id = create_test_education()


@given("the job seeker is not currently studying")
def not_currently_studying(context):
    context.form_data["current_study"] = False


@given("another identical education record already exists")
def duplicate_record(context):
    context.education_id = create_test_education()

    unique = uuid4().hex[:8]
    duplicate_institution = f"Taylor University Duplicate {unique}"

    document_reference = db.collection("education").document()

    document_reference.set(
        {
            "applicant_id": APPLICANT_ID,
            "qualification": "Master Degree",
            "institution": duplicate_institution,
            "field_of_study": "Software Engineering",
            "start_date": "2024-01",
            "end_date": "2025-12",
            "current_study": False,
            "grade": "4.00",
            "description": "Duplicate Record",
        }
    )

    context.duplicate_id = document_reference.id

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Master Degree",
        "institution": duplicate_institution,
        "field_of_study": "Software Engineering",
        "start_date": "2024-01",
        "end_date": "2025-12",
        "current_study": False,
        "grade": "4.00",
        "description": "Duplicate Record",
    }


@given("the education record does not exist")
def education_not_found(context):
    context.education_id = f"INVALID_EDUCATION_{uuid4().hex}"

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


# ==================================================
# When Steps
# ==================================================


@when("the job seeker enters valid updated education information")
def valid_update(context):
    unique = uuid4().hex[:8]

    context.form_data = {
        "education_id": context.education_id,
        "degree": "Master Degree",
        "institution": (f"Taylor University Updated {unique}"),
        "field_of_study": "Software Engineering",
        "start_date": "2024-01",
        "end_date": "2025-12",
        "current_study": False,
        "grade": "4.00",
        "description": f"Updated {unique}",
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
def duplicate_information():
    pass


@when("submits the edit education form")
@when("the job seeker submits the edit education form")
def submit_update(context, client):
    context.response = client.post(
        "/update-education",
        data=context.form_data,
    )


# ==================================================
# Then Steps
# ==================================================


@then("the education record should be updated successfully")
def updated(context):
    assert context.response.status_code == 200, context.response.text

    body = context.response.json()

    assert body["success"] is True

    document = db.collection("education").document(context.education_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["qualification"] == "Master Degree"
    assert data["institution"] == (context.form_data["institution"])


@then("the system should redirect to the Manage Education page")
def redirect(context):
    body = context.response.json()

    assert body["redirect"] == "/manage-education"


@then(parsers.parse('the system should display "{message}"'))
def display_error(context, message):
    assert context.response.status_code in (
        400,
        404,
        409,
    ), context.response.text

    body = context.response.json()

    assert body["success"] is False
    assert body["message"] == message


@then("the education record should remain unchanged")
def unchanged(context):
    document = db.collection("education").document(context.education_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None
    assert data["qualification"] == "Bachelor Degree"
