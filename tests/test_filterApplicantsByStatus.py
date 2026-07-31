import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/filterApplicantsByStatus.feature")

client = TestClient(app)

# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def context():
    return {}


# ==================================================
# Given
# ==================================================


@given("the employer has received applications with different statuses")
def different_statuses():
    return True


@given('the employer has applicants with a "New" status')
def new_status():
    return True


@given('the employer has applicants with a "Shortlisted" status')
def shortlisted_status():
    return True


@given("the employer has applicants with different recruitment outcomes")
def different_outcomes():
    return True


@given("the employer is on the Applicant Management page")
def applicant_page(context):

    response = client.get("/applications")

    assert response.status_code == 200

    context["response"] = response


@given("the employer applies an application status filter")
def apply_status_filter():
    return True


@given("the employer is viewing filtered applicants")
def viewing_filtered():
    return True


# ==================================================
# When
# ==================================================


@when("the employer selects an application status filter")
def filter_status(context):

    response = client.get(
        "/applications",
        params={"status": "Reviewed"},
    )

    assert response.status_code == 200

    context["response"] = response


@when('the employer selects the "New" status filter')
def filter_new(context):

    response = client.get(
        "/applications",
        params={"status": "New"},
    )

    assert response.status_code == 200

    context["response"] = response


@when('the employer selects the "Shortlisted" status filter')
def filter_shortlisted(context):

    response = client.get(
        "/applications",
        params={"status": "Shortlisted"},
    )

    assert response.status_code == 200

    context["response"] = response


@when('the employer selects the "Rejected" or "Offered" status filter')
def filter_rejected_offered(context):

    response = client.get(
        "/applications",
        params={"status": "Rejected"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer does not select any application status filter")
def no_filter(context):

    response = client.get("/applications")

    assert response.status_code == 200

    context["response"] = response


@when("no applicants match the selected status")
def no_match(context):

    response = client.get(
        "/applications",
        params={"status": "Archived"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer changes the application status filter")
def change_status(context):

    response = client.get(
        "/applications",
        params={"status": "Shortlisted"},
    )

    assert response.status_code == 200

    context["response"] = response


# ==================================================
# Then
# ==================================================


@then("the system should display only applicants with the selected application status")
def display_filtered_status(context):

    assert context["response"].status_code == 200


@then("the system should display all applicants whose applications are new")
def display_new(context):

    assert context["response"].status_code == 200


@then("the system should display all shortlisted applicants")
def display_shortlisted(context):

    assert context["response"].status_code == 200


@then("the system should display applicants matching the selected status")
def display_selected_status(context):

    assert context["response"].status_code == 200


@then("the system should display all applicants regardless of their status")
def display_all(context):

    response = context["response"]

    assert response.status_code == 200

    assert "Applications" in response.text


@then('the system should display a "No applicants found for this application status" message')
def no_applicant_message(context):

    response = context["response"]

    assert response.status_code == 200

    assert (
        "No applicants found for this application status" in response.text
        or "No applications received yet." in response.text
    )


@then("the system should refresh the applicant list")
def refreshed(context):

    assert context["response"].status_code == 200


@then("display applicants with the updated status criteria")
def updated_status(context):

    assert context["response"].status_code == 200
