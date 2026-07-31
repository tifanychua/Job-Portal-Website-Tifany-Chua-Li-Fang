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


APPLICATION_ID = "5iVgjmXsCDG4lpM5uUuj"


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_list(client: TestClient):

    response = client.get("/application")

    if response.status_code == 200:

        print("✅ SUCCESS: Submitted application list displayed")

    else:

        print("❌ FAILED:", response.status_code, response.text)

    assert response.status_code == 200


# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_details(client: TestClient):

    response = client.get(f"/application/{APPLICATION_ID}")

    if response.status_code == 200:

        data = response.text.lower()

        required_fields = ["application", "status"]

        missing = []

        for field in required_fields:

            if field not in data:
                missing.append(field)

        if not missing:

            print("✅ SUCCESS: Application details and status displayed")

        else:

            print(f"❌ FAILED: Missing {missing}")

        assert len(missing) == 0

    else:

        print("❌ FAILED:", response.status_code, response.text)

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
        self.application_id = APPLICATION_ID


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario
# --------------------------------------------------


@given("the job seeker is viewing submitted applications")
def viewing_applications(client, context):

    context.response = client.get("/application")

    assert context.response.status_code == 200


@when("the job seeker selects an application")
def select_application(client, context):

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
