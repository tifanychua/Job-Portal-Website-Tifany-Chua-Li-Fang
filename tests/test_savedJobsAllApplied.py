"""Acceptance + unit tests for the "Saved jobs: All / Applied sections" story.

The All/Applied tabs on savedJob.html are filtered client-side based on the
`data-applied="true|false"` attribute the server renders on each
`.saved-card` (see savedJob.py: job["is_applied"]). These tests exercise the
real GET /saved-jobs route against an in-memory fake Firestore and assert on
that server-rendered data contract.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

import pytest
from fakes import FakeFirestore, patch_db_everywhere
from fastapi.testclient import TestClient
from html_helpers import item_block
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend import saved_job
from job_portal_web.backend.main import app

JOB_SEEKER_ID = "J000001"
OTHER_JOB_SEEKER_ID = "J000002"
COMPANY_ID = "COMP001"

scenarios("features/savedJobsAllApplied.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    db = FakeFirestore()
    patch_db_everywhere(monkeypatch, db)
    db.seed("company", COMPANY_ID, {"companyName": "TARUMT Sdn Bhd", "verified": True})
    return db


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):
    def fake_job_seeker_id(request):
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = JOB_SEEKER_ID
        return JOB_SEEKER_ID

    monkeypatch.setattr(saved_job, "_get_current_job_seeker_id", fake_job_seeker_id)


@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Helpers
# ==================================================


def seed_job(fake_db, job_id, *, title="Software Engineer"):
    fake_db.seed(
        "job_list",
        job_id,
        {
            "job_title": title,
            "company_id": COMPANY_ID,
            "location": "Kuala Lumpur",
            "employment_type": "Full-time",
            "status": "Active",
        },
    )


def seed_saved(fake_db, job_id, *, seeker=JOB_SEEKER_ID, days_ago=0):
    fake_db.seed(
        "saved_job",
        f"{seeker}_{job_id}",
        {
            "job_seeker_id": seeker,
            "job_id": job_id,
            "saved_at": datetime.now(UTC) - timedelta(days=days_ago),
        },
    )


def seed_application(fake_db, job_id, *, seeker=JOB_SEEKER_ID, status="Submitted"):
    fake_db.seed(
        "application",
        f"APP_{seeker}_{job_id}",
        {
            "job_seeker_id": seeker,
            "job_id": job_id,
            "status": status,
        },
    )


def saved_card(page_html: str, job_id: str) -> str:
    return item_block(page_html, job_id, item_class="saved-card")


def tab_counts(page_html: str):
    all_match = re.search(r"All Saved\s*<span class=\"tab-count\">\((\d+)\)", page_html)
    applied_match = re.search(r">\s*Applied\s*<span class=\"tab-count\">\((\d+)\)", page_html)
    assert all_match and applied_match, "saved-job tab counts not found in page"
    return int(all_match.group(1)), int(applied_match.group(1))


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.applied_job_id = None
        self.not_applied_job_id = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Scenario: View all saved jobs
# ==================================================


@given("the job seeker has saved both applied and not-applied jobs")
def given_applied_and_not_applied(fake_db, context):
    context.applied_job_id = "JOB_APPLIED"
    context.not_applied_job_id = "JOB_NOT_APPLIED"

    seed_job(fake_db, context.applied_job_id, title="Backend Engineer")
    seed_job(fake_db, context.not_applied_job_id, title="Frontend Engineer")

    seed_saved(fake_db, context.applied_job_id)
    seed_saved(fake_db, context.not_applied_job_id)

    seed_application(fake_db, context.applied_job_id)


@when("the job seeker opens the All section")
def open_all_section(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display all jobs saved by the job seeker")
def assert_all_jobs_displayed(context):
    assert context.response.status_code == 200
    page = context.response.text
    assert f'data-id="{context.applied_job_id}"' in page
    assert f'data-id="{context.not_applied_job_id}"' in page


# ==================================================
# Scenario: View applied saved jobs
# ==================================================


@given("the job seeker has saved jobs with different application statuses")
def given_mixed_statuses(fake_db, context):
    given_applied_and_not_applied(fake_db, context)


@when("the job seeker opens the Applied section")
def open_applied_section(client, context):
    # Applied is a client-side filter over the same server response.
    context.response = client.get("/saved-jobs")


@then("the system should display only saved jobs that the job seeker has applied for")
def assert_only_applied_flagged(context):
    page = context.response.text
    assert saved_card(page, context.applied_job_id).count('data-applied="true"') == 1
    assert saved_card(page, context.not_applied_job_id).count('data-applied="false"') == 1


# ==================================================
# Scenario: Exclude not-applied jobs from Applied section
# ==================================================


@given("the job seeker has saved a job but has not applied for it")
def given_not_applied_job(fake_db, context):
    context.not_applied_job_id = "JOB_ONLY_SAVED"
    seed_job(fake_db, context.not_applied_job_id)
    seed_saved(fake_db, context.not_applied_job_id)


@then("the saved job should not appear in the Applied section")
def assert_not_in_applied(context):
    page = context.response.text
    assert saved_card(page, context.not_applied_job_id).count('data-applied="false"') == 1


@then("it should remain available in the All section")
def assert_remains_in_all(context):
    page = context.response.text
    assert f'data-id="{context.not_applied_job_id}"' in page


# ==================================================
# Scenario: Display application status
# ==================================================


@given("the job seeker has applied for a saved job")
def given_applied_saved_job(fake_db, context):
    context.applied_job_id = "JOB_WITH_BADGE"
    seed_job(fake_db, context.applied_job_id)
    seed_saved(fake_db, context.applied_job_id)
    seed_application(fake_db, context.applied_job_id)


@when("the job seeker views the saved-job list")
def view_saved_job_list(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display a clear applied-status indicator for that job")
def assert_applied_badge(context):
    card = saved_card(context.response.text, context.applied_job_id)
    assert 'data-applied="true"' in card
    assert 'badge-info">Applied' in card


# ==================================================
# Scenario: Update Applied section after application submission
# ==================================================


@given("the job seeker has saved a job")
def given_saved_job(fake_db, context):
    context.job_id = "JOB_TO_APPLY"
    seed_job(fake_db, context.job_id)
    seed_saved(fake_db, context.job_id)


@given("the job has not been applied for")
def given_not_yet_applied(context):
    context.response = None  # nothing to assert yet


@when("the job seeker successfully submits an application for the job")
def submit_application(fake_db, context):
    seed_application(fake_db, context.job_id)
    context.response = None


@then("the saved job should appear in the Applied section")
def assert_now_in_applied(client, context):
    page = client.get("/saved-jobs").text
    assert saved_card(page, context.job_id).count('data-applied="true"') == 1
    context.response = client.get("/saved-jobs")


@then("the job should display an applied-status indicator")
def assert_now_has_badge(context):
    card = saved_card(context.response.text, context.job_id)
    assert 'badge-info">Applied' in card


# ==================================================
# Scenario: Switch between All and Applied sections
# ==================================================


@given("the job seeker is viewing the saved-jobs page")
def viewing_saved_jobs_page(fake_db, client, context):
    context.applied_job_id = "JOB_SWITCH_APPLIED"
    context.not_applied_job_id = "JOB_SWITCH_NOT_APPLIED"
    seed_job(fake_db, context.applied_job_id)
    seed_job(fake_db, context.not_applied_job_id)
    seed_saved(fake_db, context.applied_job_id)
    seed_saved(fake_db, context.not_applied_job_id)
    seed_application(fake_db, context.applied_job_id)
    context.response = client.get("/saved-jobs")


@when("the job seeker switches between the All and Applied sections")
def switch_tabs(context):
    # Both tabs read from the same already-fetched server response;
    # switching is purely a client-side re-render.
    pass


@then("the system should update the displayed saved-job list correctly")
def assert_tab_data_correct(context):
    all_count, applied_count = tab_counts(context.response.text)
    assert all_count == 2
    assert applied_count == 1


@then("clearly highlight the selected section")
def assert_active_tab_markup(context):
    page = context.response.text
    assert 'class="saved-tab active" data-filter="all"' in page
    assert 'data-filter="applied" onclick="setSavedTab(\'applied\', this)"' in page


# ==================================================
# Scenario: Remove a job from the saved list
# ==================================================


@given("the job seeker has a saved job displayed in the All or Applied section")
def given_removable_saved_job(fake_db, context):
    context.job_id = "JOB_TO_REMOVE"
    seed_job(fake_db, context.job_id)
    seed_saved(fake_db, context.job_id)


@when("the job seeker removes the job from the saved list")
def remove_saved_job(client, context):
    context.response = client.delete(f"/api/saved-jobs/{context.job_id}")
    assert context.response.status_code == 200


@then("the job should be removed from both the All and Applied sections")
def assert_removed_from_both(client, context):
    page = client.get("/saved-jobs").text
    assert f'data-id="{context.job_id}"' not in page


# ==================================================
# Scenario: No applied saved jobs available
# ==================================================


@given("the job seeker has saved jobs but has not applied for any of them")
def given_none_applied(fake_db, context):
    context.not_applied_job_id = "JOB_NONE_APPLIED"
    seed_job(fake_db, context.not_applied_job_id)
    seed_saved(fake_db, context.not_applied_job_id)


@then("the system should display a message indicating that there are no applied saved jobs")
def assert_no_applied_message(context):
    page = context.response.text
    _, applied_count = tab_counts(page)
    assert applied_count == 0
    # The "no results for this tab" empty state is rendered (hidden until
    # the Applied tab is selected client-side, but present in the DOM).
    assert 'id="savedNoResults"' in page
    assert "No matching saved jobs" in page


# ==================================================
# Scenario: No saved jobs available
# ==================================================


@given("the job seeker has not saved any jobs")
def given_no_saved_jobs(context):
    pass


@when("the job seeker opens the saved-jobs page")
def open_saved_jobs_page(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should display an appropriate empty-state message")
def assert_empty_state(context):
    page = context.response.text
    all_count, applied_count = tab_counts(page)
    assert all_count == 0
    assert applied_count == 0
    # savedEmpty is only hidden (display:none) when there ARE saved jobs.
    assert 'id="savedEmpty"' in page
    assert '<div class="saved-empty" id="savedEmpty" style="display:none">' not in page
    assert "No saved jobs yet" in page


# ==================================================
# Scenario: Prevent access to another job seeker's saved jobs
# ==================================================


@given("saved jobs belong to another job seeker")
def given_other_seekers_saved_jobs(fake_db, context):
    context.other_job_id = "JOB_OTHER_SEEKER"
    seed_job(fake_db, context.other_job_id)
    seed_saved(fake_db, context.other_job_id, seeker=OTHER_JOB_SEEKER_ID)


@when("the current job seeker views the saved-jobs page")
def current_seeker_views_page(client, context):
    context.response = client.get("/saved-jobs")


@then("the system should not display the other job seeker's saved jobs or application information")
def assert_other_jobs_hidden(context):
    page = context.response.text
    assert f'data-id="{context.other_job_id}"' not in page
    all_count, _ = tab_counts(page)
    assert all_count == 0
