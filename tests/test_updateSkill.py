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
from google.api_core.exceptions import NotFound
from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)

scenarios("features/updateSkill.feature")


# ==========================================================
# Fixtures
# ==========================================================

@pytest.fixture
def context():
    return {}


@pytest.fixture
def applicant_id():
    return "applicant001"


# ==========================================================
# Helper Functions
# ==========================================================

def create_skill(
    industry_id="IND001",
    category_id="CAT001",
    skill_id=None,
    level="Intermediate"
):

    if skill_id is None:
        skill_id = str(uuid4())

    doc = db.collection("job_seeker_skill").document()

    doc.set({

        "applicant_id": "applicant001",

        "industry_id": industry_id,

        "category_id": category_id,

        "skill_id": skill_id,

        "level": level,

        "created_at": datetime.utcnow(),

        "updated_at": datetime.utcnow()

    })

    return doc.id


def delete_skill(document_id):

    doc_ref = db.collection(
        "job_seeker_skill"
    ).document(document_id)

    if doc_ref.get().exists:
        doc_ref.delete()


# ==========================================================
# GIVEN
# ==========================================================

@given("the job seeker has an existing skill listed in the profile")
def given_existing_skill(context):

    context["document_id"] = create_skill(
        skill_id="SKILL001"
    )


@given("the job seeker has multiple skills listed in the profile")
def given_multiple_skills(context):

    context["document1"] = create_skill(
        skill_id="SKILL001"
    )

    context["document2"] = create_skill(
        skill_id="SKILL002"
    )


@given("the job seeker already has a skill listed in the profile")
def given_duplicate_skills(context):

    context["document1"] = create_skill(
        skill_id="SKILL001"
    )

    context["document2"] = create_skill(
        skill_id="SKILL002"
    )


@given("the selected skill does not exist")
def given_invalid_document(context):

    context["document_id"] = "invalid_document_id"


@given("the job seeker is editing an existing skill")
def given_edit_existing(context):

    context["document_id"] = create_skill(
        skill_id="SKILL001"
    )


@given("the job seeker is editing a skill")
def given_edit_skill(context):

    context["document_id"] = create_skill(
        skill_id="SKILL001"
    )

# ==========================================================
# WHEN
# ==========================================================

@when("the job seeker edits the skill information and saves the changes")
def update_skill(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "UPDATED_SKILL",

            "level": "Advanced"

        },

        follow_redirects=False

    )


@when("the job seeker changes the skill level and saves the changes")
def update_skill_level(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Expert"

        },

        follow_redirects=False

    )


@when("the job seeker updates multiple skills")
def update_multiple_skills(context):

    context["response1"] = client.post(

        f"/edit-skill/{context['document1']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Advanced"

        },

        follow_redirects=False

    )

    context["response2"] = client.post(

        f"/edit-skill/{context['document2']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL002",

            "level": "Expert"

        },

        follow_redirects=False

    )


@when("the job seeker changes the industry category skill and saves the changes")
def update_skill_information(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND002",

            "category_id": "CAT002",

            "skill_id": "NEW_SKILL",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker updates another skill to the same skill")
def update_duplicate_skill(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document2']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Beginner"

        },

        follow_redirects=False

    )


@when("the job seeker submits the update")
def update_invalid_document(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker cancels the update")
def cancel_update(context):

    context["response"] = client.get(

        "/manageSkills"

    )


@when("the job seeker saves the skill without making any changes")
def save_without_changes(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker submits the form without selecting an industry")
def empty_industry(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker submits the form without selecting a category")
def empty_category(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "",

            "skill_id": "SKILL001",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker submits the form without selecting a skill")
def empty_skill(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "",

            "level": "Intermediate"

        },

        follow_redirects=False

    )


@when("the job seeker submits the form without selecting a skill level")
def empty_level(context):

    context["response"] = client.post(

        f"/edit-skill/{context['document_id']}",

        data={

            "industry_id": "IND001",

            "category_id": "CAT001",

            "skill_id": "SKILL001",

            "level": ""

        },

        follow_redirects=False

    )

# ==========================================================
# THEN
# ==========================================================

@then("the system should update the skill successfully")
def update_success(context):

    assert context["response"].status_code == 303


@then("display the updated skill in the profile")
def updated_skill(context):

    response = client.get("/manageSkills")

    assert response.status_code == 200

    delete_skill(context["document_id"])


@then("the system should update the skill level successfully")
def update_level_success(context):

    assert context["response"].status_code == 303

    delete_skill(context["document_id"])


@then("the system should save all updated skills successfully")
def update_multiple_success(context):

    assert context["response1"].status_code == 303

    assert context["response2"].status_code == 303

    delete_skill(context["document1"])

    delete_skill(context["document2"])


@then("the system should display the updated skill information")
def updated_information(context):

    response = client.get("/manageSkills")

    assert response.status_code == 200

    delete_skill(context["document_id"])


@then("the system should prevent duplicate skills from being saved")
def duplicate_prevented(context):

    assert context["response"].status_code == 303


@then("display an appropriate validation message")
def duplicate_message(context):

    response = client.get("/manageSkills")

    assert response.status_code == 200

    delete_skill(context["document1"])

    delete_skill(context["document2"])


@then("the system should display an error message")
def invalid_document(context):

    assert context["response"].status_code == 303

@then("the original skill information should remain unchanged")
def cancel_update_success(context):

    doc = (

        db.collection("job_seeker_skill")

        .document(context["document_id"])

        .get()

    )

    assert doc.exists

    delete_skill(context["document_id"])


@then("the system should keep the existing skill information")
def keep_information(context):

    assert context["response"].status_code == 303

    delete_skill(context["document_id"])


@then("the system should display a validation message")
def validation_message(context):

    assert context["response"].status_code == 422

    delete_skill(context["document_id"])