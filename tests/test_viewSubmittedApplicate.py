from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest
import re

from main import app

scenarios("features/viewSubmittedApplicate.feature")


@pytest.fixture
def client():
    return TestClient(app)


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

    print("APPLICATION PAGE STATUS:", context.response.status_code)

    assert context.response.status_code == 200


@when("the job seeker selects an application")
def select_application(client, context):

    html = context.response.text

    # Find application id from generated links
    ids = re.findall(r"/application/([a-zA-Z0-9_-]+)", html)

    if not ids:

        print("❌ FAILED: No application id found")

        pytest.fail("No application available for testing")

    context.application_id = ids[0]

    print("TEST APPLICATION ID:", context.application_id)

    context.response = client.get(f"/application/{context.application_id}")


@then("the system should display the application details and status")
def verify_application_details(context):

    print("DETAIL PAGE STATUS:", context.response.status_code)

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
