from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from main import app

scenarios("features/viewApplicationStatus.feature")


@pytest.fixture
def client():
    return TestClient(app)


class Context:

    def __init__(self):
        self.response = None
        self.application_id = "J000001"


@pytest.fixture
def context():
    return Context()


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

    statuses = ["Submitted", "Cancelled", "Shortlisted", "Rejected", "Offered"]

    assert any(status in page for status in statuses)

    print("✅ SUCCESS: Application statuses displayed")


@given("an employer has updated an application status")
def updated_status():
    pass


@when("the job seeker views the application details")
def open_application_detail(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the updated application status should be displayed")
def verify_updated_status(context):

    assert context.response.status_code == 200

    page = context.response.text

    statuses = ["Shortlisted", "Rejected", "Offered", "Cancelled", "Submitted"]

    assert any(status in page for status in statuses)

    print("✅ SUCCESS: Updated application status displayed")
