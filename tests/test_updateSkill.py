from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==========================================================
# LOAD FEATURE FILE
# ==========================================================

scenarios("features/updateSkill.feature")


# ==========================================================
# TEST CONSTANTS
# ==========================================================

TEST_SUFFIX = uuid4().hex

# Keep the applicant unique to prevent conflicts with other test files.
APPLICANT_ID = f"TEST_UPDATE_APPLICANT_{TEST_SUFFIX}"

# These must be real, active master skill IDs in Firestore.
SKILL_ID_1 = "SK000002"
SKILL_ID_2 = "SK000001"
SKILL_ID_3 = "SK000003"

INDUSTRY_ID = "IND001"
CATEGORY_ID = "CAT001"

LEVEL_BEGINNER = "Beginner"
LEVEL_INTERMEDIATE = "Intermediate"
LEVEL_ADVANCED = "Advanced"
LEVEL_EXPERT = "Expert"


# ==========================================================
# FIXTURES
# ==========================================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def context():
    return {
        "created_documents": [],
        "response": None,
    }


@pytest.fixture
def applicant_id():
    return APPLICANT_ID


@pytest.fixture(autouse=True)
def isolate_test_applicant(monkeypatch):
    """
    Give this test module its own job seeker.

    The master skill IDs remain real Firestore IDs, while the
    applicant and job_seeker_skill documents remain isolated.
    """

    monkeypatch.setenv("TEST_APPLICANT_ID", APPLICANT_ID)

    clear_applicant_skills()

    db.collection("job_seeker").document(APPLICANT_ID).set(
        {
            "uid": APPLICANT_ID,
            "name": "Update Skill Test Applicant",
            "email": f"{APPLICANT_ID.lower()}@example.com",
            "user_type": "job_seeker",
            "test": True,
        }
    )

    yield

    clear_applicant_skills()

    db.collection("job_seeker").document(APPLICANT_ID).delete()


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================


def clear_applicant_skills():
    """
    Delete all skill records belonging to this test applicant.
    """

    documents = list(
        db.collection("job_seeker_skill").where("applicant_id", "==", APPLICANT_ID).stream()
    )

    for document in documents:
        document.reference.delete()


def create_skill(
    context,
    skill_id,
    level=LEVEL_INTERMEDIATE,
    industry_id=INDUSTRY_ID,
    category_id=CATEGORY_ID,
):
    """
    Create one job seeker skill record.

    The document ID is unique, while the skill ID references
    an existing active skill in the master skills collection.
    """

    document_id = f"TEST_UPDATE_DOCUMENT_{uuid4().hex}"
    current_time = datetime.now(UTC)

    db.collection("job_seeker_skill").document(document_id).set(
        {
            "id": document_id,
            "applicant_id": APPLICANT_ID,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "created_at": current_time,
            "updated_at": current_time,
        }
    )

    context["created_documents"].append(document_id)

    return document_id


def get_skill(document_id):
    """
    Retrieve one job seeker skill record.
    """

    document = db.collection("job_seeker_skill").document(document_id).get()

    assert document.exists

    data = document.to_dict()

    assert data is not None

    return data


def post_skill_update(
    client,
    document_id,
    skill_id,
    level,
    industry_id=INDUSTRY_ID,
    category_id=CATEGORY_ID,
):
    """
    Submit a skill update without following the redirect.
    """

    return client.post(
        f"/edit-skill/{document_id}",
        data={
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
        },
        follow_redirects=False,
    )


def assert_update_success(response):
    """
    Confirm a successful skill update redirect.
    """

    assert response.status_code == 303, response.text
    assert response.headers.get("location") == "/manageSkills"


# ==========================================================
# GIVEN STEPS
# ==========================================================


@given("the job seeker has an existing skill listed in the profile")
def given_existing_skill(context):
    context["document_id"] = create_skill(
        context,
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@given("the job seeker has multiple skills listed in the profile")
def given_multiple_skills(context):
    context["document1"] = create_skill(
        context,
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )

    context["document2"] = create_skill(
        context,
        skill_id=SKILL_ID_2,
        level=LEVEL_INTERMEDIATE,
    )


@given("the job seeker already has a skill listed in the profile")
def given_duplicate_skills(context):
    context["document1"] = create_skill(
        context,
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    context["document2"] = create_skill(
        context,
        skill_id=SKILL_ID_2,
        level=LEVEL_INTERMEDIATE,
    )


@given("the selected skill does not exist")
def given_invalid_document(context):
    context["document_id"] = f"INVALID_DOCUMENT_{uuid4().hex}"


@given("the job seeker is editing an existing skill")
def given_edit_existing(context):
    context["document_id"] = create_skill(
        context,
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@given("the job seeker is editing a skill")
def given_edit_skill(context):
    context["document_id"] = create_skill(
        context,
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


# ==========================================================
# WHEN STEPS
# ==========================================================


@when("the job seeker edits the skill information and saves the changes")
def update_skill(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        skill_id=SKILL_ID_3,
        level=LEVEL_ADVANCED,
    )


@when("the job seeker changes the skill level and saves the changes")
def update_skill_level(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        skill_id=SKILL_ID_1,
        level=LEVEL_EXPERT,
    )


@when("the job seeker updates multiple skills")
def update_multiple_skills(context, client):
    context["response1"] = post_skill_update(
        client=client,
        document_id=context["document1"],
        skill_id=SKILL_ID_1,
        level=LEVEL_ADVANCED,
    )

    context["response2"] = post_skill_update(
        client=client,
        document_id=context["document2"],
        skill_id=SKILL_ID_2,
        level=LEVEL_EXPERT,
    )


@when("the job seeker changes the industry category skill and saves the changes")
def update_skill_information(context, client):
    """
    Use a known-valid industry, category and skill combination.

    The scenario still verifies that the selected skill information
    and level are updated successfully.
    """

    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        industry_id=INDUSTRY_ID,
        category_id=CATEGORY_ID,
        skill_id=SKILL_ID_3,
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker updates another skill to the same skill")
def update_duplicate_skill(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document2"],
        skill_id=SKILL_ID_1,
        level=LEVEL_BEGINNER,
    )


@when("the job seeker submits the update")
def update_invalid_document(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker cancels the update")
def cancel_update(context, client):
    context["response"] = client.get(
        "/manageSkills",
        follow_redirects=False,
    )


@when("the job seeker saves the skill without making any changes")
def save_without_changes(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker submits the form without selecting an industry")
def empty_industry(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        industry_id="",
        category_id=CATEGORY_ID,
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker submits the form without selecting a category")
def empty_category(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        industry_id=INDUSTRY_ID,
        category_id="",
        skill_id=SKILL_ID_1,
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker submits the form without selecting a skill")
def empty_skill(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        industry_id=INDUSTRY_ID,
        category_id=CATEGORY_ID,
        skill_id="",
        level=LEVEL_INTERMEDIATE,
    )


@when("the job seeker submits the form without selecting a skill level")
def empty_level(context, client):
    context["response"] = post_skill_update(
        client=client,
        document_id=context["document_id"],
        industry_id=INDUSTRY_ID,
        category_id=CATEGORY_ID,
        skill_id=SKILL_ID_1,
        level="",
    )


# ==========================================================
# THEN STEPS
# ==========================================================


@then("the system should update the skill successfully")
def update_success(context):
    response = context["response"]

    assert_update_success(response)

    data = get_skill(context["document_id"])

    assert data["industry_id"] == INDUSTRY_ID
    assert data["category_id"] == CATEGORY_ID
    assert data["skill_id"] == SKILL_ID_3
    assert data["level"] == LEVEL_ADVANCED


@then("display the updated skill in the profile")
def updated_skill(context, client):
    response = client.get("/manageSkills")

    assert response.status_code == 200

    data = get_skill(context["document_id"])

    assert data["skill_id"] == SKILL_ID_3
    assert data["level"] == LEVEL_ADVANCED


@then("the system should update the skill level successfully")
def update_level_success(context):
    response = context["response"]

    assert_update_success(response)

    data = get_skill(context["document_id"])

    assert data["skill_id"] == SKILL_ID_1
    assert data["level"] == LEVEL_EXPERT


@then("the system should save all updated skills successfully")
def update_multiple_success(context):
    first_response = context["response1"]
    second_response = context["response2"]

    assert_update_success(first_response)
    assert_update_success(second_response)

    first_data = get_skill(context["document1"])
    second_data = get_skill(context["document2"])

    assert first_data["skill_id"] == SKILL_ID_1
    assert first_data["level"] == LEVEL_ADVANCED

    assert second_data["skill_id"] == SKILL_ID_2
    assert second_data["level"] == LEVEL_EXPERT


@then("the system should display the updated skill information")
def updated_information(context, client):
    response = context["response"]

    assert_update_success(response)

    data = get_skill(context["document_id"])

    assert data["industry_id"] == INDUSTRY_ID
    assert data["category_id"] == CATEGORY_ID
    assert data["skill_id"] == SKILL_ID_3
    assert data["level"] == LEVEL_INTERMEDIATE

    page_response = client.get("/manageSkills")

    assert page_response.status_code == 200


@then("the system should prevent duplicate skills from being saved")
def duplicate_prevented(context):
    response = context["response"]

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Skill already added"

    first_data = get_skill(context["document1"])
    second_data = get_skill(context["document2"])

    assert first_data["skill_id"] == SKILL_ID_1
    assert second_data["skill_id"] == SKILL_ID_2

    assert second_data["level"] == LEVEL_INTERMEDIATE


@then("display an appropriate validation message")
def duplicate_message(context):
    response = context["response"]

    assert response.status_code == 400
    assert response.json()["detail"] == "Skill already added"


@then("the system should display an error message")
def invalid_document(context):
    response = context["response"]

    assert response.status_code == 404
    assert response.json()["detail"] == "Skill not found"


@then("the original skill information should remain unchanged")
def cancel_update_success(context):
    response = context["response"]

    assert response.status_code == 200

    data = get_skill(context["document_id"])

    assert data["industry_id"] == INDUSTRY_ID
    assert data["category_id"] == CATEGORY_ID
    assert data["skill_id"] == SKILL_ID_1
    assert data["level"] == LEVEL_INTERMEDIATE


@then("the system should keep the existing skill information")
def keep_information(context):
    response = context["response"]

    assert_update_success(response)

    data = get_skill(context["document_id"])

    assert data["industry_id"] == INDUSTRY_ID
    assert data["category_id"] == CATEGORY_ID
    assert data["skill_id"] == SKILL_ID_1
    assert data["level"] == LEVEL_INTERMEDIATE


@then("the system should display a validation message")
def validation_message(context):
    response = context["response"]

    # Empty strings are handled inside the route and return 400.
    # A missing form field would instead be handled by FastAPI as 422.
    assert response.status_code in (400, 422)

    body = response.json()

    assert "detail" in body
