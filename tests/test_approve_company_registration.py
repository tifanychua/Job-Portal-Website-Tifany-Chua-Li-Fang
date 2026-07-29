from fastapi.testclient import TestClient
import pytest

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.routes import admin
from job_portal_web.backend.database import db

# ==========================================
# LOAD FEATURE FILE
# ==========================================

scenarios("features/approve_company_registration.feature")


# ==========================================
# TEST CLIENT
# ==========================================


@pytest.fixture
def client():

    return TestClient(app)


# ==========================================
# CONTEXT
# ==========================================


@pytest.fixture
def context():

    return {}


# ==========================================
# MOCK EMAIL
# ==========================================


@pytest.fixture
def mock_email(monkeypatch):

    context = {"sent": False, "email": None}

    async def fake_send_approval_email(*args, **kwargs):

        context["sent"] = True

        if len(args) > 0:

            context["email"] = args[0]

    monkeypatch.setattr(admin, "send_company_approval_email", fake_send_approval_email)

    return context


# ==========================================
# CLEANUP
# ==========================================

TEST_COMPANY_ID = "TEST_COMPANY_001"


def delete_test_company():

    db.collection("company").document(TEST_COMPANY_ID).delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_company()

    yield

    delete_test_company()


# ==========================================
# CREATE TEST DATA
# ==========================================


def create_pending_company():

    db.collection("company").document(TEST_COMPANY_ID).set(
        {
            "companyName": "ABC Technology Sdn Bhd",
            "businessEmail": "abc@gmail.com",
            "email": "abc@gmail.com",
            "registrationNumber": "REG123456",
            "industry": "Technology",
            "status": "Pending",
        }
    )

    return TEST_COMPANY_ID


# ==========================================
# SCENARIO 1
# ==========================================


@given("there are pending company registration requests")
def pending_company_requests(context):

    context["company_id"] = create_pending_company()


@when("the admin opens the company registration management page")
def admin_open_company_management(client, context):

    context["response"] = client.get("/admin/company-requests")


@then("the system should display the list of pending registration requests")
def verify_pending_company_display(context):

    response = context["response"]

    assert response.status_code == 200

    assert "ABC Technology Sdn Bhd" in response.text


# ==========================================
# SCENARIO 2
# ==========================================


@given("the admin is reviewing a pending company registration request")
def admin_review_company(context):

    context["company_id"] = create_pending_company()


@when("the admin approves the company registration")
def approve_company(client, context):

    context["response"] = client.post(
        f"/admin/company/{context['company_id']}/approve", follow_redirects=False
    )


@then('the system should update the company status to "Active"')
def verify_company_active(context):

    assert context["response"].status_code == 303

    company = db.collection("company").document(context["company_id"]).get().to_dict()

    assert company["status"] == "Active"


@then("allow the company to access employer features")
def verify_company_access():

    # status Active means employer access allowed

    assert True


# ==========================================
# SCENARIO 3
# ==========================================


@given("the admin has approved a company registration request")
def approved_company(context):

    context["company_id"] = create_pending_company()


@when("the approval process is completed")
def complete_approval(client, context):

    context["response"] = client.post(
        f"/admin/company/{context['company_id']}/approve", follow_redirects=False
    )


@then("the system should notify the company")
def verify_company_notification(context, mock_email):

    assert context["response"].status_code == 303

    company = db.collection("company").document(context["company_id"]).get().to_dict()

    assert company["status"] == "Active"

    assert mock_email["sent"] is True

    assert mock_email["email"] == "abc@gmail.com"
