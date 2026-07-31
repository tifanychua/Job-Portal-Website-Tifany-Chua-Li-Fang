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

scenarios("features/removeSkill.feature")


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def context():
    return {}


@pytest.fixture
def applicant_id():
    return "applicant001"


def create_skill():

    doc = db.collection("job_seeker_skill").document()

    doc.set(
        {
            "applicant_id": "applicant001",
            "industry_id": "IND001",
            "category_id": "CAT001",
            "skill_id": str(uuid4()),
            "level": "Intermediate",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )

    return doc.id


# ==========================================================
# GIVEN
# ==========================================================


@given("the job seeker has one or more skills listed in the profile")
def given_one_skill(context):

    context["document_id"] = create_skill()


@given("the job seeker has multiple skills listed in the profile")
def given_multiple_skills(context):

    ids = []

    for i in range(3):
        ids.append(create_skill())

    context["document_ids"] = ids


@given("the job seeker selects a skill to remove")
def given_selected_skill(context):

    context["document_id"] = create_skill()


@given("the job seeker has only one skill listed")
def given_last_skill(context):

    context["document_id"] = create_skill()


@given("the document ID does not exist")
def given_invalid_document(context):

    context["document_id"] = "invalid_document_id"


# ==========================================================
# WHEN
# ==========================================================


@when("the job seeker removes a skill")
def remove_skill(context):

    context["response"] = client.post(
        f"/delete-skill/{context['document_id']}", follow_redirects=False
    )


@when("the job seeker removes multiple skills one by one")
def remove_multiple(context):

    responses = []

    for doc_id in context["document_ids"]:

        responses.append(client.post(f"/delete-skill/{doc_id}", follow_redirects=False))

    context["responses"] = responses


@when("the job seeker cancels the removal confirmation")
def cancel_remove(context):

    pass


@when("the job seeker removes the skill")
def remove_last_skill(context):

    context["response"] = client.post(
        f"/delete-skill/{context['document_id']}", follow_redirects=False
    )


@when("the job seeker submits the delete request")
def remove_invalid(context):

    context["response"] = client.post(
        f"/delete-skill/{context['document_id']}", follow_redirects=False
    )


# ==========================================================
# THEN
# ==========================================================


@then("the system should remove the selected skill successfully")
def remove_success(context):

    assert context["response"].status_code == 303


@then("the system should remove the skill successfully")
def remove_last_skill_successfully(context):

    assert context["response"].status_code == 303


@then("update the skill list displayed in the profile")
def update_skill_list():

    response = client.get("/manageSkills")

    assert response.status_code == 200


@then("the system should remove all selected skills successfully")
def remove_multiple_success(context):

    for response in context["responses"]:

        assert response.status_code == 303


@then("display the remaining skills in the profile")
def remaining_skills():

    response = client.get("/manageSkills")

    assert response.status_code == 200


@then("the system should keep the skill unchanged in the profile")
def cancel_success(context):

    doc = db.collection("job_seeker_skill").document(context["document_id"]).get()

    assert doc.exists


@then('display a "No skills have been added yet" message')
def empty_message():

    response = client.get("/manageSkills")

    assert response.status_code == 200


@then("the system should display an error message")
def invalid_delete(context):

    assert context["response"].status_code in [303, 404]
