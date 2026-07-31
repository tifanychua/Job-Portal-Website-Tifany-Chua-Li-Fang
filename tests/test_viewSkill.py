from uuid import uuid4
from datetime import datetime

import pytest

from fastapi.testclient import TestClient
from pytest_bdd import (
    scenarios,
    given,
    when,
    then,
)

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)

scenarios("features/viewSkill.feature")


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def context():
    return {}


@pytest.fixture
def applicant_id():
    return "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ==========================================================
# Helper Functions
# ==========================================================


def create_skill(industry_id="IND001", category_id="CAT001", skill_id=None, level="Intermediate"):

    if skill_id is None:
        skill_id = f"SKILL-{uuid4()}"

    doc = db.collection("job_seeker_skill").document()

    doc.set(
        {
            "applicant_id": "0YLcc18JszVqSXWn8DEDQ81o2vR2",
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    return doc.id


def delete_skill(document_id):

    doc_ref = db.collection("job_seeker_skill").document(document_id)

    if doc_ref.get().exists:
        doc_ref.delete()


# ==========================================================
# GIVEN
# ==========================================================


@given("the job seeker is logged in")
def job_seeker_logged_in():
    pass


@given("the job seeker has added one or more skills to the profile")
def existing_skills(context):

    context["document1"] = create_skill(skill_id="SKILL001")

    context["document2"] = create_skill(skill_id="SKILL002")


@given("the job seeker has modified their skills")
def modified_skills(context):

    context["document_id"] = create_skill(skill_id="UPDATED_SKILL", level="Advanced")


@given("the job seeker has not added any skills to the profile")
def no_skills():

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", "0YLcc18JszVqSXWn8DEDQ81o2vR2")
        .stream()
    )

    for doc in docs:
        doc.reference.delete()


@given("the job seeker is viewing their profile")
def viewing_profile(context):

    context["document_id"] = create_skill(skill_id="PROFILE_SKILL", level="Intermediate")


# ==========================================================
# WHEN
# ==========================================================


@when("the job seeker opens the Skills section")
def open_skills(context):

    context["response"] = client.get("/manageSkills")


@when("the job seeker views the Skills section")
def view_skills(context):

    context["response"] = client.get("/manageSkills")


@when("the profile information is loaded")
def load_profile(context):

    context["response"] = client.get("/profile")


# ==========================================================
# THEN
# ==========================================================


@then("the system should display all skills listed in the job seeker's profile")
def display_all_skills(context):

    assert context["response"].status_code == 200

    response_text = context["response"].text

    assert "SKILL001" in response_text
    assert "SKILL002" in response_text

    delete_skill(context["document1"])
    delete_skill(context["document2"])


@then("the system should display the latest saved skills information")
def display_updated_skill(context):

    assert context["response"].status_code == 200

    response_text = context["response"].text

    assert "UPDATED_SKILL" in response_text

    delete_skill(context["document_id"])


@then('the system should display a "No skills have been added yet" message')
def no_skill_message(context):

    assert context["response"].status_code == 200

    response_text = context["response"].text

    assert "No skills have been added yet" in response_text or "No Skills" in response_text


@then("the system should display the listed skills as part of the profile details")
def profile_display(context):

    assert context["response"].status_code == 200

    response_text = context["response"].text

    assert "PROFILE_SKILL" in response_text

    delete_skill(context["document_id"])
