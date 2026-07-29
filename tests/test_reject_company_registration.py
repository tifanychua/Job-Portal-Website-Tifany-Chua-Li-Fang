from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


scenarios("features/reject_company_registration.feature")


COMPANY_ID = "C000001"


# Store response
response_data = {}


# =====================================
# Helper
# =====================================


def create_pending_company():

    db.collection("company").document(COMPANY_ID).set(
        {"companyName": "ABC Technology Sdn Bhd", "status": "Pending", "test": True}
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


@given("the administrator is reviewing a pending company registration request")
def pending_company():

    create_pending_company()


# =====================================
# WHEN
# =====================================


@when("the administrator rejects the registration request")
def reject_company():

    response = client.post(f"/admin/company/{COMPANY_ID}/reject")

    response_data["response"] = response


# =====================================
# THEN
# =====================================


@then('the system should update the company status to "Rejected"')
def verify_rejected_status():

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company is not None

    assert company["status"] == "Rejected"


@then("the company should not be allowed to access employer features")
def verify_company_access():

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company["status"] == "Rejected"

    cleanup()
