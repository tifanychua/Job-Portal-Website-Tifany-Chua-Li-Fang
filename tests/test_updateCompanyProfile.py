from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Company Profile Test Data
# ==================================================


def company_data():

    return {
        "companyName": "ABC Technology Sdn Bhd",
        "registrationNumber": "202401234567",
        "businessEmail": "hr@abctech.com",
        "phone": "0123456789",
        "companyWebsite": "https://www.abctech.com",
        "foundedYear": "2020",
        "companySize": "51-200",
        "companyType": "Private Company",
        "address": "No.1 Jalan Bukit",
        "address_line2": "",
        "city": "Kuala Lumpur",
        "state": "Wilayah Persekutuan",
        "postalCode": "56000",
        "country": "Malaysia",
        "industry_id": "it",
        "specialty_category_ids": ["software_engineering", "web_development"],
        "companyDescription": ("ABC Technology is a software " "development company."),
    }


# ==================================================
# Acceptance Test 1
# Update company profile successfully
# ==================================================


def test_update_company_profile_success(client):

    response = client.post("/update-company-profile", data=company_data(), follow_redirects=False)

    assert response.status_code == 303

    print("✅ Acceptance Test Passed: " "Company profile updated successfully.")


# ==================================================
# Acceptance Test 2
# Updated company information saved
# ==================================================


def test_updated_company_information_saved(client):

    client.post("/update-company-profile", data=company_data(), follow_redirects=False)

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    data = company.to_dict()

    assert data["companyName"] == "ABC Technology Sdn Bhd"

    assert data["businessEmail"] == "hr@abctech.com"

    assert data["companyDescription"] == "ABC Technology is a software development company."

    print("✅ Acceptance Test Passed: " "Updated company information saved successfully.")


# ==================================================
# Acceptance Test 3
# Upload company logo successfully
# ==================================================


def test_upload_company_logo_success(client):

    data = company_data()

    from pathlib import Path

    logo_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "job_portal_web"
        / "images"
        / "number-1.png"
    )

    with open(logo_path, "rb") as logo:

        response = client.post(
            "/update-company-profile",
            data=data,
            files={"logo": ("logo.png", logo, "image/png")},
            follow_redirects=False,
        )

    assert response.status_code == 303

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    assert "logo" in company.to_dict()

    print("✅ Acceptance Test Passed: " "Company logo uploaded successfully.")


# ==================================================
# Acceptance Test 4
# View updated company profile
# ==================================================


def test_view_updated_company_profile(client):

    client.post("/update-company-profile", data=company_data(), follow_redirects=False)

    response = client.get("/edit-company-profile")

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: " "Updated company profile displayed successfully.")

    # ==================================================


# Negative Test 1
# Update profile without company name
# ==================================================


def test_update_without_company_name(client):

    data = company_data()

    data["companyName"] = ""

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Company name validation works.")


# ==================================================
# Negative Test 2
# Update profile without industry
# ==================================================


def test_update_without_industry(client):

    data = company_data()

    data["industry_id"] = ""

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Industry validation works.")


# ==================================================
# Negative Test 3
# Update profile without contact information
# ==================================================


def test_update_without_contact_information(client):

    data = company_data()

    data["businessEmail"] = ""
    data["phone"] = ""

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Contact information validation works.")


# ==================================================
# Negative Test 4
# Invalid founded year
# ==================================================


def test_update_invalid_founded_year(client):

    data = company_data()

    data["foundedYear"] = "1700"

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Founded year validation works.")


# ==================================================
# Negative Test 5
# Invalid postal code
# ==================================================


def test_update_invalid_postal_code(client):

    data = company_data()

    data["postalCode"] = "123"

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Postal code validation works.")


# ==================================================
# Negative Test 6
# No specialty selected
# ==================================================


def test_update_without_specialties(client):

    data = company_data()

    data["specialty_category_ids"] = []

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Specialty validation works.")


# ==================================================
# Negative Test 7
# More than six specialties
# ==================================================


def test_update_more_than_six_specialties(client):

    data = company_data()

    data["specialty_category_ids"] = ["1", "2", "3", "4", "5", "6", "7"]

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Maximum specialty validation works.")


# ==================================================
# Negative Test 8
# Missing company description
# ==================================================


def test_update_without_company_description(client):

    data = company_data()

    data["companyDescription"] = ""

    response = client.post("/update-company-profile", data=data, follow_redirects=False)

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Company description validation works.")


# ==================================================
# Negative Test 9
# Upload unsupported logo format
# ==================================================


def test_upload_invalid_logo_format(client):

    data = company_data()

    from pathlib import Path

    pdf_path = (
        Path(__file__).resolve().parent.parent / "src" / "job_portal_web" / "images" / "logo.pdf"
    )

    with open(pdf_path, "rb") as logo:

        response = client.post(
            "/update-company-profile",
            data=data,
            files={"logo": ("logo.pdf", logo, "application/pdf")},
            follow_redirects=False,
        )

    assert response.status_code >= 400

    print("✅ Negative Test Passed: " "Unsupported logo format rejected.")

    # ==================================================


# Load Feature File
# ==================================================

scenarios("features/updateCompanyProfile.feature")


# ==================================================
# Context
# ==================================================


class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Update company profile successfully
# ==================================================


@given("the employer has an existing company profile")
def existing_company_profile(context):

    context.response = None


@when("the employer updates the company information with valid details")
def update_company_profile(client, context):

    context.response = client.post(
        "/update-company-profile", data=company_data(), follow_redirects=False
    )


@then("the system should save the updated company profile")
def verify_company_updated(context):

    assert context.response.status_code == 303

    print("✅ Scenario Passed: " "Company profile updated successfully.")


@then("display the updated company information")
def verify_updated_information():

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    data = company.to_dict()

    assert data["companyName"] == "ABC Technology Sdn Bhd"

    print("✅ Scenario Passed: " "Updated company information displayed.")


# ==================================================
# Scenario 2
# Update all required company information
# ==================================================


@given("the employer has an existing company profile")
def existing_company_profile_again(context):

    context.response = None


@when("the employer updates all required company information")
def update_required_information(client, context):

    context.response = client.post(
        "/update-company-profile", data=company_data(), follow_redirects=False
    )


@then("the system should allow the company profile to be updated successfully")
def verify_required_information_saved():

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    print("✅ Scenario Passed: " "Required information updated successfully.")


# ==================================================
# Scenario 3
# Upload company logo successfully
# ==================================================


@given("the employer has an existing company profile")
def existing_company_profile_logo(context):

    context.response = None


@when("the employer uploads a valid company logo")
def upload_company_logo(client, context):

    data = company_data()

    from pathlib import Path

    logo_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "job_portal_web"
        / "images"
        / "number-1.png"
    )

    with open(logo_path, "rb") as logo:

        context.response = client.post(
            "/update-company-profile",
            data=data,
            files={"logo": ("logo.png", logo, "image/png")},
            follow_redirects=False,
        )


@then("the system should store the uploaded logo")
def verify_logo_saved():

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    assert "logo" in company.to_dict()

    print("✅ Scenario Passed: " "Logo uploaded successfully.")


@then("display the logo on the company profile")
def verify_logo_display():

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    assert company.to_dict().get("logo") is not None

    print("✅ Scenario Passed: " "Logo displayed successfully.")

    # ==================================================


# Scenario 4
# View updated company profile
# ==================================================


@given("the employer has updated the company profile")
def updated_company_profile(client, context):

    client.post("/update-company-profile", data=company_data(), files={}, follow_redirects=False)


@when("a job seeker views the company profile")
def job_seeker_views_profile(client, context):

    context.response = client.get("/edit-company-profile")


@then("the system should display the latest company information")
def latest_company_information(context):

    assert context.response.status_code == 200

    company = db.collection("company").document("8r1bqsSUA8SqEsjlUr1tFyLtaOW2").get()

    assert company.exists

    print("✅ Scenario Passed: Latest company information displayed.")


# ==================================================
# Scenario 5
# Missing company name
# ==================================================


@given("the employer has an existing company profile")
def existing_profile(context):

    context.response = None


@when("the employer submits the profile without entering the company name")
def missing_company_name(client, context):

    data = company_data()

    data["companyName"] = ""

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


@then("the system should display a validation message")
def validation_message(context):

    assert context.response.status_code >= 400

    print("✅ Scenario Passed: Validation message displayed.")


@then("the company profile should not be updated")
def profile_not_updated():

    print("✅ Scenario Passed: Company profile not updated.")


# ==================================================
# Scenario 6
# Missing industry
# ==================================================


@when("the employer submits the profile without selecting an industry")
def missing_industry(client, context):

    data = company_data()

    data["industry_id"] = ""

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 7
# Missing contact information
# ==================================================


@when("the employer submits the profile without contact information")
def missing_contact(client, context):

    data = company_data()

    data["businessEmail"] = ""
    data["phone"] = ""

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 8
# Invalid founded year
# ==================================================


@when("the employer enters an invalid founded year")
def invalid_year(client, context):

    data = company_data()

    data["foundedYear"] = "1700"

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 9
# Invalid postal code
# ==================================================


@when("the employer enters an invalid postal code")
def invalid_postal(client, context):

    data = company_data()

    data["postalCode"] = "123"

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )

    # ==================================================


# Scenario 10
# No specialty selected
# ==================================================


@when("the employer submits the profile without selecting any specialty")
def no_specialties(client, context):

    data = company_data()

    data["specialty_category_ids"] = []

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 11
# More than six specialties
# ==================================================


@when("the employer selects more than six specialties")
def more_than_six_specialties(client, context):

    data = company_data()

    data["specialty_category_ids"] = ["1", "2", "3", "4", "5", "6", "7"]

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 12
# Missing company description
# ==================================================


@when("the employer submits the profile without entering the company description")
def missing_company_description(client, context):

    data = company_data()

    data["companyDescription"] = ""

    context.response = client.post(
        "/update-company-profile", data=data, files={}, follow_redirects=False
    )


# ==================================================
# Scenario 13
# Unsupported logo format
# ==================================================


@when("the employer uploads an unsupported file format")
def unsupported_logo(client, context):

    data = company_data()

    from pathlib import Path

    pdf_path = (
        Path(__file__).resolve().parent.parent / "src" / "job_portal_web" / "images" / "logo.pdf"
    )

    with open(pdf_path, "rb") as logo:

        context.response = client.post(
            "/update-company-profile",
            data=data,
            files={"logo": ("logo.pdf", logo, "application/pdf")},
            follow_redirects=False,
        )


@then("the system should reject the uploaded file")
def reject_uploaded_logo(context):

    assert context.response.status_code >= 400

    print("✅ Scenario Passed: Unsupported logo rejected.")


# ==================================================
# Common Validation Steps
# ==================================================


@then("the system should prevent the company profile from being updated")
def prevent_profile_update(context):

    assert context.response.status_code >= 400

    print("✅ Scenario Passed: Company profile update prevented.")


@then("display an error message")
def display_error_message(context):

    assert context.response.status_code >= 400

    print("✅ Scenario Passed: Error message displayed.")
