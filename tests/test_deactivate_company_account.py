from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


scenarios("features/deactivate_company_account.feature")


COMPANY_ID = "C000001"


# Store responses between steps
response_data = {}


# =====================================
# Helper
# =====================================


def create_verified_company():

    db.collection("company").document(COMPANY_ID).set(
        {"companyName": "ABC Technology Sdn Bhd", "status": "Verified", "test": True}
    )


def create_deactivated_company():

    db.collection("company").document(COMPANY_ID).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "status": "Deactivated",
            "deactivationReason": "Policy violation",
            "test": True,
        }
    )


def cleanup():

    doc = db.collection("company").document(COMPANY_ID).get()

    if doc.exists:

        data = doc.to_dict()

        if data.get("test"):

            doc.reference.delete()


# =====================================
# GIVEN
# =====================================


@given("the administrator is viewing a verified company account")
def verified_company():

    create_verified_company()


@given("one or more company accounts have been deactivated")
def existing_deactivated_company():

    create_deactivated_company()


# =====================================
# WHEN
# =====================================


@when("the administrator deactivates the company account")
def deactivate_company():

    response = client.post(f"/admin/company/{COMPANY_ID}/deactivate")

    response_data["response"] = response


@when("the administrator views the company management page")
def view_company_management():

    response = client.get("/admin/company-requests?status=Deactivated")

    response_data["response"] = response


# =====================================
# THEN
# =====================================


@then('the system should update the company status to "Deactivated"')
def verify_company_status():

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company is not None

    assert company["status"] == "Deactivated"


@then("the company should no longer have access to employer features")
def verify_company_access():

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company["status"] == "Deactivated"


@then(
    "the system should display all deactivated company accounts along with their deactivation reasons"
)
def verify_deactivated_company_list():

    response = response_data["response"]

    assert response.status_code == 200

    html = response.text

    assert "ABC Technology Sdn Bhd" in html

    assert "Deactivated" in html

    cleanup()
