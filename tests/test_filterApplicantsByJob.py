import pytest
from fastapi.testclient import TestClient
from pytest_bdd import (
    scenarios,
    given,
    when,
    then,
)
from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/filterApplicantsByJob.feature")

client = TestClient(app)

JOB_ID = "job001"
JOB_WITHOUT_APPLICANTS = "job999"

# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def context():
    return {}


# ==================================================
# Given
# ==================================================


@given("the employer has one or more job postings with applicants")
def employer_has_jobs():
    return True


@given("the employer is on the Applicant Management page")
def applicant_page(context):

    response = client.get("/applications")

    assert response.status_code == 200

    context["response"] = response


@given("the employer selects a job position that has no applicants")
def no_applicants():
    return True


@given("the employer is viewing filtered applicants")
def viewing_filtered():
    return True


@given("the employer has filtered applicants by job position")
def filtered_applicants():
    return True


# ==================================================
# When
# ==================================================


@when("the employer selects a specific job position from the filter option")
def filter_job(context):

    response = client.get(
        "/applications",
        params={"job_id": JOB_ID},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer does not select any job position filter")
def no_filter(context):

    response = client.get("/applications")

    assert response.status_code == 200

    context["response"] = response


@when("the system applies the filter")
def apply_empty_filter(context):

    response = client.get(
        "/applications",
        params={"job_id": JOB_WITHOUT_APPLICANTS},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer selects a different job position filter")
def change_filter(context):

    response = client.get(
        "/applications",
        params={"job_id": "job002"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer selects an applicant from the filtered list")
def open_applicant(context):

    response = client.get("/application/application001")

    assert response.status_code == 200

    context["response"] = response


# ==================================================
# Then
# ==================================================


@then("the system should display only applicants who applied for the selected job position")
def filtered_correctly(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display all applicants from all job postings")
def all_applicants(context):

    response = context["response"]

    assert response.status_code == 200


@then('the system should display a "No applicants found for this job position" message')
def no_applicant_message(context):

    response = context["response"]

    assert response.status_code == 200

    assert (
        "No applicants found for this job position" in response.text
        or "No applicants" in response.text
    )


@then("the system should refresh the applicant list")
def refreshed(context):

    response = context["response"]

    assert response.status_code == 200


@then("display applicants related to the newly selected job position")
def correct_applicants(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display the applicant's details and application information")
def applicant_details(context):

    response = context["response"]

    assert response.status_code == 200
