import uuid

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app
from job_portal_web.backend.routes import admin

# ==========================================
# LOAD FEATURE
# ==========================================

scenarios("features/approve_company_registration.feature")


# ==========================================
# CONSTANTS
# ==========================================

TEST_COMPANY_EMAIL = "abc@gmail.com"
TEST_COMPANY_NAME = "ABC Technology Sdn Bhd"


# ==========================================
# CLIENT
# ==========================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==========================================
# CONTEXT
# ==========================================


@pytest.fixture
def context():
    return {
        "company_id": None,
        "response": None,
    }


# ==========================================
# UNIQUE TEST COMPANY ID
# ==========================================


@pytest.fixture
def test_company_id():
    unique_value = uuid.uuid4().hex
    company_id = f"TEST_COMPANY_{unique_value}"

    yield company_id

    db.collection("company").document(company_id).delete()


# ==========================================
# MOCK EMAIL
# ==========================================


@pytest.fixture
def mock_email(monkeypatch):
    result = {
        "sent": False,
        "company": None,
        "status": None,
    }

    async def fake_send_company_status_email(company, status):
        result["sent"] = True
        result["company"] = company
        result["status"] = status

    monkeypatch.setattr(
        admin,
        "send_company_status_email",
        fake_send_company_status_email,
    )

    return result


# ==========================================
# TEST DATA HELPERS
# ==========================================


def delete_test_company(company_id):
    if company_id:
        db.collection("company").document(company_id).delete()


def create_pending_company(company_id):
    company_data = {
        "companyName": TEST_COMPANY_NAME,
        "businessEmail": TEST_COMPANY_EMAIL,
        "email": TEST_COMPANY_EMAIL,
        "registrationNumber": f"REG-{company_id[-8:]}",
        "industry": "Technology",
        "status": "Pending",
        "test": True,
    }

    company_ref = db.collection("company").document(company_id)
    company_ref.set(company_data)

    snapshot = company_ref.get()

    assert snapshot.exists, f"Test company {company_id} was not created in Firestore"

    saved_company = snapshot.to_dict()

    assert saved_company is not None
    assert saved_company.get("status") == "Pending"

    return company_id


def get_test_company(company_id):
    snapshot = db.collection("company").document(company_id).get()

    assert snapshot.exists, f"Company {company_id} no longer exists in Firestore"

    company = snapshot.to_dict()

    assert company is not None

    return company


# ==========================================
# SCENARIO 1
# VIEW PENDING COMPANY REQUESTS
# ==========================================


@given("there are pending company registration requests")
def pending_company_requests(context, test_company_id):
    context["company_id"] = create_pending_company(test_company_id)


@when("the admin opens the company registration management page")
def open_company_page(client, context):
    context["response"] = client.get("/admin/company-requests")


@then("the system should display the list of pending registration requests")
def verify_company_list(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text
    assert TEST_COMPANY_NAME in response.text


# ==========================================
# SCENARIO 2
# APPROVE COMPANY
# ==========================================


@given("the admin is reviewing a pending company registration request")
def reviewing_company(context, test_company_id):
    context["company_id"] = create_pending_company(test_company_id)


@when("the admin approves the company registration")
def approve_company(client, context, mock_email):
    company_id = context["company_id"]

    assert company_id is not None

    context["response"] = client.post(
        f"/admin/company/{company_id}/approve",
        follow_redirects=False,
    )


@then('the system should update the company status to "Active"')
def verify_active(context):
    response = context["response"]
    company_id = context["company_id"]

    assert response is not None
    assert company_id is not None
    assert response.status_code == 303, response.text

    company = get_test_company(company_id)

    assert company.get("status") == "Active"


@then("allow the company to access employer features")
def verify_access(context):
    company_id = context["company_id"]

    assert company_id is not None

    company = get_test_company(company_id)

    assert company.get("status") == "Active"


# ==========================================
# SCENARIO 3
# NOTIFY COMPANY AFTER APPROVAL
# ==========================================


@given("the admin has approved a company registration request")
def approved_company(context, test_company_id):
    # The approval action is performed by the following When step.
    context["company_id"] = create_pending_company(test_company_id)


@when("the approval process is completed")
def complete_approval(client, context, mock_email):
    company_id = context["company_id"]

    assert company_id is not None

    context["response"] = client.post(
        f"/admin/company/{company_id}/approve",
        follow_redirects=False,
    )


@then("the system should notify the company")
def verify_notification(context, mock_email):
    response = context["response"]
    company_id = context["company_id"]

    assert response is not None
    assert company_id is not None
    assert response.status_code == 303, response.text

    company = get_test_company(company_id)

    assert company.get("status") == "Active"

    assert mock_email["sent"] is True
    assert mock_email["status"] == "Approved"

    notified_company = mock_email["company"]

    assert notified_company is not None
    assert notified_company.get("email") == TEST_COMPANY_EMAIL
    assert notified_company.get("companyName") == TEST_COMPANY_NAME
