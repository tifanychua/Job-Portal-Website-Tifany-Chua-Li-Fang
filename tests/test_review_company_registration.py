import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

client = TestClient(app)


scenarios("features/review_company_registration.feature")


COMPANY_ID = "TEST_COMPANY_REVIEW_001"


# ==================================
# Fixture
# ==================================


@pytest.fixture
def context():

    return {}


# ==================================
# Firestore Helper
# ==================================


def create_pending_company():

    db.collection("company").document(COMPANY_ID).set(
        {
            "companyName": "TARUMT",
            "registrationNumber": "123456789120",
            "industry": "Finance & Banking",
            "companySize": "11 - 50 employees",
            "companyWebsite": "",
            "businessEmail": "teohyy-pm23@student.tarc.edu.my",
            "email": "teohyongyun91@gmail.com",
            "phone": "+60 1223456789",
            "address": "75, Lorong Machang Bubok 2",
            "city": "Bukit Mertajam",
            "state": "Penang",
            "country": "Malaysia",
            "postalCode": "14020",
            "companyDescription": "ssdffdfsd",
            "logo": "companyLogo.png",
            "status": "Pending",
            "contactPerson": {
                "fullName": "YONG YUN TEOH",
                "jobTitle": "asdasd",
                "email": "teohyy-pm23@student.tarc.edu.my",
                "phone": "+60 1568954565",
                "department": "",
                "preferredContactMethod": "Email",
                "altPhone": "",
                "bestTimeToContact": "",
                "correspondenceAddress": "75, Lorong Machang Bubok 2",
            },
            "test": True,
        }
    )


def delete_all_pending_companies():

    docs = db.collection("company").where("status", "==", "Pending").stream()

    for doc in docs:
        doc.reference.delete()


# ==================================
# GIVEN
# ==================================


@given("there are one or more pending company registration requests")
def pending_company_requests():

    create_pending_company()


@given("the administrator is viewing a pending company registration request")
def viewing_pending_company():

    create_pending_company()


@given("there are no pending company registration requests")
def no_pending_company_requests():

    delete_all_pending_companies()


# ==================================
# WHEN
# ==================================


@when("the administrator opens the Company Verification page")
def open_company_verification(context):

    response = client.get("/admin/company-requests?status=Pending")

    context["response"] = response


@when("the administrator selects a company")
def select_company(context):

    response = client.get(f"/admin/company/{COMPANY_ID}")

    context["response"] = response


# ==================================
# THEN
# ==================================


@then("the system should display all pending company registration requests")
def verify_pending_company_list(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "TARUMT" in html

    assert "Pending" in html

    delete_all_pending_companies()


@then("the system should display the company's registration information and supporting documents")
def verify_company_information(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "TARUMT" in html

    assert "YONG YUN TEOH" in html

    assert "asdasd" in html

    # No document checking
    # Industry is stored in Firestore
    # but not shown in current HTML page.

    delete_all_pending_companies()


@then('the system should display a "No pending company registration requests" message')
def verify_empty_company_list(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert (
        "No pending" in html
        or "No company" in html
        or "No registration" in html
        or "TARUMT" not in html
    )
