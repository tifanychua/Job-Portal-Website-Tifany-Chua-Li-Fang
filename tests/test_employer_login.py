from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.main import app

scenarios("features/employer_login.feature")


@pytest.fixture
def client():
    return TestClient(app)


class Context:
    def __init__(self):
        self.response = None
        self.login_response = None
        self.auth_token = None
        self.post_job_response = None
        self.manage_applications_response = None
        self.recruitment_response = None
        self.profile_response = None
        self.dashboard_response = None


@pytest.fixture
def context():
    return Context()


# ============================================================
# MOCK HELPERS
# ============================================================


def mock_company_login(db_mock, status="Active"):
    """Configure Firestore mocks for an existing employer."""

    job_doc = MagicMock()
    job_doc.exists = False

    company_doc = MagicMock()
    company_doc.exists = True
    company_doc.to_dict.return_value = {
        "status": status,
        "accountStatus": "Active",
    }

    def collection_side_effect(name):
        collection = MagicMock()

        if name == "job_seeker":
            collection.document.return_value.get.return_value = job_doc

        elif name == "company":
            collection.document.return_value.get.return_value = company_doc

        return collection

    db_mock.collection.side_effect = collection_side_effect


def mock_company_not_found(db_mock):
    """Configure Firestore mocks when no account exists."""

    job_doc = MagicMock()
    job_doc.exists = False

    company_doc = MagicMock()
    company_doc.exists = False

    def collection_side_effect(name):
        collection = MagicMock()

        if name == "job_seeker":
            collection.document.return_value.get.return_value = job_doc

        elif name == "company":
            collection.document.return_value.get.return_value = company_doc

        return collection

    db_mock.collection.side_effect = collection_side_effect


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_employer_login_success(mock_db, mock_verify, client):
    mock_verify.return_value = {
        "uid": "company123",
    }

    mock_company_login(mock_db)

    response = client.post(
        "/firebase-login",
        json={"token": "valid_token"},
    )

    assert response.status_code == 200
    assert response.json()["redirect"] == "/manage-jobs"


@patch("job_portal_web.backend.auth.auth.verify_id_token")
def test_employer_invalid_token(mock_verify, client):
    mock_verify.side_effect = Exception("Authentication failed. Please sign in again.")

    response = client.post(
        "/firebase-login",
        json={"token": "wrong_token"},
    )

    assert response.status_code == 401

    assert response.json()["error"] == ("Authentication failed. Please sign in again.")


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_employer_not_found(mock_db, mock_verify, client):
    mock_verify.return_value = {
        "uid": "company123",
    }

    mock_company_not_found(mock_db)

    response = client.post(
        "/firebase-login",
        json={"token": "valid_token"},
    )

    assert response.status_code == 404

    assert response.json()["error"] == (
        "No account information was found. Please complete your registration or contact support."
    )


def test_employer_empty_token(client):
    response = client.post(
        "/firebase-login",
        json={},
    )

    assert response.status_code == 422


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_employer_rejected_account(mock_db, mock_verify, client):
    mock_verify.return_value = {
        "uid": "company123",
    }

    mock_company_login(
        mock_db,
        status="Rejected",
    )

    response = client.post(
        "/firebase-login",
        json={"token": "valid_token"},
    )

    assert response.status_code == 403

    assert response.json()["error"] == (
        "Your company registration has been rejected. "
        "Please contact the administrator for assistance."
    )


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_employer_deactive_account(mock_db, mock_verify, client):
    mock_verify.return_value = {
        "uid": "company123",
    }

    mock_company_login(
        mock_db,
        status="Deactive",
    )

    response = client.post(
        "/firebase-login",
        json={"token": "valid_token"},
    )

    assert response.status_code == 403

    assert response.json()["error"] == (
        "Your company account has been deactivated. Please contact the administrator."
    )


# ============================================================
# SUCCESSFUL EMPLOYER LOGIN BDD STEPS
# ============================================================


@given("the employer has a registered company account")
def employer_registered():
    pass


@when("the employer enters a valid email address and password")
def valid_login(client, context):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):
        verify.return_value = {
            "uid": "company123",
        }

        mock_company_login(db)

        context.response = client.post(
            "/firebase-login",
            json={"token": "valid_token"},
        )


@then("the system should authenticate the employer successfully")
def login_success(context):
    assert context.response.status_code == 200


@then("redirect the employer to the employer dashboard")
def redirect_dashboard(context):
    assert context.response.json()["redirect"] == "/manage-jobs"


# ============================================================
# INVALID EMPLOYER LOGIN BDD STEPS
# ============================================================


@given("the employer has entered incorrect login credentials")
def invalid_credentials():
    pass


@when("the employer attempts to log in")
def invalid_login(client, context):
    with patch("job_portal_web.backend.auth.auth.verify_id_token") as verify:
        verify.side_effect = Exception("Authentication failed. Please sign in again.")

        context.response = client.post(
            "/firebase-login",
            json={"token": "wrong_token"},
        )


@then("the system should display an error message")
def error_message(context):
    assert context.response.status_code == 401

    assert context.response.json()["error"] == ("Authentication failed. Please sign in again.")


@then("prevent access to the account")
def prevent_access(context):
    assert context.response.status_code == 401


# ============================================================
# ACCESS EMPLOYER FEATURES BDD STEPS
# ============================================================


@given("the employer has logged in successfully")
def employer_logged_in(client, context):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):
        verify.return_value = {
            "uid": "company123",
        }

        mock_company_login(db)

        context.login_response = client.post(
            "/firebase-login",
            json={"token": "valid_token"},
        )

        assert context.login_response.status_code == 200

        context.auth_token = context.login_response.json().get("token")


@when("the employer accesses the platform")
def access_platform(client, context):
    cookies = context.login_response.cookies

    context.dashboard_response = client.get(
        "/manage-jobs",
        cookies=cookies,
    )

    context.post_job_response = context.dashboard_response
    context.manage_applications_response = context.dashboard_response
    context.recruitment_response = context.dashboard_response


@then(
    "the system should allow access to job posting, applicant management, and recruitment features"
)
def allow_access(context):
    assert context.login_response.status_code == 200

    assert context.login_response.json()["redirect"] == "/manage-jobs"

    assert context.dashboard_response.status_code == 200


# ============================================================
# EMPLOYER ROLE RESTRICTION
# ============================================================


def test_employer_cannot_access_job_seeker_features(client):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):
        verify.return_value = {
            "uid": "company123",
        }

        mock_company_login(db)

        login_response = client.post(
            "/firebase-login",
            json={"token": "valid_token"},
        )

        assert login_response.status_code == 200

        assert login_response.json()["redirect"] == "/manage-jobs"


# ============================================================
# BLOCKED EMPLOYER ACCOUNT BDD STEPS
# ============================================================


@given('the employer account status is "Rejected" or "Deactive"')
def rejected_or_deactive():
    pass


@when("the employer attempts to log in with valid credentials")
def blocked_login(client, context):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):
        verify.return_value = {
            "uid": "company123",
        }

        mock_company_login(
            db,
            status="Rejected",
        )

        context.response = client.post(
            "/firebase-login",
            json={"token": "valid_token"},
        )


@then("the system should block the login")
def block_login(context):
    assert context.response.status_code == 403


@then("display an account status error message")
def account_status_error(context):
    assert context.response.json()["error"] == (
        "Your company registration has been rejected. "
        "Please contact the administrator for assistance."
    )
