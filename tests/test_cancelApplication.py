from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from main import app

scenarios("features/cancelApplication.feature")


@pytest.fixture
def client():
    return TestClient(app)


class Context:

    def __init__(self):
        self.response = None
        self.application_id = "J000001"  # existing application id


@pytest.fixture
def context():
    return Context()


# --------------------------------------------------
# Scenario 1
# Job seeker withdraws a submitted application
# --------------------------------------------------


@given("the job seeker has submitted a job application")
def submitted_application():
    pass


@when("the job seeker selects the withdraw application option")
def withdraw_application(client, context):

    context.response = client.post(f"/application/{context.application_id}/cancel")


@then('the application status should be updated to "Cancelled"')
def verify_cancelled(context):

    assert context.response.status_code == 200

    assert "Cancelled" in context.response.text

    print("✅ SUCCESS: Application status updated to Cancelled")


# --------------------------------------------------
# Scenario 2
# Save withdrawn application status
# --------------------------------------------------


@given("the job seeker has withdrawn an application")
def withdrawn_application(client, context):

    client.post(f"/application/{context.application_id}/cancel")


@when("the withdrawal request is processed")
def process_request(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the updated application status should be saved in the database")
def verify_database(context):

    assert context.response.status_code == 200

    data = context.response.text

    assert "Cancelled" in data

    print("✅ SUCCESS: Updated application status saved in database")
