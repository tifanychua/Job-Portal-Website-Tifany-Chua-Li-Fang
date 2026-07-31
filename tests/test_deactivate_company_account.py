from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# =====================================
# LOAD FEATURE
# =====================================

scenarios("features/deactivate_company_account.feature")


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
# TEST DATA
# =====================================

TEST_COMPANY_ID = "TEST_DEACTIVATE_COMPANY_001"


# =====================================
# CLEANUP
# =====================================


def delete_test_company():

    doc = db.collection("company").document(TEST_COMPANY_ID).get()

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
# CREATE COMPANY DATA
# =====================================


def create_verified_company():

    db.collection("company").document(TEST_COMPANY_ID).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "email": "abc@gmail.com",
            "status": "Verified",
            "test": True,
        }
    )

    return TEST_COMPANY_ID


def create_deactivated_company():

    db.collection("company").document(TEST_COMPANY_ID).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "email": "abc@gmail.com",
            "status": "Deactivated",
            "deactivationReason": "Policy violation",
            "test": True,
        }
    )

    return TEST_COMPANY_ID


# =====================================
# SCENARIO 1
# =====================================


@given("the administrator is viewing a verified company account")
def verified_company(context):

    context["company_id"] = create_verified_company()


@when("the administrator deactivates the company account")
def deactivate_company(client, context):

    response = client.post(
        f"/admin/company/{context['company_id']}/deactivate", follow_redirects=False
    )

    context["response"] = response


@then('the system should update the company status to "Deactivated"')
def verify_company_status(context):

    response = context["response"]

    assert response.status_code in (302, 303, 307)

    company = db.collection("company").document(context["company_id"]).get().to_dict()

    assert company["status"] == "Deactivated"


@then("the company should no longer have access to employer features")
def verify_company_access(context):

    company = db.collection("company").document(context["company_id"]).get().to_dict()

    assert company["status"] == "Deactivated"


# =====================================
# SCENARIO 2
# =====================================


@given("one or more company accounts have been deactivated")
def deactivated_company(context):

    context["company_id"] = create_deactivated_company()


@when("the administrator views the company management page")
def view_company_management(client, context):

    response = client.get("/admin/company-requests?status=Deactivated")

    context["response"] = response


@then(
    "the system should display all deactivated company accounts along with their deactivation reasons"
)
def verify_deactivated_company_list(context):

    response = context["response"]

    assert response.status_code == 200

    html = response.text

    assert "ABC Technology Sdn Bhd" in html

    assert "Deactivated" in html


# =====================================
# NORMAL TEST
# =====================================


def test_view_deactivated_company_accounts(client):

    create_deactivated_company()

    response = client.get("/admin/company-requests?status=Deactivated")

    assert response.status_code == 200

    assert "ABC Technology Sdn Bhd" in response.text

    assert "Deactivated" in response.text


# =====================================
# NEGATIVE TEST
# =====================================


def test_deactivate_invalid_company(client):

    response = client.post("/admin/company/INVALID_ID/deactivate")

    assert response.status_code in (404, 500)
