from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient
import pytest

from job_portal_web.backend.main import app

client = TestClient(app)


scenarios("features/filterApplicantsByApplicationDate.feature")


@pytest.fixture
def context():
    return {}


# =====================================================
# Given
# =====================================================


@given("the employer has received applications for one or more job postings")
def applications_exist():
    pass


@given("the employer is viewing the Applicant Management page")
def applicant_management_page():
    pass


@given("the employer is on the Applicant Management page")
def applicant_page():
    pass


@given("the employer applies an application date filter")
def apply_date_filter():
    pass


@given("the employer is viewing filtered applicants")
def viewing_filtered_applicants():
    pass


# =====================================================
# When
# =====================================================


@when("the employer selects a specific application date filter")
def specific_date_filter(context):

    context["response"] = client.get(
        "/applications",
        params={"date": "today"},
    )


@when("the employer selects a start date and end date for filtering")
def date_range_filter(context):

    context["response"] = client.get(
        "/applications",
        params={
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
        },
    )


@when("the employer does not apply any application date filter")
def no_date_filter(context):

    context["response"] = client.get("/applications")


@when("no applicants match the selected date or date range")
def no_matching_date(context):

    context["response"] = client.get(
        "/applications",
        params={
            "start_date": "1990-01-01",
            "end_date": "1990-01-02",
        },
    )


@when("the employer changes the application date filter")
def change_date_filter(context):

    context["response"] = client.get(
        "/applications",
        params={"date": "7days"},
    )


# =====================================================
# Then
# =====================================================


@then("the system should display only applicants who submitted applications on the selected date")
def specific_date_results(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display applicants who applied within the selected date range")
def date_range_results(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display all applicants regardless of application date")
def all_applications(context):

    response = context["response"]

    assert response.status_code == 200


@then('the system should display a "No applicants found for this date range" message')
def no_date_results(context):

    response = context["response"]

    assert response.status_code == 200

    assert (
        "No applicants found for this date range" in response.text
        or "No applicants found." in response.text
    )


@then("the system should refresh the applicant list")
def refresh_list(context):

    response = context["response"]

    assert response.status_code == 200


@then("display applicants matching the new date criteria")
def updated_date_results(context):

    response = context["response"]

    assert response.status_code == 200
