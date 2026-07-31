from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import (
    scenarios,
    given,
    when,
    then)

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# Load Feature File
# ==================================================

scenarios("features/addSkill.feature")

# ==================================================
# Test Client
# ==================================================

client = TestClient(app)

# ==================================================
# Test Constants
# ==================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"

INDUSTRY_ID = "IND001"
CATEGORY_ID = "CAT001"

SKILL_ID_1 = "SK000002"
SKILL_ID_2 = "SK000001"
SKILL_ID_3 = "SK000003"

LEVEL_BEGINNER = "Beginner"
LEVEL_INTERMEDIATE = "Intermediate"
LEVEL_ADVANCED = "Advanced"

# ==================================================
# Helper Functions
# ==================================================


def create_skill(
    skill_id: str,
    level: str = LEVEL_BEGINNER,
    industry_id: str = INDUSTRY_ID,
    category_id: str = CATEGORY_ID,
):
    """
    Insert a skill into Firestore.
    """

    doc_id = str(uuid4())

    db.collection("job_seeker_skill").document(doc_id).set(
        {
            "id": doc_id,
            "applicant_id": APPLICANT_ID,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
        }
    )

    return doc_id


def delete_skill(skill_id: str):
    """
    Remove all matching skills.
    """

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", skill_id)
        .stream()
    )

    for doc in docs:
        doc.reference.delete()


def clear_all_skills():
    """
    Remove every skill belonging to 0YLcc18JszVqSXWn8DEDQ81o2vR2.
    """

    docs = db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()

    for doc in docs:
        doc.reference.delete()


# ==================================================
# Fixtures
# ==================================================


@pytest.fixture
def context():
    """
    Shared scenario context.
    """
    return {}


# ==================================================
# Given Steps
# ==================================================


@given("the job seeker is logged in")
def job_seeker_logged_in():
    """
    Login is mocked.
    """
    return True


@given("is on the Edit Profile page")
@given("the job seeker is on the Edit Profile page")
def open_edit_profile(context):
    response = client.get("/manageSkills")

    assert response.status_code == 200

    context["response"] = response


@given("the job seeker has no skills in the profile")
def no_skills():
    clear_all_skills()


@given("the job seeker has already added a skill")
def existing_skill():
    clear_all_skills()

    create_skill(
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )


@given("the job seeker has existing skills")
def existing_multiple_skills():
    clear_all_skills()

    create_skill(
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    create_skill(
        skill_id=SKILL_ID_2,
        level=LEVEL_INTERMEDIATE,
    )


# ==================================================
# When Steps
# ==================================================


@when("the job seeker enters one or more skills and saves the profile")
def add_single_skill(context):

    delete_skill(SKILL_ID_1)

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker adds multiple skills and saves the profile")
def add_multiple_skills(context):

    clear_all_skills()

    client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_2,
            "level": LEVEL_INTERMEDIATE,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker leaves the skills section empty and saves the profile")
def save_without_skill(context):

    response = client.post(
        "/save-profile",
        data={},
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker adds skills with different proficiency levels")
def add_different_levels(context):

    clear_all_skills()

    client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_BEGINNER,
        },
        follow_redirects=True,
    )

    client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_2,
            "level": LEVEL_INTERMEDIATE,
        },
        follow_redirects=True,
    )

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_3,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker adds a new skill and saves the profile")
def add_first_skill(context):

    clear_all_skills()

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker attempts to add the same skill again")
def add_duplicate_skill(context):

    # The skill has already been created in the Given step.
    # Simply attempt to add it again through the API.

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker leaves the industry field empty")
def empty_industry(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": "",
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("saves the profile")
def save_profile(context):
    """
    Placeholder step for validation scenarios.
    """
    pass


@when("the job seeker leaves the skill category field empty")
def empty_category(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": "",
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker leaves the skill field empty")
def empty_skill(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": "",
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker leaves the proficiency level field empty")
def empty_level(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": SKILL_ID_1,
            "level": "",
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker attempts to add an invalid skill")
def invalid_skill(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": INDUSTRY_ID,
            "category_id": CATEGORY_ID,
            "skill_id": "INVALID_SKILL",
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


@when("the job seeker selects a skill category that does not belong to the selected industry")
def invalid_category(context):

    response = client.post(
        "/add-skill",
        data={
            "industry_id": "IND001",
            "category_id": "INVALID_CATEGORY",
            "skill_id": SKILL_ID_1,
            "level": LEVEL_ADVANCED,
        },
        follow_redirects=True,
    )

    context["response"] = response


# ==================================================
# Then Steps (Positive Scenarios)
# ==================================================


@then("the system should save the skills successfully")
def skill_saved_successfully(context):

    response = context["response"]

    assert response.status_code == 200

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", SKILL_ID_1)
        .stream()
    )

    skills = list(docs)

    assert len(skills) == 1


@then("display the updated skills in the profile")
def updated_skill_displayed(context):

    response = client.get("/profile")

    assert response.status_code == 200

    response_text = response.text

    assert "Python" in response_text


@then("the system should display all added skills in the profile")
def multiple_skills_displayed(context):

    response = client.get("/profile")

    assert response.status_code == 200

    response_text = response.text

    assert "Python" in response_text
    assert "Java" in response_text


@then("the system should save the profile")
def profile_saved(context):

    response = context["response"]

    assert response.status_code == 200


@then("indicate that no skills have been added")
def no_skill_message(context):

    response = client.get("/profile")

    assert response.status_code == 200

    response_text = response.text

    assert (
        "No skills have been added" in response_text
        or "No Skills" in response_text
        or "No skills yet" in response_text
    )


@then("the system should save all skills with their selected proficiency levels")
def verify_skill_levels(context):

    docs = db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()

    levels = []

    for doc in docs:

        levels.append(doc.to_dict()["level"])

    assert LEVEL_BEGINNER in levels
    assert LEVEL_INTERMEDIATE in levels
    assert LEVEL_ADVANCED in levels


@then("the system should display the newly added skill in the profile")
def first_skill_displayed(context):

    response = client.get("/profile")

    assert response.status_code == 200

    response_text = response.text

    assert "Python" in response_text


# ==================================================
# Then Steps (Negative Scenarios)
# ==================================================


@then("the system should prevent duplicate skills from being added")
def duplicate_skill_not_added(context):

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", SKILL_ID_1)
        .stream()
    )

    skills = list(docs)

    # Only one record should exist
    assert len(skills) == 1


@then("display duplicate skill validation message")
def duplicate_validation_message(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "already exists" in response.text
        or "Duplicate" in response.text
        or "Skill already added" in response.text
    )


@then("the system should display a validation message for the industry field")
def industry_validation(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "Industry" in response.text
        or "industry_id" in response.text
        or "Select Industry" in response.text
    )


@then("the system should display a validation message for the skill category field")
def category_validation(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "Category" in response.text
        or "category_id" in response.text
        or "Select Skill Category" in response.text
    )


@then("the system should display a validation message for the skill field")
def skill_validation(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "Skill" in response.text or "skill_id" in response.text or "Select Skill" in response.text
    )


@then("the system should display a validation message for the proficiency level field")
def level_validation(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "Level" in response.text
        or "level" in response.text
        or "Select Skill Level" in response.text
    )


@then("the system should reject the skill")
def reject_invalid_skill(context):

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", "INVALID_SKILL")
        .stream()
    )

    assert len(list(docs)) == 0


@then("display invalid skill validation message")
def invalid_skill_message(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert "Invalid Skill" in response.text or "Skill does not exist" in response.text


@then("the system should prevent the skill from being saved")
def invalid_category_not_saved(context):

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("category_id", "==", "INVALID_CATEGORY")
        .stream()
    )

    assert len(list(docs)) == 0


@then("display invalid category validation message")
def invalid_category_message(context):

    response = context["response"]

    assert response.status_code in (200, 400, 422)

    assert (
        "Invalid Category" in response.text
        or "Category does not belong to industry" in response.text
    )


# ==================================================
# Cleanup
# ==================================================


@pytest.fixture(autouse=True)
def cleanup():

    yield

    clear_all_skills()
