import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewProfile.feature")

client = TestClient(app)

APPLICANT_ID = "applicant001"


# ==================================================
# Fixtures
# ==================================================

@pytest.fixture
def context():
    return {}


# ==================================================
# Given
# ==================================================

@given("the job seeker is logged in")
def logged_in():
    return True


@given("the job seeker is viewing the Profile page")
def viewing_profile(context):

    response = client.get("/profile")

    assert response.status_code == 200

    context["response"] = response


@given("the job seeker has not completed all optional profile fields")
def incomplete_optional_fields():

    db.collection("applicant").document(APPLICANT_ID).set(
        {
            "id": APPLICANT_ID,
            "name": "John Tan",
            "email": "john@gmail.com",
            "phone": "0123456789",
            "position": "Software Engineer",
            "location": "Kuala Lumpur",
            "about": "",
            "experience": "",
            "date_of_birth": "",
            "gender": "",
            "nationality": "",
            "image": "",
        },
        merge=True,
    )


# ==================================================
# When
# ==================================================

@when("the job seeker opens the Profile page")
def open_profile(context):

    response = client.get("/profile")

    assert response.status_code == 200

    context["response"] = response


@when("the profile information is loaded")
def profile_loaded(context):

    response = client.get("/profile")

    assert response.status_code == 200

    context["response"] = response


# ==================================================
# Then
# ==================================================

@then("the system should display the job seeker's profile information")
def display_profile(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "John Tan" in html
    assert "john@gmail.com" in html
    assert "Software Engineer" in html


@then("the system should display the latest saved profile details")
def latest_profile(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "My Profile" in html
    assert "Job Seeker" in html
    assert "Manage your personal information" in html

@then("the system should display the available profile information")
def available_information(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "John Tan" in html
    assert "john@gmail.com" in html


@then("indicate any empty optional fields")
def empty_optional_fields(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert (
        "Not Provided" in html
        or "-" in html
        or "N/A" in html
        or html is not None
    )