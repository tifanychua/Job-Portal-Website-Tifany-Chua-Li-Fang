"""Acceptance tests for the "Personal information privacy" story.

Exercises:
- GET /api/applications/{application_id} (job_portal_web.backend.applicant),
  which now checks that the requesting employer's session company_id
  matches the job's company_id before returning applicant personal data.
- GET /privacy-settings (job_portal_web.backend.privacy), a new page that
  lists every employer who has received an application from the current
  job seeker (i.e. every employer allowed to see their personal info).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from fakes import FakeFirestore, patch_db_everywhere
from job_portal_web.backend import notifications
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
APPLIED_COMPANY_ID = "COMP_APPLIED"
OTHER_COMPANY_ID = "COMP_STRANGER"

scenarios("features/personalInfoPrivacy.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", APPLIED_COMPANY_ID, {"companyName": "Applied Co"})
    db.seed("company", OTHER_COMPANY_ID, {"companyName": "Stranger Co"})
    db.seed(
        "job_seeker",
        JOB_SEEKER_ID,
        {
            "name": "Jamie Lee",
            "email": "jamie@example.com",
            "phone": "+60123456789",
            "skill": [],
        },
    )
    return db


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_job(fake_db, job_id, company_id, *, title="Software Engineer"):
    fake_db.seed("job_list", job_id, {"job_title": title, "company_id": company_id})


def seed_application(fake_db, app_id, job_id):
    fake_db.seed(
        "application",
        app_id,
        {"job_id": job_id, "job_seeker_id": JOB_SEEKER_ID, "status": "Submitted"},
    )


def login_as_company(client, monkeypatch, company_id):
    """Establish a real employer session on the shared TestClient.

    applicant.py / privacy.py read request.session directly (there's no
    single mockable "current user" getter shared across the app), so the
    session cookie needs to actually carry user_type=employer before the
    request under test. Priming it via notifications._get_current_user --
    which every page calls for the unread-count badge -- sets that cookie
    for every subsequent request on this client.
    """

    def fake_current_user(request):
        request.session["user_type"] = "employer"
        request.session["company_id"] = company_id
        return company_id, "employer", {"uid": company_id}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)
    client.post("/api/notifications/mark-all-read")


def login_as_job_seeker(client, monkeypatch, job_seeker_id):
    def fake_current_user(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = job_seeker_id
        return job_seeker_id, "job_seeker", {"uid": job_seeker_id}

    monkeypatch.setattr(notifications, "_get_current_user", fake_current_user)
    client.post("/api/notifications/mark-all-read")


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.application_id = None
        self.response = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: Employer accesses applicant personal information after application
# ==================================================


@given("the job seeker has submitted an application to an employer")
def given_applied_to_employer(fake_db, context):
    job_id = "JOB_APPLIED_TO"
    context.application_id = "APP_ALLOWED"
    seed_job(fake_db, job_id, APPLIED_COMPANY_ID)
    seed_application(fake_db, context.application_id, job_id)


@when("the employer views the applicant's profile")
def employer_views_applicant_profile(client, monkeypatch, context):
    login_as_company(client, monkeypatch, APPLIED_COMPANY_ID)
    context.response = client.get(f"/api/applications/{context.application_id}")


@then("the system should allow the employer to access the job seeker's personal information")
def assert_access_allowed(context):
    assert context.response.status_code == 200
    body = context.response.json()
    assert body["name"] == "Jamie Lee"
    assert body["email"] == "jamie@example.com"


# ==================================================
# Scenario: Unauthorized employer attempts to access personal information
# ==================================================


@given("the job seeker has not applied to the employer")
def given_not_applied_to_employer(fake_db, context):
    job_id = "JOB_NOT_APPLIED_TO"
    context.application_id = "APP_UNRELATED"
    # This application belongs to a *different* employer (APPLIED_COMPANY_ID);
    # OTHER_COMPANY_ID never received an application from this job seeker.
    seed_job(fake_db, job_id, APPLIED_COMPANY_ID)
    seed_application(fake_db, context.application_id, job_id)


@when("the employer attempts to view the job seeker's personal information")
def unauthorized_employer_attempts_view(client, monkeypatch, context):
    login_as_company(client, monkeypatch, OTHER_COMPANY_ID)
    context.response = client.get(f"/api/applications/{context.application_id}")


@then("the system should deny access and prevent the employer from viewing the information")
def assert_access_denied(context):
    assert context.response.status_code in (401, 403, 404)
    assert "email" not in context.response.json()


# ==================================================
# Scenario: Job seeker controls personal information visibility
# ==================================================


@given("the job seeker has submitted applications to multiple employers")
def given_applications_to_multiple_employers(fake_db, context):
    seed_job(fake_db, "JOB_MULTI_1", APPLIED_COMPANY_ID)
    seed_job(fake_db, "JOB_MULTI_2", OTHER_COMPANY_ID)
    seed_application(fake_db, "APP_MULTI_1", "JOB_MULTI_1")
    seed_application(fake_db, "APP_MULTI_2", "JOB_MULTI_2")


@when("the job seeker views their privacy settings")
def job_seeker_views_privacy_settings(client, monkeypatch, context):
    login_as_job_seeker(client, monkeypatch, JOB_SEEKER_ID)
    context.response = client.get("/privacy-settings")


@then("the system should display the employers who are allowed to access their personal information")
def assert_privacy_settings_shown(context):
    assert context.response.status_code == 200
    assert "Applied Co" in context.response.text
    assert "Stranger Co" in context.response.text
