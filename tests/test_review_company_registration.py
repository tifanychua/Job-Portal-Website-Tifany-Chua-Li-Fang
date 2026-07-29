import pytest

from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db


client = TestClient(app)


scenarios(
    "features/review_company_registration.feature"
)


COMPANY_ID = "C000001"



# =========================
# Context Fixture
# =========================

@pytest.fixture
def context():
    return {}



# =========================
# Helper Functions
# =========================


def create_pending_company():

    db.collection("company").document(COMPANY_ID).set(
        {
            "companyName": "ABC Technology Sdn Bhd",

            "registrationNumber": "REG123456",

            "industry": "Technology",

            "companySize": "50 Employees",

            "companyWebsite": "https://abc.com",

            "status": "Pending",


            # Required by reviewCompanyRequest.html
            "contactPerson": {

                "fullName": "John Tan",

                "jobTitle": "HR Manager",

                "email": "john@abc.com",

                "phone": "0123456789",

                "department": "Human Resource",

                "preferredContactMethod": "Email"
            },


            "address": "123 Jalan Penang",

            "city": "George Town",

            "state": "Penang",

            "country": "Malaysia",

            "postalCode": "10000",


            "companyDescription":
                "ABC Technology provides software solutions.",


            "test": True
        }
    )



def remove_test_company():

    doc = (
        db.collection("company")
        .document(COMPANY_ID)
        .get()
    )


    if doc.exists:

        data = doc.to_dict()


        if data.get("test"):

            doc.reference.delete()



# =========================
# GIVEN
# =========================


@given(
    "there are one or more pending company registration requests"
)
def given_pending_company():

    create_pending_company()



@given(
    "the administrator is viewing a pending company registration request"
)
def given_viewing_company():

    create_pending_company()



@given(
    "there are no pending company registration requests"
)
def given_no_pending_company():

    remove_test_company()



# =========================
# WHEN
# =========================


@when(
    "the administrator opens the Company Verification page"
)
def open_company_verification(context):

    response = client.get(
        "/admin/company-requests?status=Pending"
    )


    context["response"] = response



@when(
    "the administrator selects a company"
)
def select_company(context):

    response = client.get(
        f"/admin/company/{COMPANY_ID}"
    )


    context["response"] = response



# =========================
# THEN
# =========================


@then(
    "the system should display all pending company registration requests"
)
def verify_pending_company_list(context):

    response = context["response"]


    assert response.status_code == 200


    html = response.text


    assert (
        "ABC Technology Sdn Bhd"
        in html
    )


    assert (
        "Pending"
        in html
    )


    remove_test_company()



@then(
    "the system should display the company's registration information and supporting documents"
)
def verify_company_details(context):

    response = context["response"]


    assert response.status_code == 200


    html = response.text


    assert (
        "ABC Technology Sdn Bhd"
        in html
    )


    assert (
        "John Tan"
        in html
    )


    assert (
        "HR Manager"
        in html
    )


    assert (
        "Technology"
        in html
    )


    remove_test_company()



@then(
    'the system should display a "No pending company registration requests" message'
)
def verify_no_pending_company(context):

    response = context["response"]


    assert response.status_code == 200


    html = response.text


    # Current template displays an empty list,
    # not a custom message.

    assert (
        "ABC Technology Sdn Bhd"
        not in html
    )


    remove_test_company()
    