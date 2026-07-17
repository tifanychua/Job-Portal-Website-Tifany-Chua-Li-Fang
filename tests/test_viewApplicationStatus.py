from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from main import app


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


def test_view_application_status_list(client: TestClient):
    """
    Acceptance test: Job seeker views application statuses

    Given the job seeker has submitted job applications
    When the job seeker opens the application status page
    Then the system should display the current status of each application
    """

    response = client.get("/application")


    if response.status_code == 200:

        page = response.text

        statuses = [
            "Submitted",
            "Cancelled",
            "Shortlisted",
            "Rejected",
            "Offered"
        ]

        if any(status in page for status in statuses):

            print(
                "✅ SUCCESS: Job seeker views application statuses"
            )

        else:

            print(
                "❌ FAILED: Application statuses not found"
            )

    else:

        print(
            "❌ FAILED: Unable to open application status page"
        )


    assert response.status_code == 200

    assert any(
        status in response.text
        for status in statuses
    )



# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_view_updated_application_status(client: TestClient):
    """
    Acceptance test: Job seeker views updated application status

    Given an employer has updated an application status
    When the job seeker views application details
    Then the updated application status should be displayed
    """


    application_id = "J000001"


    response = client.get(
        f"/application/{application_id}"
    )


    if response.status_code == 200:

        page = response.text

        statuses = [
            "Shortlisted",
            "Rejected",
            "Offered",
            "Cancelled",
            "Submitted"
        ]


        if any(status in page for status in statuses):

            print(
                "✅ SUCCESS: Job seeker views updated application status"
            )

        else:

            print(
                "❌ FAILED: Updated status not found"
            )

    else:

        print(
            "❌ FAILED: Unable to retrieve application details"
        )


    assert response.status_code == 200

    assert any(
        status in response.text
        for status in statuses
    )



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
        self.application_id = "J000001"



@pytest.fixture
def context():

    return Context()



# --------------------------------------------------
# Scenario 1:
# View Application Status
# --------------------------------------------------


@given("the job seeker has submitted job applications")
def submitted_applications():

    pass



@when("the job seeker opens the application status page")
def open_status_page(client, context):

    context.response = client.get(
        "/application"
    )



@then("the system should display the current status of each application")
def verify_status_list(context):

    assert context.response.status_code == 200


    page = context.response.text


    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered"
    ]


    assert any(
        status in page
        for status in statuses
    )


    print(
        "✅ SUCCESS: Application statuses displayed"
    )



# --------------------------------------------------
# Scenario 2:
# View Updated Application Status
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
        "Shortlisted",
        "Rejected",
        "Offered",
        "Cancelled",
        "Submitted"
    ]


    assert any(
        status in page
        for status in statuses
    )


    print(
        "✅ SUCCESS: Updated application status displayed"
    )