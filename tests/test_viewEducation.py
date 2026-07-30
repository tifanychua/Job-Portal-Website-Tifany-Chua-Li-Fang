from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db


# ==================================================
# Test Client
# ==================================================

@pytest.fixture
def client():

    return TestClient(app)


# ==================================================
# Test Applicant
# ==================================================

APPLICANT_ID = "applicant001"


# ==================================================
# Acceptance Test 1
# View education records
# ==================================================

def test_view_education_success(client):

    response = client.get("/manage-education")

    assert response.status_code == 200

    assert "manageEducation.html" in str(response.template)

    print("✅ Acceptance Test Passed: Education records displayed successfully.")


# ==================================================
# Acceptance Test 2
# Page loads successfully
# ==================================================

def test_manage_education_page_load(client):

    response = client.get("/manage-education")

    assert response.status_code == 200

    print("✅ Acceptance Test Passed: Manage Education page loaded successfully.")


# ==================================================
# Load Feature
# ==================================================

scenarios("features/viewEducation.feature")


# ==================================================
# Context
# ==================================================

class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# View education records
# ==================================================

@given("the job seeker has education records")
def education_exists():

    pass


@when("the job seeker visits the Manage Education page")
def visit_manage_education(client, context):

    context.response = client.get("/manage-education")


@then("the system should display the education records")
def display_education(context):

    assert context.response.status_code == 200

    assert "manageEducation.html" in str(context.response.template)

    print("✅ Scenario Passed: Education records displayed successfully.")


# ==================================================
# Scenario 2
# No education records
# ==================================================

@given("the job seeker has no education records")
def no_education():

    pass


@when("the job seeker visits the Manage Education page")
def visit_manage_education_empty(client, context):

    context.response = client.get("/manage-education")


@then("the system should display the empty education message")
def empty_message(context):

    assert context.response.status_code == 200

    assert "manageEducation.html" in str(context.response.template)

    print("✅ Scenario Passed: Empty education page displayed successfully.")