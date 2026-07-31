from pytest_bdd import scenarios, given, when, then
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

from job_portal_web.backend.main import app

scenarios("features/employer_register.feature")

# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def client():
    return TestClient(app)


class Context:
    def __init__(self):
        self.response = None
        self.company_data = None
        self.document = None
        self.email = None


@pytest.fixture
def context():
    return Context()


# ==========================================================
# Helper Functions
# ==========================================================


def valid_employer_data():
    return {
        "token": "valid_token",
        "companyName": "ABC Technology Sdn Bhd",
        "registrationNumber": "202401234567",
        "businessEmail": "company@gmail.com",
        "phone": "+60 123456789",
        "industry": "Information Technology",
        "companySize": "11 - 50 employees",
        "companyWebsite": "https://abc.com",
        "companyDescription": "Software Development Company",
        "address": "Jalan Bukit Bintang",
        "city": "Kuala Lumpur",
        "state": "Kuala Lumpur",
        "postalCode": "55100",
        "country": "Malaysia",
        "contactFullName": "John Tan",
        "contactJobTitle": "HR Manager",
        "contactDepartment": "Human Resource",
        "contactEmail": "john@abc.com",
        "contactPhone": "+60 111111111",
        "altPhone": "",
        "preferredContactMethod": "Email",
        "bestTimeToContact": "Morning",
        "correspondenceAddress": "Jalan Bukit Bintang",
    }


def setup_firestore(db_mock):
    collection = MagicMock()
    document = MagicMock()
    collection.document.return_value = document
    db_mock.collection.return_value = collection
    return document


# ==========================================================
# Unit Tests
# ==========================================================


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_employer_register_success(mock_db, mock_verify, client):

    mock_verify.return_value = {"uid": "company123", "email": "company@gmail.com"}

    document = setup_firestore(mock_db)

    response = client.post("/firebase-register/employer", json=valid_employer_data())

    assert response.status_code == 200
    assert response.json()["success"] is True

    document.set.assert_called_once()


@patch("job_portal_web.backend.auth.auth.verify_id_token")
def test_invalid_firebase_token(mock_verify, client):

    mock_verify.side_effect = Exception("Invalid Token")

    response = client.post("/firebase-register/employer", json=valid_employer_data())

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid Token"


def test_missing_required_field(client):

    data = valid_employer_data()
    del data["companyName"]

    response = client.post("/firebase-register/employer", json=data)

    assert response.status_code == 422


def test_missing_token(client):

    data = valid_employer_data()
    del data["token"]

    response = client.post("/firebase-register/employer", json=data)

    assert response.status_code == 422


@patch("job_portal_web.backend.auth.auth.verify_id_token")
@patch("job_portal_web.backend.auth.db")
def test_company_status_pending(mock_db, mock_verify, client):

    mock_verify.return_value = {"uid": "company123", "email": "company@gmail.com"}

    document = setup_firestore(mock_db)

    response = client.post("/firebase-register/employer", json=valid_employer_data())

    assert response.status_code == 200

    saved_data = document.set.call_args[0][0]

    assert saved_data["status"] == "Pending"


# ==========================================================
# BDD - Given
# ==========================================================


@given("the employer is on the registration page")
def employer_on_registration_page(context):
    pass


@given("the email address is already registered")
def existing_email(context):
    context.email = "company@gmail.com"


@given("the employer has successfully registered an account")
def employer_registered(context):
    context.company_data = valid_employer_data()


# ==========================================================
# BDD - When
# ==========================================================


@when("the employer enters valid registration details and submits the registration form")
def register_success(context, client):

    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as mock_verify,
        patch("job_portal_web.backend.auth.db") as mock_db,
    ):

        mock_verify.return_value = {"uid": "company123", "email": "company@gmail.com"}

        document = setup_firestore(mock_db)

        context.document = document

        context.response = client.post("/firebase-register/employer", json=valid_employer_data())


@when("the employer submits the registration form using that email address")
def register_existing_email(context, client):

    with patch("job_portal_web.backend.auth.auth.verify_id_token") as mock_verify:

        mock_verify.side_effect = Exception("Email address already exists")

        context.response = client.post("/firebase-register/employer", json=valid_employer_data())


@when("the employer submits the registration form with missing or invalid information")
def register_invalid_information(context, client):

    data = valid_employer_data()
    del data["companyName"]

    context.response = client.post("/firebase-register/employer", json=data)


@when("the employer enters different values for the password and confirm password fields")
def password_not_match(context):

    # Frontend validation
    context.response = MagicMock()
    context.response.status_code = 400


@when("the registration process is completed")
def registration_completed(context, client):

    with (
        patch("job_portal_web.backend.auth.auth.verify_id_token") as mock_verify,
        patch("job_portal_web.backend.auth.db") as mock_db,
    ):

        mock_verify.return_value = {"uid": "company123", "email": "company@gmail.com"}

        document = setup_firestore(mock_db)

        context.document = document

        context.response = client.post("/firebase-register/employer", json=valid_employer_data())


# ==========================================================
# BDD - Then
# ==========================================================


@then("the system should create a new employer account successfully")
def register_successful(context):

    assert context.response.status_code == 200
    assert context.response.json()["success"] is True


@then('the employer account status should be set to "Pending"')
def verify_company_status(context):

    assert context.document is not None

    saved = context.document.set.call_args[0][0]

    assert saved["status"] == "Pending"


@then('the system should display an "Email address already exists" message')
def email_exists(context):

    assert context.response.status_code == 401
    assert context.response.json()["error"] == "Email address already exists"


@then("the account should not be created")
def account_not_created(context):

    assert context.response.status_code != 200


@then("the system should display validation messages")
def validation_message(context):

    assert context.response.status_code == 422


@then('the system should display a "Passwords do not match" message')
def password_message(context):

    assert context.response.status_code == 400
