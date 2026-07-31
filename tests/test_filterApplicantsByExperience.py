from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient
import pytest

from job_portal_web.backend.main import app

client = TestClient(app)

scenarios("features/filterApplicantsByExperience.feature")


@pytest.fixture
def context():
    return {}


# ==========================================================
# Shared Context
# ==========================================================


@given("the employer has received applications from candidates with different experience levels")
def applications_exist(context):
    context["response"] = client.get("/applications")


@given("the employer is viewing the Applicant Management page")
def applicant_management_page(context):
    context["response"] = client.get("/applications")


@given("the employer is on the Applicant Management page")
def applicant_page(context):
    context["response"] = client.get("/applications")


@given("the employer applies an experience level filter")
def experience_filter(context):
    context["response"] = client.get("/applications", params={"experience": "10 years"})


@given("the employer is viewing filtered applicants")
def filtered_applicants(context):
    context["response"] = client.get("/applications", params={"experience": "1-2"})


# ==========================================================
# When Steps
# ==========================================================


@when("the employer selects an experience level filter")
def select_experience(context):
    context["response"] = client.get("/applications", params={"experience": "3-5"})


@when("the employer selects a minimum years of experience requirement")
def minimum_experience(context):
    context["response"] = client.get("/applications", params={"experience": "5+"})


@when("the employer does not select any experience level filter")
def no_experience_filter(context):
    context["response"] = client.get("/applications")


@when("no applicants match the selected experience requirement")
def no_matching_experience(context):
    context["response"] = client.get("/applications", params={"experience": "10 years"})


@when("the employer changes the experience level filter")
def change_experience_filter(context):
    context["response"] = client.get("/applications", params={"experience": "entry"})


# ==========================================================
# Then Steps
# ==========================================================


@then("the system should display only applicants who match the selected experience level")
def experience_filtered(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display applicants who meet or exceed the selected experience level")
def minimum_experience_display(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display all applicants regardless of their experience level")
def display_all(context):

    response = context["response"]

    assert response.status_code == 200

    assert "<table" in response.text


@then('the system should display a "No applicants found for this experience level" message')
def no_experience_message(context):

    response = context["response"]

    assert response.status_code == 200

    assert (
        "No applicants found for this experience level" in response.text
        or "No applicants found for this job position." in response.text
    )


@then("the system should refresh the applicant list")
def refresh_list(context):

    response = context["response"]

    assert response.status_code == 200


@then("display applicants who match the updated experience criteria")
def updated_experience(context):

    response = context["response"]

    assert response.status_code == 200
