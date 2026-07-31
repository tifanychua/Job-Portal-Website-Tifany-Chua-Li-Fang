from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from job_portal_web.backend.main import app
from job_portal_web.backend import job_application


# --------------------------------------------------
# Fake Login
# --------------------------------------------------

@pytest.fixture(autouse=True)
def fake_login(monkeypatch):

    def fake_current_user(request):

        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = "J000001"

        return (
            "J000001",
            {
                "uid": "J000001",
                "full_name": "Test User",
                "headline": "Software Engineer",
                "photo": "user.png",
            },
        )

    monkeypatch.setattr(
        job_application,
        "_get_current_job_seeker",
        fake_current_user,
    )


# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------
# Acceptance Test 1
# --------------------------------------------------

def test_view_application_status_list(client: TestClient):

    response = client.get("/application")

    if response.status_code == 200:

        page = response.text

        statuses = [
            "Submitted",
            "Cancelled",
            "Shortlisted",
            "Rejected",
            "Offered",
        ]

        if any(status in page for status in statuses):
            print("✅ SUCCESS: Job seeker views application statuses")
        else:
            print("❌ FAILED: Application statuses not found")

    else:
        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code == 200
    assert any(status in response.text for status in statuses)


# --------------------------------------------------
# Acceptance Test 2
# --------------------------------------------------

def test_view_updated_application_status(client: TestClient):

    application_id = "5iVgjmXsCDG4lpM5uUuj"

    response = client.get(f"/application/{application_id}")

    if response.status_code == 200:

        page = response.text

        statuses = [
            "Submitted",
            "Cancelled",
            "Shortlisted",
            "Rejected",
            "Offered",
        ]

        if any(status in page for status in statuses):
            print("✅ SUCCESS: Job seeker views updated application status")
        else:
            print("❌ FAILED: Updated status not found")

    else:
        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code == 200
    assert any(status in response.text for status in statuses)


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/viewApplicationStatus.feature")


# --------------------------------------------------
# Context
# --------------------------------------------------

class Context:

    def __init__(self):

        self.response = None
        self.application_id = "5iVgjmXsCDG4lpM5uUuj"


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1
# --------------------------------------------------

@given("the job seeker has submitted job applications")
def submitted_applications():
    pass


@when("the job seeker opens the application status page")
def open_status_page(client, context):

    context.response = client.get("/application")


@then("the system should display the current status of each application")
def verify_status_list(context):

    assert context.response.status_code == 200

    page = context.response.text

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in page for status in statuses)

    print("✅ SUCCESS: Application statuses displayed")


# --------------------------------------------------
# Scenario 2
# --------------------------------------------------

@given("an employer has updated an application status")
def updated_status():
    pass


@when("the job seeker views the application details")
def open_application_detail(client, context):

    context.response = client.get(
        f"/application/{context.application_id}"
    )


@then("the updated application status should be displayed")
def verify_updated_status(context):

    assert context.response.status_code == 200

    page = context.response.text

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in page for status in statuses)

    print("✅ SUCCESS: Updated application status displayed")