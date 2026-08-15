from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.main import app

# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewAboutUs.feature")


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class Context:
    def __init__(self):
        self.response = None
        self.jobs_link_found = False


@pytest.fixture
def context():
    return Context()


# ==================================================
# Helpers
# ==================================================


def open_about_us_page(client: TestClient, context: Context):
    context.response = client.get(
        "/about-us",
        follow_redirects=False,
    )


def page_text(context: Context) -> str:
    assert context.response is not None
    return context.response.text.lower()


def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase.lower() in text for phrase in phrases)


# ==================================================
# Scenario 1: Access About Us
# ==================================================


@given("the job seeker is viewing the website")
def viewing_website(context):
    context.response = None


@when("the job seeker opens the About Us page")
def open_about_us(client, context):
    open_about_us_page(client, context)


@then("the About Us page should be displayed")
def verify_about_us_page(context):
    assert context.response is not None
    assert context.response.status_code == 200
    assert "about" in page_text(context)


# ==================================================
# Scenario 2: Platform Information
# ==================================================


@given("the job seeker is viewing the About Us page")
def viewing_about_us(client, context):
    open_about_us_page(client, context)
    assert context.response.status_code == 200


@when("the About Us content is loaded")
def about_us_content_loaded(context):
    assert context.response is not None


@then("an introduction to the platform should be displayed")
def verify_platform_introduction(context):
    text = page_text(context)
    assert contains_any(
        text,
        (
            "about us",
            "who we are",
            "about the platform",
            "our story",
        ),
    )


@then("information about how the platform supports job seekers should be displayed")
def verify_job_seeker_support(context):
    text = page_text(context)
    assert contains_any(
        text,
        (
            "job seeker",
            "career",
            "job opportunities",
            "find jobs",
            "find the right job",
        ),
    )


# ==================================================
# Scenario 3: Mission and Values
# ==================================================


@when("the job seeker views the mission and values section")
def view_mission_and_values(context):
    assert context.response is not None


@then("the platform mission should be displayed")
def verify_mission(context):
    assert "mission" in page_text(context)


@then("the platform core values should be displayed")
def verify_core_values(context):
    text = page_text(context)
    assert contains_any(text, ("core values", "our values", "values"))


# ==================================================
# Scenario 4: Job Seeker Services
# ==================================================


@when("the job seeker views the services section")
def view_services(context):
    assert context.response is not None


@then("services available to job seekers should be displayed")
def verify_job_seeker_services(context):
    text = page_text(context)

    assert contains_any(
        text,
        (
            "services",
            "what we offer",
            "what we provide",
            "how we help",
            "for job seekers",
        ),
    )


@then("the services should include finding jobs and connecting with employers")
def verify_service_information(context):
    text = page_text(context)

    has_job_service = contains_any(
        text,
        (
            "find jobs",
            "find a job",
            "job opportunities",
            "explore jobs",
            "browse jobs",
        ),
    )
    has_employer_connection = contains_any(
        text,
        (
            "employer",
            "company",
            "companies",
            "connect",
        ),
    )

    assert has_job_service
    assert has_employer_connection


# ==================================================
# Scenario 5: Explore Jobs
# ==================================================


@when("the job seeker selects the Explore Jobs option")
def select_explore_jobs(context):
    html = context.response.text
    context.jobs_link_found = bool(
        re.search(
            r'href=["\'](?:https?://[^"\']+)?/jobs(?:\?[^"\']*)?["\']',
            html,
            flags=re.IGNORECASE,
        )
    )


@then("the job seeker should be directed to the available jobs page")
def verify_jobs_navigation(context):
    assert context.jobs_link_found


# ==================================================
# Scenario 6: Guest Access
# ==================================================


@given("the job seeker is not logged in")
def job_seeker_not_logged_in(client, context):
    client.cookies.clear()
    context.response = None


@when("the job seeker opens the About Us page as a guest")
def open_about_us_as_guest(client, context):
    open_about_us_page(client, context)


@then("the About Us page should be displayed without requiring authentication")
def verify_guest_access(context):
    assert context.response is not None
    assert context.response.status_code == 200
    assert "login" not in context.response.headers.get("location", "").lower()
    assert "about" in page_text(context)
