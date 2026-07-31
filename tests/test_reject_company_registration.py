from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient
import pytest

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# =====================================
# LOAD FEATURE FILE
# =====================================

scenarios("features/reject_company_registration.feature")


# =====================================
# CONSTANT
# =====================================

COMPANY_ID = "C000001"


# =====================================
# CLIENT
# =====================================


@pytest.fixture
def client():

    return TestClient(app)


# =====================================
# CONTEXT
# =====================================


@pytest.fixture
def context():

    return {}


# =====================================
# HELPER
# =====================================


def create_pending_company():

    db.collection("company").document(COMPANY_ID).set(
        {"companyName": "ABC Technology Sdn Bhd", "status": "Pending", "test": True}
    )


def delete_test_company():

    doc = db.collection("company").document(COMPANY_ID).get()

    if doc.exists:

        data = doc.to_dict()

        if data.get("test"):

            doc.reference.delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_company()

    yield

    delete_test_company()


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
def reject_company(client, context):

    response = client.post(f"/admin/company/{COMPANY_ID}/reject")

    context["response"] = response


# =====================================
# THEN
# =====================================


@then('the system should update the company status to "Rejected"')
def verify_rejected_status(context):

    response = context["response"]

    assert response.status_code == 200

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company is not None

    assert company["status"] == "Rejected"


@then("the company should not be allowed to access employer features")
def verify_company_access():

    company = db.collection("company").document(COMPANY_ID).get().to_dict()

    assert company["status"] == "Rejected"

    # rejected company should not be active

    assert company["status"] != "Approved"
