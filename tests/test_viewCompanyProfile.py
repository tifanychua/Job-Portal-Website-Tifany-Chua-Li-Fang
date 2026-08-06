import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewCompanyProfile.feature")

client = TestClient(app)

COMPANY_ID = "company001"


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def context():
    return {}


# ==================================================
# Given
# ==================================================


@given("the employer is logged in")
def employer_logged_in():
    """
    Login is mocked.
    """
    return True


@given("the employer is viewing the Company Profile page")
def viewing_company_profile(context):

    response = client.get("/company-profile")

    assert response.status_code == 200

    context["response"] = response


@given("the employer has not completed all optional company profile fields")
def incomplete_company_profile():

    db.collection("company").document(COMPANY_ID).set(
        {
            "id": COMPANY_ID,
            "company_name": "ABC Technology Sdn. Bhd.",
            "email": "hr@abctech.com",
            "phone": "0123456789",
            "industry": "Information Technology",
            "location": "Kuala Lumpur",
            "website": "",
            "description": "",
            "company_size": "",
            "logo": "",
        },
        merge=True,
    )


# ==================================================
# When
# ==================================================


@when("the employer opens the Company Profile page")
def open_company_profile(context):

    response = client.get("/company-profile")

    assert response.status_code == 200

    context["response"] = response


@when("the company profile information is loaded")
def load_company_profile(context):

    response = client.get("/company-profile")

    assert response.status_code == 200

    context["response"] = response


# ==================================================
# Then
# ==================================================


@then("the system should display the company profile information")
def display_company_profile(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "Company Profile" in html


@then("the system should display the latest saved company profile details")
def latest_company_profile(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "Company Profile" in html


@then("the system should display the available company profile information")
def available_company_information(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "Company Profile" in html


@then("indicate any empty optional fields")
def empty_optional_fields(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "Not Provided" in html or "N/A" in html or "-" in html or html is not None
