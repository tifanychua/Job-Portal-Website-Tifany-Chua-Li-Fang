from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from job_portal_web.backend.main import app
import pytest

scenarios("features/login.feature")


@pytest.fixture
def client():
    return TestClient(app)


class Context:
    def __init__(self):
        self.response = None
        self.login_response = None
        self.auth_token = None
        self.profile_response = None
        self.jobs_response = None
        self.applications_response = None


@pytest.fixture
def context():
    return Context()


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_login_success(mock_db, mock_verify, client):
    mock_verify.return_value = {"uid": "user123"}
    doc = MagicMock()
    doc.exists = True
    mock_db.collection.return_value.document.return_value.get.return_value = doc

    response = client.post("/firebase-login", json={"token": "valid_token"})

    assert response.status_code == 200
    assert response.json()["redirect"] == "/"


@patch("job_portal_web.backend.auth.auth.verify_id_token")
def test_login_invalid_token(mock_verify, client):
    mock_verify.side_effect = Exception("Invalid Token")

    response = client.post("/firebase-login", json={"token": "wrong_token"})

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid Token"


def test_login_empty_token(client):
    response = client.post("/firebase-login", json={})
    assert response.status_code == 422


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_login_user_not_found(mock_db, mock_verify, client):
    mock_verify.return_value = {"uid": "abc123"}

    job_doc = MagicMock()
    job_doc.exists = False

    company_doc = MagicMock()
    company_doc.exists = False

    mock_db.collection.side_effect = [
        MagicMock(document=MagicMock(return_value=MagicMock(get=MagicMock(return_value=job_doc)))),
        MagicMock(
            document=MagicMock(return_value=MagicMock(get=MagicMock(return_value=company_doc)))
        ),
    ]

    response = client.post("/firebase-login", json={"token": "valid"})

    assert response.status_code == 404
    assert (
        response.json()["error"]
        == "No account information was found. Please complete your registration or contact support."
    )


@given("the job seeker has a registered account")
def step_registered_account():
    pass


@when("the job seeker enters a valid email address and password")
def step_valid_login(client, context):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):

        verify.return_value = {"uid": "user123"}
        doc = MagicMock()
        doc.exists = True
        db.collection.return_value.document.return_value.get.return_value = doc

        context.response = client.post("/firebase-login", json={"token": "valid_token"})


@then("the system should authenticate the user successfully")
def step_auth_success(context):
    assert context.response.status_code == 200


@then("redirect the job seeker to the dashboard")
def step_redirect(context):
    assert context.response.json()["redirect"] == "/"


@given("the job seeker has entered incorrect login credentials")
def step_invalid_credentials():
    pass


@when("the job seeker attempts to log in")
def step_attempt_login(client, context):
    with patch("job_portal_web.backend.auth.auth.verify_id_token") as verify:
        verify.side_effect = Exception("Invalid Token")
        context.response = client.post("/firebase-login", json={"token": "wrong_token"})


@then("the system should display an error message")
def step_error(context):
    assert context.response.status_code == 401


@then("prevent access to the account")
def step_prevent(context):
    assert context.response.json()["error"] == "Invalid Token"


@given("the job seeker is on the login page")
def step_login_page():
    pass


@when("the job seeker leaves the email address or password field empty")
def step_empty(client, context):
    context.response = client.post("/firebase-login", json={})


@when("attempts to log in")
def step_attempt():
    pass


@then("the system should display validation messages")
def step_validation(context):
    assert context.response.status_code == 422


@then("request the job seeker to complete the required fields")
def step_required():
    pass


@given("the job seeker has logged in successfully")
def job_seeker_logged_in(client, context):
    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as verify,
        patch("job_portal_web.backend.auth.db") as db,
    ):

        verify.return_value = {"uid": "user123"}
        doc = MagicMock()
        doc.exists = True
        db.collection.return_value.document.return_value.get.return_value = doc

        context.login_response = client.post("/firebase-login", json={"token": "valid_token"})
        context.auth_token = context.login_response.json().get("token")


@when("the job seeker accesses the platform")
def job_seeker_access(client, context):
    headers = {"Authorization": f"Bearer {context.auth_token}"}
    context.profile_response = client.get("/profile", headers=headers)
    context.jobs_response = client.get("/jobs", headers=headers)


@then("the system should allow access to profile and job search features")
def job_seeker_access_allowed(context):
    assert context.profile_response.status_code == 200
    assert context.jobs_response.status_code == 200
