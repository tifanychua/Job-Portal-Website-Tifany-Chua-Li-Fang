from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# =====================================
# LOAD FEATURE
# =====================================

scenarios("features/deactivate_company_account.feature")


# =====================================
# CLIENT
# =====================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# =====================================
# CONTEXT
# =====================================


@pytest.fixture
def context():
    return {
        "company_id": None,
        "response": None,
    }


# =====================================
# TEST DATA FIXTURE
# =====================================


@pytest.fixture
def company_id():
    test_company_id = f"TEST_DEACTIVATE_COMPANY_{uuid4().hex}"

    yield test_company_id

    document_reference = db.collection("company").document(test_company_id)

    document = document_reference.get()

    if document.exists:
        data = document.to_dict()

        if data and data.get("test") is True:
            document_reference.delete()


# =====================================
# CREATE COMPANY DATA
# =====================================


def create_verified_company(company_id):
    db.collection("company").document(company_id).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "email": "abc@gmail.com",
            "status": "Verified",
            "test": True,
        }
    )

    return company_id


def create_deactivated_company(company_id):
    db.collection("company").document(company_id).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "email": "abc@gmail.com",
            "status": "Deactivated",
            "deactivationReason": "Policy violation",
            "test": True,
        }
    )

    return company_id


# =====================================
# SCENARIO 1
# =====================================


@given("the administrator is viewing a verified company account")
def verified_company(context, company_id):
    context["company_id"] = create_verified_company(company_id)


@when("the administrator deactivates the company account")
def deactivate_company(client, context):
    context["response"] = client.post(
        f"/admin/company/{context['company_id']}/deactivate",
        follow_redirects=False,
    )


@then('the system should update the company status to "Deactivated"')
def verify_company_status(context):
    response = context["response"]

    assert response.status_code in (200, 302, 303, 307)

    document = db.collection("company").document(context["company_id"]).get()

    assert document.exists

    company = document.to_dict()

    assert company is not None
    assert company["status"] == "Deactivated"


@then("the company should no longer have access to employer features")
def verify_company_access(context):
    document = db.collection("company").document(context["company_id"]).get()

    assert document.exists

    company = document.to_dict()

    assert company is not None
    assert company["status"] == "Deactivated"


# =====================================
# SCENARIO 2
# =====================================


@given("one or more company accounts have been deactivated")
def deactivated_company(context, company_id):
    context["company_id"] = create_deactivated_company(company_id)


@when("the administrator views the company management page")
def view_company_management(client, context):
    context["response"] = client.get(
        "/admin/company-requests",
        params={"status": "Deactivated"},
    )


@then(
    "the system should display all deactivated company accounts "
    "along with their deactivation reasons"
)
def verify_deactivated_company_list(context):
    response = context["response"]

    assert response.status_code == 200

    document = db.collection("company").document(context["company_id"]).get()

    assert document.exists

    company = document.to_dict()

    assert company is not None
    assert company["companyName"] == "ABC Technology Sdn Bhd"
    assert company["status"] == "Deactivated"
    assert company["deactivationReason"] == "Policy violation"

    # Verify what the page actually shows
    assert "ABC Technology Sdn Bhd" in response.text
    assert "Deactivated" in response.text


# =====================================
# NORMAL TEST
# =====================================


def test_view_deactivated_company_accounts(client, company_id):
    create_deactivated_company(company_id)

    document = db.collection("company").document(company_id).get()

    assert document.exists

    company = document.to_dict()

    assert company is not None
    assert company["companyName"] == "ABC Technology Sdn Bhd"
    assert company["status"] == "Deactivated"
    assert company["deactivationReason"] == "Policy violation"

    response = client.get(
        "/admin/company-requests",
        params={"status": "Deactivated"},
    )

    assert response.status_code == 200
    assert "ABC Technology Sdn Bhd" in response.text
    assert "Deactivated" in response.text


# =====================================
# NEGATIVE TEST
# =====================================


def test_deactivate_invalid_company(client):
    invalid_company_id = f"INVALID_COMPANY_{uuid4().hex}"

    response = client.post(
        f"/admin/company/{invalid_company_id}/deactivate",
        follow_redirects=False,
    )

    assert response.status_code in (404, 500)
