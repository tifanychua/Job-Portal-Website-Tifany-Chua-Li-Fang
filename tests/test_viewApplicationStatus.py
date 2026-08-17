from __future__ import annotations

import pytest
from fakes import FakeFirestore, patch_db_everywhere
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import job_application
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
APPLICATION_ID = "5iVgjmXsCDG4lpM5uUuj"


# --------------------------------------------------
# Fake Firestore
# --------------------------------------------------


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()

    patch_db_everywhere(monkeypatch, db)

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
            "job_title": "Software Engineer",
            "title": "Software Engineer",
            "company_id": "COMP001",
            "companyId": "COMP001",
            "status": "Active",
        },
    )

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
            "status": "Shortlisted",
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
# Test Client
# --------------------------------------------------


@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------
# Acceptance Test 1
# --------------------------------------------------


def test_view_application_status_list(client: TestClient):

    response = client.get("/application")

    assert response.status_code == 200

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in response.text for status in statuses)


# --------------------------------------------------
# Acceptance Test 2
# --------------------------------------------------


def test_view_updated_application_status(client: TestClient):

    response = client.get(f"/application/{APPLICATION_ID}")

    assert response.status_code == 200

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in response.text for status in statuses)


# --------------------------------------------------
# BDD Feature
# --------------------------------------------------

scenarios("features/viewApplicationStatus.feature")


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

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in context.response.text for status in statuses)


# --------------------------------------------------
# Scenario 2
# --------------------------------------------------


@given("an employer has updated an application status")
def updated_status():
    pass


@when("the job seeker views the application details")
def open_application_detail(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the updated application status should be displayed")
def verify_updated_status(context):

    assert context.response.status_code == 200

    statuses = [
        "Submitted",
        "Cancelled",
        "Shortlisted",
        "Rejected",
        "Offered",
    ]

    assert any(status in context.response.text for status in statuses)
