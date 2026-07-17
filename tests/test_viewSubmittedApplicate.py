from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest
import re

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client():
    """
    Shared FastAPI test client.
    """
    return TestClient(app)


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_list(client: TestClient):
    """
    Acceptance test: Job seeker views submitted applications

    Given the job seeker has submitted applications
    When the job seeker opens the application page
    Then the system should display submitted applications
    """

    response = client.get("/application")

    if response.status_code == 200:

        print("✅ SUCCESS: Submitted application list displayed")

    else:

        print("❌ FAILED: Unable to display submitted applications")

    assert response.status_code == 200


# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_details(client: TestClient):
    """
    Acceptance test: Job seeker views application details

    Given the job seeker has submitted applications
    When the job seeker selects an application
    Then the system should display application details and status
    """

    response = client.get("/application")

    assert response.status_code == 200

    html = response.text

    ids = re.findall(r"/application/([a-zA-Z0-9_-]+)", html)

    if not ids:

        print("❌ FAILED: No application found")

        pytest.fail("No application available for testing")

    application_id = ids[0]

    response = client.get(f"/application/{application_id}")

    if response.status_code == 200:

        data = response.text.lower()

        required_fields = ["application", "status"]

        missing = []

        for field in required_fields:

            if field not in data:

                missing.append(field)

        if len(missing) == 0:

            print("✅ SUCCESS: Application details and status displayed")

        else:

            print(f"❌ FAILED: Missing {missing}")

        assert len(missing) == 0

    else:

        print("❌ FAILED: Unable to open application details")

    assert response.status_code == 200


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/viewSubmittedApplicate.feature")


# --------------------------------------------------
# Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None
        self.application_id = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario:
# Job seeker views application details
# --------------------------------------------------


@given("the job seeker is viewing submitted applications")
def viewing_applications(client, context):

    context.response = client.get("/application")

    assert context.response.status_code == 200


@when("the job seeker selects an application")
def select_application(client, context):

    html = context.response.text

    ids = re.findall(r"/application/([a-zA-Z0-9_-]+)", html)

    if not ids:

        print("❌ FAILED: No application id found")

        pytest.fail("No application available for testing")

    context.application_id = ids[0]

    context.response = client.get(f"/application/{context.application_id}")


@then("the system should display the application details and status")
def verify_application_details(context):

    assert context.response.status_code == 200

    data = context.response.text.lower()

    required_fields = ["application", "status"]

    missing = []

    for field in required_fields:

        if field not in data:

            missing.append(field)

    if missing:

        print(f"❌ FAILED: Missing {missing}")

    else:

        print("✅ SUCCESS: Application details and status displayed")

    assert len(missing) == 0
