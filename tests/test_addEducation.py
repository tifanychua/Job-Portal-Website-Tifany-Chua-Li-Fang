from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# Load Feature File
# ==================================================

scenarios("features/addEducation.feature")


# ==================================================
# Constants
# ==================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class ScenarioContext:
    def __init__(self):
        self.response = None
        self.education_id = None
        self.form_data = {}
        self.message = ""


@pytest.fixture
def context():
    return ScenarioContext()


@pytest.fixture(autouse=True)
def cleanup(context):
    """
    Delete an education document created by a BDD scenario.
    """

    yield

    if context.education_id:
        document_reference = db.collection("education").document(context.education_id)

        if document_reference.get().exists:
            document_reference.delete()


# ==================================================
# Helper Functions
# ==================================================


def find_education_by_institution(institution):
    return list(db.collection("education").where("institution", "==", institution).stream())


# ==================================================
# Normal Test 1
# ==================================================


def test_successfully_add_education(client):
    unique = uuid4().hex[:8]
    institution = f"Taylor's University {unique}"

    response = client.post(
        "/add-education",
        data={
            "degree": "Bachelor Degree",
            "institution": institution,
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
            "grade": "3.80",
            "description": "Acceptance Test",
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["success"] is True
    assert body["redirect"] == "/manage-education"

    documents = find_education_by_institution(institution)

    assert len(documents) == 1

    for document in documents:
        document.reference.delete()


# ==================================================
# Normal Test 2
# ==================================================


def test_missing_qualification(client):
    response = client.post(
        "/add-education",
        data={
            "degree": "",
            "institution": "Taylor's University",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Please select your qualification."


# ==================================================
# Normal Test 3
# ==================================================


def test_missing_institution(client):
    response = client.post(
        "/add-education",
        data={
            "degree": "Bachelor Degree",
            "institution": "",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Please enter your institution."


# ==================================================
# Normal Test 4
# ==================================================


def test_missing_start_date(client):
    response = client.post(
        "/add-education",
        data={
            "degree": "Bachelor Degree",
            "institution": "Taylor's University",
            "field_of_study": "Software Engineering",
            "start_date": "",
            "end_date": "2024-02",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Please select your start date."


# ==================================================
# Normal Test 5
# ==================================================


def test_missing_end_date(client):
    response = client.post(
        "/add-education",
        data={
            "degree": "Bachelor Degree",
            "institution": "Taylor's University",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "",
            "current_study": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Please select your end date."


# ==================================================
# Given Steps
# ==================================================


@given("the job seeker is on the Manage Education page")
def open_manage_education(context, client):
    context.response = client.get("/manage-education")

    assert context.response.status_code == 200


@given("the job seeker is not currently studying")
def not_currently_studying(context):
    context.form_data["current_study"] = False


@given("an identical education record already exists")
def duplicate_record(context):
    unique = uuid4().hex[:8]

    context.form_data = {
        "degree": "Bachelor Degree",
        "institution": f"Taylor University {unique}",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
        "grade": "3.80",
        "description": "Duplicate Test",
    }

    document_reference = db.collection("education").document()

    document_reference.set(
        {
            "applicant_id": APPLICANT_ID,
            "qualification": context.form_data["degree"],
            "institution": context.form_data["institution"],
            "field_of_study": context.form_data["field_of_study"],
            "start_date": context.form_data["start_date"],
            "end_date": context.form_data["end_date"],
            "current_study": context.form_data["current_study"],
            "grade": context.form_data["grade"],
            "description": context.form_data["description"],
        }
    )

    context.education_id = document_reference.id


# ==================================================
# When Steps
# ==================================================


@when("the job seeker enters valid education information")
def valid_information(context):
    unique = uuid4().hex[:8]

    context.form_data = {
        "degree": "Bachelor Degree",
        "institution": f"Taylor University {unique}",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
        "grade": "3.80",
        "description": "BDD Test",
    }


@when("the job seeker leaves the qualification empty")
def bdd_missing_qualification(context):
    context.form_data = {
        "degree": "",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker leaves the institution empty")
def bdd_missing_institution(context):
    context.form_data = {
        "degree": "Bachelor Degree",
        "institution": "",
        "field_of_study": "Software Engineering",
        "start_date": "2020-01",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker leaves the start date empty")
def bdd_missing_start_date(context):
    context.form_data = {
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "",
        "end_date": "2024-02",
        "current_study": False,
    }


@when("the job seeker leaves the end date empty")
def bdd_missing_end_date(context):
    context.form_data.update(
        {
            "degree": "Bachelor Degree",
            "institution": "Taylor University",
            "field_of_study": "Software Engineering",
            "start_date": "2020-01",
            "end_date": "",
            "current_study": False,
        }
    )


@when("the job seeker enters an end date earlier than the start date")
def invalid_period(context):
    context.form_data = {
        "degree": "Bachelor Degree",
        "institution": "Taylor University",
        "field_of_study": "Software Engineering",
        "start_date": "2024-01",
        "end_date": "2020-01",
        "current_study": False,
    }


@when("the job seeker enters the same education information")
def duplicate_information(context):
    pass


@when("submits the education form")
def submit_form(context, client):
    context.response = client.post(
        "/add-education",
        data=context.form_data,
    )


# ==================================================
# Then Steps
# ==================================================


@then("the education record should be saved successfully")
def saved(context):
    assert context.response.status_code == 200

    body = context.response.json()

    assert body["success"] is True

    documents = find_education_by_institution(context.form_data["institution"])

    assert len(documents) == 1

    context.education_id = documents[0].id


@then("the system should redirect to the Manage Education page")
def redirect(context):
    body = context.response.json()

    assert body["redirect"] == "/manage-education"


@then(parsers.parse('the system should display "{message}"'))
def display_error(context, message):
    assert context.response.status_code in (400, 409)

    body = context.response.json()

    assert body["success"] is False
    assert body["message"] == message


@then("the education record should not be saved")
def not_saved(context):
    institution = context.form_data.get("institution", "")

    if not institution:
        return

    documents = find_education_by_institution(institution)

    assert len(documents) == 0


@then("the education record should not be duplicated")
def no_duplicate(context):
    documents = find_education_by_institution(context.form_data["institution"])

    assert len(documents) == 1

    context.education_id = documents[0].id
