from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------
# Acceptance Tests
# --------------------------------------------------


def test_cancel_application_success(client):
    """
    Acceptance test:
    Job seeker withdraws a submitted application
    """

    response = client.post("/application/J000001/cancel")

    if response.status_code == 200:
        print("✅ SUCCESS: Application withdrawn successfully")
    else:
        print("❌ FAILED: Unable to withdraw application")

    assert response.status_code == 200


def test_cancel_application_saved(client):
    """
    Acceptance test:
    Withdrawn application status is saved
    """

    client.post("/application/J000001/cancel")

    response = client.get("/application/J000001")

    if response.status_code == 200 and "Cancelled" in response.text:
        print("✅ SUCCESS: Withdrawal saved in database")
    else:
        print("❌ FAILED: Withdrawal not saved")

    assert response.status_code == 200
    assert "Cancelled" in response.text


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/cancelApplication.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None
        self.application_id = "J000001"


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

    assert "Cancelled" in context.response.text

    print("✅ SUCCESS: Updated application status saved in database")
