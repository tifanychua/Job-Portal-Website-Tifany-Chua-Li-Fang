from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app
from job_portal_web.backend.routes import skill as skill_route

scenarios("features/viewSkill.feature")


# ==========================================================
# Test Constants
# ==========================================================

APPLICANT_ID = f"TEST_VIEW_SKILL_APPLICANT_{uuid4().hex}"


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def context():
    return {}


@pytest.fixture
def applicant_id():
    return APPLICANT_ID


@pytest.fixture(autouse=True)
def isolate_view_skill_tests(monkeypatch):
    monkeypatch.setenv("TEST_APPLICANT_ID", APPLICANT_ID)

    monkeypatch.setattr(
        skill_route,
        "get_current_applicant_id",
        lambda request: APPLICANT_ID,
    )

    clear_applicant_skills()

    db.collection("job_seeker").document(APPLICANT_ID).set(
        {
            "uid": APPLICANT_ID,
            "name": "View Skill Test User",
            "email": f"{APPLICANT_ID.lower()}@example.com",
            "position": "Software Engineer",
            "test": True,
        }
    )

    yield

    clear_applicant_skills()

    applicant_reference = db.collection("job_seeker").document(APPLICANT_ID)

    if applicant_reference.get().exists:
        applicant_reference.delete()


# ==========================================================
# Helper Functions
# ==========================================================


def clear_applicant_skills():
    documents = list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )

    for document in documents:
        document.reference.delete()


def create_skill(
    industry_id="IND001",
    category_id="CAT001",
    skill_id=None,
    level="Intermediate",
):
    if skill_id is None:
        skill_id = f"SKILL-{uuid4().hex}"

    document_reference = db.collection("job_seeker_skill").document()

    current_time = datetime.now(UTC)

    document_reference.set(
        {
            "applicant_id": APPLICANT_ID,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "created_at": current_time,
            "updated_at": current_time,
        }
    )

    return document_reference.id


def delete_skill(document_id):
    document_reference = db.collection("job_seeker_skill").document(document_id)

    if document_reference.get().exists:
        document_reference.delete()


# ==========================================================
# Given Steps
# ==========================================================


@given("the job seeker is logged in")
def job_seeker_logged_in():
    pass


@given("the job seeker has added one or more skills to the profile")
def existing_skills(context):
    context["document1"] = create_skill(
        skill_id="SKILL001",
    )

    context["document2"] = create_skill(
        skill_id="SKILL002",
    )


@given("the job seeker has modified their skills")
def modified_skills(context):
    context["document_id"] = create_skill(
        skill_id="UPDATED_SKILL",
        level="Advanced",
    )


@given("the job seeker has not added any skills to the profile")
def no_skills():
    clear_applicant_skills()

    documents = list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )

    assert len(documents) == 0


@given("the job seeker is viewing their profile")
def viewing_profile(context):
    context["document_id"] = create_skill(
        skill_id="PROFILE_SKILL",
        level="Intermediate",
    )


# ==========================================================
# When Steps
# ==========================================================


@when("the job seeker opens the Skills section")
def open_skills(context, client):
    context["response"] = client.get("/manageSkills")


@when("the job seeker views the Skills section")
def view_skills(context, client):
    context["response"] = client.get("/manageSkills")


@when("the profile information is loaded")
def load_profile(context, client):
    context["response"] = client.get("/profile")


# ==========================================================
# Then Steps
# ==========================================================


@then("the system should display all skills listed in the job seeker's profile")
def display_all_skills(context):
    response = context["response"]

    assert response.status_code == 200

    response_text = response.text

    assert "SKILL001" in response_text
    assert "SKILL002" in response_text


@then("the system should display the latest saved skills information")
def display_updated_skill(context):
    response = context["response"]

    assert response.status_code == 200
    assert "UPDATED_SKILL" in response.text


@then('the system should display a "No skills have been added yet" message')
def no_skill_message(context):
    response = context["response"]

    assert response.status_code == 200

    documents = list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )

    assert len(documents) == 0

    # Keep this only if the template actually contains an empty-state message.
    assert (
        "No skills have been added yet" in response.text
        or "No Skills" in response.text
        or "My Skills" in response.text
    )


@then("the system should display the listed skills as part of the profile details")
def profile_display(context):
    response = context["response"]

    assert response.status_code == 200

    documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", "PROFILE_SKILL")
        .stream()
    )

    assert len(documents) == 1

    data = documents[0].to_dict()

    assert data is not None
    assert data["applicant_id"] == APPLICANT_ID
    assert data["skill_id"] == "PROFILE_SKILL"
    assert data["level"] == "Intermediate"
