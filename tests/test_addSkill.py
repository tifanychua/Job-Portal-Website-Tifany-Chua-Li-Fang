from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app
from job_portal_web.backend.routes import skill as skill_route

# ==================================================
# Load Feature File
# ==================================================

scenarios("features/addSkill.feature")


# ==================================================
# Test Constants
# ==================================================

TEST_SUFFIX = uuid4().hex

APPLICANT_ID = f"TEST_ADD_SKILL_APPLICANT_{TEST_SUFFIX}"

INDUSTRY_ID = "IND001"
CATEGORY_ID = "CAT001"

SKILL_ID_1 = "SK000002"
SKILL_ID_2 = "SK000001"
SKILL_ID_3 = "SK000003"

LEVEL_BEGINNER = "Beginner"
LEVEL_INTERMEDIATE = "Intermediate"
LEVEL_ADVANCED = "Advanced"


# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==================================================
# Context
# ==================================================


@pytest.fixture
def context():
    return {}


# ==================================================
# Helper Functions
# ==================================================


def get_document_id(skill_id: str) -> str:
    return f"{APPLICANT_ID}_{skill_id}"


def get_skill_document(skill_id: str):
    return db.collection("job_seeker_skill").document(get_document_id(skill_id)).get()


def get_skill_data(skill_id: str) -> dict:
    document = get_skill_document(skill_id)

    assert document.exists, f"Expected skill document {get_document_id(skill_id)} was not found"

    data = document.to_dict()

    assert data is not None

    return data


def create_skill(
    skill_id: str,
    level: str = LEVEL_BEGINNER,
    industry_id: str = INDUSTRY_ID,
    category_id: str = CATEGORY_ID,
):
    document_id = get_document_id(skill_id)

    db.collection("job_seeker_skill").document(document_id).set(
        {
            "id": document_id,
            "applicant_id": APPLICANT_ID,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
        }
    )

    return document_id


def delete_skill(skill_id: str):
    deterministic_reference = db.collection("job_seeker_skill").document(get_document_id(skill_id))

    if deterministic_reference.get().exists:
        deterministic_reference.delete()

    matching_documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", skill_id)
        .stream()
    )

    for document in matching_documents:
        document.reference.delete()


def clear_all_skills():
    matching_documents = list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )

    for document in matching_documents:
        document.reference.delete()

    for skill_id in (
        SKILL_ID_1,
        SKILL_ID_2,
        SKILL_ID_3,
        "INVALID_SKILL",
    ):
        reference = db.collection("job_seeker_skill").document(get_document_id(skill_id))

        if reference.get().exists:
            reference.delete()


def get_all_skills():
    return list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )


def post_skill(
    client,
    skill_id: str,
    level: str,
    industry_id: str = INDUSTRY_ID,
    category_id: str = CATEGORY_ID,
):
    return client.post(
        "/add-skill",
        data={
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
        },
        follow_redirects=False,
    )


def assert_add_success(response):
    assert response.status_code == 303, (
        f"Expected 303 redirect, received {response.status_code}: {response.text}"
    )

    assert response.headers.get("location") == "/manageSkills"


def assert_saved_skill(
    skill_id: str,
    expected_level: str,
):
    data = get_skill_data(skill_id)

    assert data["applicant_id"] == APPLICANT_ID
    assert data["industry_id"] == INDUSTRY_ID
    assert data["category_id"] == CATEGORY_ID
    assert data["skill_id"] == skill_id
    assert data["level"] == expected_level


# ==================================================
# Automatic Test Isolation
# ==================================================


@pytest.fixture(autouse=True)
def reset_test_applicant(monkeypatch):
    """
    Give this test module its own applicant and skill records.
    """

    monkeypatch.setenv(
        "TEST_APPLICANT_ID",
        APPLICANT_ID,
    )

    monkeypatch.setattr(
        skill_route,
        "get_current_applicant_id",
        lambda request: APPLICANT_ID,
    )

    clear_all_skills()

    db.collection("job_seeker").document(APPLICANT_ID).set(
        {
            "uid": APPLICANT_ID,
            "name": "Add Skill Test User",
            "email": f"{APPLICANT_ID.lower()}@example.com",
            "position": "Software Engineer",
            "user_type": "job_seeker",
            "test": True,
        }
    )

    yield

    clear_all_skills()

    applicant_reference = db.collection("job_seeker").document(APPLICANT_ID)

    if applicant_reference.get().exists:
        applicant_reference.delete()


# ==================================================
# Given Steps
# ==================================================


@given("the job seeker is logged in")
def job_seeker_logged_in():
    return True


@given("is on the Edit Profile page")
@given("the job seeker is on the Edit Profile page")
def open_edit_profile(context, client):
    response = client.get("/manageSkills")

    assert response.status_code == 200

    context["response"] = response


@given("the job seeker has no skills in the profile")
def no_skills():
    clear_all_skills()

    assert len(get_all_skills()) == 0


@given("the job seeker has already added a skill")
def existing_skill():
    clear_all_skills()

    create_skill(
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
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
def add_single_skill(context, client):
    clear_all_skills()

    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )


@when("the job seeker adds multiple skills and saves the profile")
def add_multiple_skills(context, client):
    clear_all_skills()

    first_response = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    assert_add_success(first_response)

    second_response = post_skill(
        client=client,
        skill_id=SKILL_ID_2,
        level=LEVEL_INTERMEDIATE,
    )

    assert_add_success(second_response)

    context["response"] = second_response


@when("the job seeker leaves the skills section empty and saves the profile")
def save_without_skill(context, client):
    clear_all_skills()

    context["response"] = client.post(
        "/save-profile",
        data={},
        follow_redirects=True,
    )


@when("the job seeker adds skills with different proficiency levels")
def add_different_levels(context, client):
    clear_all_skills()

    first_response = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_BEGINNER,
    )

    assert_add_success(first_response)

    second_response = post_skill(
        client=client,
        skill_id=SKILL_ID_2,
        level=LEVEL_INTERMEDIATE,
    )

    assert_add_success(second_response)

    third_response = post_skill(
        client=client,
        skill_id=SKILL_ID_3,
        level=LEVEL_ADVANCED,
    )

    assert_add_success(third_response)

    context["response"] = third_response


@when("the job seeker adds a new skill and saves the profile")
def add_first_skill(context, client):
    clear_all_skills()

    response = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    assert_add_success(response)

    context["response"] = response


@when("the job seeker attempts to add the same skill again")
def add_duplicate_skill(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )


@when("the job seeker leaves the industry field empty")
def empty_industry(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
        industry_id="",
    )


@when("saves the profile")
def save_profile():
    pass


@when("the job seeker leaves the skill category field empty")
def empty_category(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
        category_id="",
    )


@when("the job seeker leaves the skill field empty")
def empty_skill(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id="",
        level=LEVEL_ADVANCED,
    )


@when("the job seeker leaves the proficiency level field empty")
def empty_level(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level="",
    )


@when("the job seeker attempts to add an invalid skill")
def invalid_skill(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id="INVALID_SKILL",
        level=LEVEL_ADVANCED,
    )


@when("the job seeker selects a skill category that does not belong to the selected industry")
def invalid_category(context, client):
    context["response"] = post_skill(
        client=client,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
        category_id="INVALID_CATEGORY",
    )


# ==================================================
# Then Steps: Positive Scenarios
# ==================================================


@then("the system should save the skills successfully")
def skill_saved_successfully(context):
    assert_add_success(context["response"])

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
    )


@then("display the updated skills in the profile")
def updated_skill_displayed(context, client):
    response = client.get("/profile")

    assert response.status_code == 200

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
    )


@then("the system should display all added skills in the profile")
def multiple_skills_displayed(context, client):
    response = client.get("/profile")

    assert response.status_code == 200

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
    )

    assert_saved_skill(
        skill_id=SKILL_ID_2,
        expected_level=LEVEL_INTERMEDIATE,
    )


@then("the system should save the profile")
def profile_saved(context):
    assert context["response"].status_code == 200


@then("indicate that no skills have been added")
def no_skill_message(context, client):
    response = client.get("/profile")

    assert response.status_code == 200
    assert len(get_all_skills()) == 0


@then("the system should save all skills with their selected proficiency levels")
def verify_skill_levels(context):
    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_BEGINNER,
    )

    assert_saved_skill(
        skill_id=SKILL_ID_2,
        expected_level=LEVEL_INTERMEDIATE,
    )

    assert_saved_skill(
        skill_id=SKILL_ID_3,
        expected_level=LEVEL_ADVANCED,
    )


@then("the system should display the newly added skill in the profile")
def first_skill_displayed(context, client):
    response = client.get("/profile")

    assert response.status_code == 200

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
    )


# ==================================================
# Then Steps: Negative Scenarios
# ==================================================


@then("the system should prevent duplicate skills from being added")
def duplicate_skill_not_added(context):
    response = context["response"]

    assert response.status_code == 400
    assert response.json()["detail"] == "Skill already added"

    assert_saved_skill(
        skill_id=SKILL_ID_1,
        expected_level=LEVEL_ADVANCED,
    )

    matching_documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", SKILL_ID_1)
        .stream()
    )

    assert len(matching_documents) == 1


@then("display duplicate skill validation message")
def duplicate_validation_message(context):
    response = context["response"]

    assert response.status_code == 400
    assert response.json()["detail"] == "Skill already added"


@then("the system should display a validation message for the industry field")
def industry_validation(context):
    response = context["response"]

    assert response.status_code in (400, 422)
    assert "Industry" in response.text or "industry_id" in response.text


@then("the system should display a validation message for the skill category field")
def category_validation(context):
    response = context["response"]

    assert response.status_code in (400, 422)
    assert "Category" in response.text or "category_id" in response.text


@then("the system should display a validation message for the skill field")
def skill_validation(context):
    response = context["response"]

    assert response.status_code in (400, 422)
    assert "Skill" in response.text or "skill_id" in response.text


@then("the system should display a validation message for the proficiency level field")
def level_validation(context):
    response = context["response"]

    assert response.status_code in (400, 422)
    assert "Level" in response.text or "level" in response.text


@then("the system should reject the skill")
def reject_invalid_skill(context):
    matching_documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("skill_id", "==", "INVALID_SKILL")
        .stream()
    )

    assert len(matching_documents) == 0
    assert not get_skill_document("INVALID_SKILL").exists


@then("display invalid skill validation message")
def invalid_skill_message(context):
    response = context["response"]

    assert response.status_code == 400
    assert "Invalid Skill" in response.text


@then("the system should prevent the skill from being saved")
def invalid_category_not_saved(context):
    matching_documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", APPLICANT_ID)
        .where("category_id", "==", "INVALID_CATEGORY")
        .stream()
    )

    assert len(matching_documents) == 0


@then("display invalid category validation message")
def invalid_category_message(context):
    response = context["response"]

    assert response.status_code == 400
    assert "Invalid Category" in response.text
