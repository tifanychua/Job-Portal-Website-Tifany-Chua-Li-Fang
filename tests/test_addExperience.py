from uuid import uuid4

import pytest
from pytest_bdd import scenarios

from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db
from pytest_bdd import given, when, then, parsers

client = TestClient(app)

scenarios("features/addExperience.feature")


class TestContext:

    def __init__(self):

        self.response = None

        self.experience_id = None

        self.form_data = {}

        self.message = ""


@pytest.fixture
def context():

    return TestContext()


def create_test_experience():

    doc_ref = db.collection("job_seeker_experience").document()

    doc_ref.set(
        {
            "applicant_id": "applicant001",
            "job_title": "Software Engineer",
            "company_name": "ABC Sdn Bhd",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
            "currently_working": False,
            "description": "Test Record",
        }
    )

    return doc_ref.id


def delete_test_experience(document_id):

    db.collection("job_seeker_experience").document(document_id).delete()


# ============================================================
# Acceptance Tests
# ============================================================


def test_successfully_add_experience():

    unique = str(uuid4())[:8]

    response = client.post(
        "/add-experience",
        data={
            "job_title": "Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
            "currently_working": False,
            "description": "Acceptance Test",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True

    assert body["redirect"] == "/manage-experience"

    docs = (
        db.collection("job_seeker_experience")
        .where("company_name", "==", f"ABC Company {unique}")
        .stream()
    )

    document = next(docs, None)

    assert document is not None

    document.reference.delete()


def test_missing_job_title():

    unique = str(uuid4())[:8]

    response = client.post(
        "/add-experience",
        data={
            "job_title": "",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
            "currently_working": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please enter your job title."


def test_missing_company_name():

    response = client.post(
        "/add-experience",
        data={
            "job_title": "Software Engineer",
            "company_name": "",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "2024-01",
            "currently_working": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please enter your company name."


def test_missing_start_date():

    unique = str(uuid4())[:8]

    response = client.post(
        "/add-experience",
        data={
            "job_title": "Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "",
            "end_date": "2024-01",
            "currently_working": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please select your start date."


def test_missing_end_date():

    unique = str(uuid4())[:8]

    response = client.post(
        "/add-experience",
        data={
            "job_title": "Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "",
            "currently_working": False,
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False

    assert body["message"] == "Please select your end date."


# ============================================================
# BDD
# ============================================================


@given("the job seeker is on the Manage Experience page")
def open_manage_experience(context):

    context.response = client.get("/manageExperience")

    assert context.response.status_code == 200


@given("the job seeker is not currently working")
def not_currently_working(context):

    context.form_data["currently_working"] = False


@given("an identical experience record already exists")
def duplicate_record(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
        "description": "Duplicate Test",
    }

    doc = db.collection("job_seeker_experience").document()

    doc.set({"applicant_id": "applicant001", **context.form_data})

    context.experience_id = doc.id


@when("the job seeker enters valid experience information")
def valid_information(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
        "description": "BDD Test",
    }


@when("the job seeker leaves the job title empty")
def missing_job_title(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
    }


@when("the job seeker leaves the company name empty")
def missing_company(context):

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": "",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
    }


@when("the job seeker leaves the start date empty")
def missing_start(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "",
        "end_date": "2024-01",
        "currently_working": False,
    }


@when("the job seeker leaves the end date empty")
def missing_end(context):

    unique = str(uuid4())[:8]

    context.form_data.update(
        {
            "job_title": "Software Engineer",
            "company_name": f"ABC Company {unique}",
            "employment_type": "Full-Time",
            "location": "Kuala Lumpur",
            "start_date": "2020-01",
            "end_date": "",
        }
    )


@when("the job seeker enters an end date earlier than the start date")
def invalid_period(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "Kuala Lumpur",
        "start_date": "2024-01",
        "end_date": "2020-01",
        "currently_working": False,
    }


@when("the job seeker enters the same experience information")
def duplicate_information(context):

    pass


@when("submits the experience form")
def submit_form(context):

    context.response = client.post("/add-experience", data=context.form_data)


@then("the experience record should be saved successfully")
def saved(context):

    assert context.response.status_code == 200

    body = context.response.json()

    assert body["success"] is True

    docs = (
        db.collection("job_seeker_experience")
        .where("company_name", "==", context.form_data["company_name"])
        .stream()
    )

    document = next(docs, None)

    assert document is not None

    document.reference.delete()


@then("the system should redirect to the Manage Experience page")
def redirect(context):

    body = context.response.json()

    assert body["redirect"] == "/manage-experience"


@then(parsers.parse('the system should display "{message}"'))
def display_error(context, message):

    assert context.response.status_code in (400, 409)

    body = context.response.json()

    assert body["success"] is False

    assert body["message"] == message


@then("the experience record should not be saved")
def not_saved(context):

    docs = (
        db.collection("job_seeker_experience")
        .where("company_name", "==", context.form_data.get("company_name", ""))
        .stream()
    )

    assert next(docs, None) is None


@then("the experience record should not be duplicated")
def no_duplicate(context):

    docs = list(
        db.collection("job_seeker_experience")
        .where("company_name", "==", context.form_data["company_name"])
        .stream()
    )

    assert len(docs) == 1

    docs[0].reference.delete()


@when("the job seeker leaves the employment type empty")
def missing_employment_type(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "",
        "location": "Kuala Lumpur",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
    }


@when("the job seeker leaves the location empty")
def missing_location(context):

    unique = str(uuid4())[:8]

    context.form_data = {
        "job_title": "Software Engineer",
        "company_name": f"ABC Company {unique}",
        "employment_type": "Full-Time",
        "location": "",
        "start_date": "2020-01",
        "end_date": "2024-01",
        "currently_working": False,
    }
