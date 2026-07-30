from uuid import uuid4

import pytest
from pytest_bdd import scenarios

from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db
from pytest_bdd import given, when, then, parsers

client = TestClient(app)

scenarios("features/addEducation.feature")

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

    doc_ref = db.collection("education").document()

    doc_ref.set({

        "applicant_id": "applicant001",
        "qualification": "Bachelor Degree",
        "institution": "Universiti Malaya",
        "field_of_study": "Computer Science",
        "start_date": "2020-01",
        "end_date": "2023-12",
        "current_study": False,
        "grade": "3.80",
        "description": "Test Record"

    })

    return doc_ref.id

def delete_test_education(document_id):

    db.collection("education").document(document_id).delete()

def test_successfully_add_education():

    response = client.post(

        "/add-education",

        data={

            "degree": "Bachelor Degree",

            "institution": "Taylor's University",

            "field_of_study": "Software Engineering",

            "start_date": "2020-01",

            "end_date": "2024-02",

            "current_study": False,

            "grade": "3.80",

            "description": "Acceptance Test"

        }

    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["redirect"] == "/manage-education"

    docs = (

        db.collection("education")

        .where("institution", "==", "Taylor's University")

        .stream()

    )

    document = next(docs, None)

    assert document is not None

    document.reference.delete()

def test_missing_qualification():

    response = client.post(

        "/add-education",

        data={

            "degree": "",

            "institution": "Taylor's University",

            "field_of_study": "Software Engineering",

            "start_date": "2020-01",

            "end_date": "2024-02",

            "current_study": False

        }

    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please select your qualification."

def test_missing_institution():

    response = client.post(

        "/add-education",

        data={

            "degree": "Bachelor Degree",

            "institution": "",

            "field_of_study": "Software Engineering",

            "start_date": "2020-01",

            "end_date": "2024-02",

            "current_study": False

        }

    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please enter your institution."

def test_missing_start_date():

    response = client.post(

        "/add-education",

        data={

            "degree": "Bachelor Degree",

            "institution": "Taylor's University",

            "field_of_study": "Software Engineering",

            "start_date": "",

            "end_date": "2024-02",

            "current_study": False

        }

    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please select your start date."

def test_missing_end_date():

    response = client.post(

        "/add-education",

        data={

            "degree": "Bachelor Degree",

            "institution": "Taylor's University",

            "field_of_study": "Software Engineering",

            "start_date": "2020-01",

            "end_date": "",

            "current_study": False

        }

    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please select your end date."

@given("the job seeker is on the Manage Education page")
def open_manage_education(context):

    context.response = client.get("/manage-education")

    assert context.response.status_code == 200

@given("the job seeker is not currently studying")
def not_currently_studying(context):

    context.form_data["current_study"] = False

@given("an identical education record already exists")
def duplicate_record(context):

    unique = str(uuid4())[:8]

    context.form_data = {

        "degree": "Bachelor Degree",

        "institution": f"Taylor University {unique}",

        "field_of_study": "Software Engineering",

        "start_date": "2020-01",

        "end_date": "2024-02",

        "current_study": False,

        "grade": "3.80",

        "description": "Duplicate Test"

    }

    doc = db.collection("education").document()

    doc.set({

        "applicant_id": "applicant001",

        "qualification": context.form_data["degree"],

        "institution": context.form_data["institution"],

        "field_of_study": context.form_data["field_of_study"],

        "start_date": context.form_data["start_date"],

        "end_date": context.form_data["end_date"],

        "current_study": False,

        "grade": context.form_data["grade"],

        "description": context.form_data["description"]

    })

    context.education_id = doc.id

@when("the job seeker enters valid education information")
def valid_information(context):

    unique = str(uuid4())[:8]

    context.form_data = {

        "degree": "Bachelor Degree",

        "institution": f"Taylor University {unique}",

        "field_of_study": "Software Engineering",

        "start_date": "2020-01",

        "end_date": "2024-02",

        "current_study": False,

        "grade": "3.80",

        "description": "BDD Test"

    }

@when("the job seeker leaves the qualification empty")
def missing_qualification(context):

    context.form_data = {

        "degree": "",

        "institution": "Taylor University",

        "field_of_study": "Software Engineering",

        "start_date": "2020-01",

        "end_date": "2024-02",

        "current_study": False

    }

@when("the job seeker leaves the institution empty")
def missing_institution(context):

    context.form_data = {

        "degree": "Bachelor Degree",

        "institution": "",

        "field_of_study": "Software Engineering",

        "start_date": "2020-01",

        "end_date": "2024-02",

        "current_study": False

    }

@when("the job seeker leaves the start date empty")
def missing_start_date(context):

    context.form_data = {

        "degree": "Bachelor Degree",

        "institution": "Taylor University",

        "field_of_study": "Software Engineering",

        "start_date": "",

        "end_date": "2024-02",

        "current_study": False

    }

@when("the job seeker leaves the end date empty")
def missing_end_date(context):

    context.form_data.update({

        "degree": "Bachelor Degree",

        "institution": "Taylor University",

        "field_of_study": "Software Engineering",

        "start_date": "2020-01",

        "end_date": ""

    })

@when("the job seeker enters an end date earlier than the start date")
def invalid_period(context):

    context.form_data = {

        "degree": "Bachelor Degree",

        "institution": "Taylor University",

        "field_of_study": "Software Engineering",

        "start_date": "2024-01",

        "end_date": "2020-01",

        "current_study": False

    }

@when("the job seeker enters the same education information")
def duplicate_information(context):

    pass

@when("submits the education form")
def submit_form(context):

    context.response = client.post(

        "/add-education",

        data=context.form_data

    )

@then("the education record should be saved successfully")
def saved(context):

    assert context.response.status_code == 200

    body = context.response.json()

    assert body["success"] is True

    docs = (

        db.collection("education")

        .where("institution", "==", context.form_data["institution"])

        .stream()

    )

    document = next(docs, None)

    assert document is not None

    document.reference.delete()

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

    docs = (

        db.collection("education")

        .where("institution", "==", context.form_data.get("institution", ""))

        .stream()

    )

    assert next(docs, None) is None

@then("the education record should not be duplicated")
def no_duplicate(context):

    docs = list(

        db.collection("education")

        .where("institution", "==", context.form_data["institution"])

        .stream()

    )

    assert len(docs) == 1

    docs[0].reference.delete()