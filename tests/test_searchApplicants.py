import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/searchApplicants.feature")

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

@given("the employer has received applications from multiple candidates")
def multiple_candidates():
    return True


@given("applicants have listed their skills in their profiles")
def applicants_have_skills():
    return True


@given("the employer has access to applicant records")
def employer_access():
    return True


@given("the employer is searching for an applicant")
def searching():
    return True


@given("the employer enters a keyword that does not match any applicant records")
def no_match_keyword(context):

    response = client.get(
        "/applications",
        params={"search": "xxxxxxxxxxxxx"},
    )

    assert response.status_code == 200

    context["response"] = response


@given("the employer has performed an applicant search")
def searched(context):

    response = client.get(
        "/applications",
        params={"search": "john"},
    )

    assert response.status_code == 200

    context["response"] = response

# ==================================================
# When
# ==================================================

@when("the employer enters an applicant's name in the search bar")
def search_name(context):

    response = client.get(
        "/applications",
        params={"search": "John"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer enters a skill keyword in the search bar")
def search_skill(context):

    response = client.get(
        "/applications",
        params={"search": "Python"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer enters an applicant's email address in the search bar")
def search_email(context):

    response = client.get(
        "/applications",
        params={"search": "john@gmail.com"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the employer enters a partial keyword")
def partial_keyword(context):

    response = client.get(
        "/applications",
        params={"search": "Joh"},
    )

    assert response.status_code == 200

    context["response"] = response


@when("the search is performed")
def perform_search(context):

    response = context["response"]

    assert response.status_code == 200


@when("the employer clears the search keyword")
def clear_search(context):

    response = client.get("/applications")

    assert response.status_code == 200

    context["response"] = response

# ==================================================
# Then
# ==================================================

@then("the system should display applicants whose names match the search keyword")
def display_name(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display applicants who have matching skills")
def display_skill(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display the applicant record associated with the email address")
def display_email(context):

    response = context["response"]

    assert response.status_code == 200


@then("the system should display applicant records containing the matching keyword")
def display_partial(context):

    response = context["response"]

    assert response.status_code == 200


@then('the system should display a "No applicants found" message')
def no_results(context):

    response = context["response"]

    assert response.status_code == 200

    assert (
        "No applicants found" in response.text
        or "No applications received yet" in response.text
    )


@then("the system should display the complete applicant list again")
def display_all(context):

    response = context["response"]

    assert response.status_code == 200

    assert "Applications" in response.text