from __future__ import annotations

import pytest
from fakes import FakeFirestore, patch_db_everywhere
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import job_application
from job_portal_web.backend.main import app

APPLICATION_ID = "5iVgjmXsCDG4lpM5uUuj"
JOB_SEEKER_ID = "J000001"


# --------------------------------------------------
# Fake Firestore
# --------------------------------------------------


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)

    db.seed(
        "application",
        APPLICATION_ID,
        {
            "job_seeker_id": JOB_SEEKER_ID,
            "jobSeekerId": JOB_SEEKER_ID,
            "applicant_id": JOB_SEEKER_ID,
            "job_id": "JOB001",
            "jobId": "JOB001",
            "company_id": "COMP001",
            "companyId": "COMP001",
            "status": "Submitted",
        },
    )

    db.seed(
        "job_seeker",
        JOB_SEEKER_ID,
        {
            "name": "Test User",
            "full_name": "Test User",
            "email": "test@example.com",
            "headline": "Software Engineer",
            "photo": "user.png",
        },
    )

    db.seed(
        "company",
        "COMP001",
        {
            "companyName": "ABC Technology",
            "name": "ABC Technology",
            "address": "Penang",
        },
    )

    db.seed(
        "job_list",
        "JOB001",
        {
            "title": "Software Engineer",
            "job_title": "Software Engineer",
            "company_id": "COMP001",
            "companyId": "COMP001",
            "status": "Active",
        },
    )

    return db


# --------------------------------------------------
# Fake Login
# --------------------------------------------------


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):

    def fake_current_user(request):

        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID

        return (
            JOB_SEEKER_ID,
            {
                "uid": JOB_SEEKER_ID,
                "full_name": "Test User",
                "headline": "Software Engineer",
                "photo": "user.png",
            },
        )

    monkeypatch.setattr(
        job_application,
        "_get_currentjob_seeker",
        fake_current_user,
    )


# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_list(client: TestClient):

    response = client.get("/application")

    assert response.status_code == 200

    print("✅ SUCCESS: Submitted application list displayed")


# --------------------------------------------------
# 2. Acceptance Test
# --------------------------------------------------


def test_view_submitted_application_details(client: TestClient):

    response = client.get(f"/application/{APPLICATION_ID}")

    assert response.status_code == 200

    data = response.text.lower()

    required_fields = ["application", "status"]

    missing = []

    for field in required_fields:
        if field not in data:
            missing.append(field)

    assert len(missing) == 0

    print("✅ SUCCESS: Application details and status displayed")


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

    assert len(missing) == 0

    print("✅ SUCCESS: Application details and status displayed")
