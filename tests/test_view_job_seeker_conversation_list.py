import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/view_job_seeker_conversation_list.feature")


JOB_SEEKER_ID = "J000001"
EMPTY_JOB_SEEKER_ID = "J999999"
EMPLOYER_ID = "C000001"
CONVERSATION_ID = f"{EMPLOYER_ID}_{JOB_SEEKER_ID}"

MESSAGE_ID = "TEST_JOBSEEKER_MESSAGE_001"
COMPANY_ID = "C000001"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def context():
    return {
        "response": None,
    }


def create_session(client, data):
    secret_key = None

    for middleware in app.user_middleware:
        if middleware.cls == SessionMiddleware:
            secret_key = middleware.kwargs["secret_key"]
            break

    if secret_key is None:
        raise RuntimeError("SessionMiddleware secret key not found")

    encoded_data = base64.b64encode(json.dumps(data).encode())

    signer = TimestampSigner(secret_key)
    cookie_value = signer.sign(encoded_data).decode()

    client.cookies.set(
        "session",
        cookie_value,
    )


def set_job_seeker_session(client):
    create_session(
        client,
        {
            "user_type": "job_seeker",
            "applicant_id": JOB_SEEKER_ID,
        },
    )


def set_empty_job_seeker_session(client):
    create_session(
        client,
        {
            "user_type": "job_seeker",
            "applicant_id": EMPTY_JOB_SEEKER_ID,
        },
    )


def remove_test_data():
    db.collection("messages").document(MESSAGE_ID).delete()
    db.collection("company").document(COMPANY_ID).delete()
    db.collection("job_seeker").document(JOB_SEEKER_ID).delete()


def insert_test_data():
    remove_test_data()

    db.collection("job_seeker").document(JOB_SEEKER_ID).set(
        {
            "name": "James",
            "email": "james@test.com",
            "test": True,
        }
    )

    db.collection("company").document(COMPANY_ID).set(
        {
            "companyName": "ABC Company",
            "test": True,
        }
    )

    db.collection("messages").document(MESSAGE_ID).set(
        {
            "conversationId": CONVERSATION_ID,
            "message": "Your interview has been scheduled",
            "time": "2099-07-30T10:00:00",
            "timestamp": "2099-07-30T10:00:00",
            "senderId": EMPLOYER_ID,
            "senderType": "employer",
            "receiverId": JOB_SEEKER_ID,
            "receiverType": "job_seeker",
            "employerId": EMPLOYER_ID,
            "jobSeekerId": JOB_SEEKER_ID,
            "test": True,
        }
    )


@pytest.fixture(autouse=True)
def cleanup():
    remove_test_data()

    yield

    remove_test_data()


@given("the job seeker is logged in and has existing conversations with employers")
def job_seeker_has_conversations(client):
    insert_test_data()
    set_job_seeker_session(client)


@given("the job seeker is viewing the conversation list")
def job_seeker_view_list(client):
    insert_test_data()
    set_job_seeker_session(client)


@given("the job seeker has no conversations with employers")
def job_seeker_no_conversations(client):
    remove_test_data()
    set_empty_job_seeker_session(client)


@when("the job seeker opens the Messages page")
def open_messages_page(context, client):
    context["response"] = client.get("/api/conversations")


@when("the conversations are loaded")
def load_conversations(context, client):
    context["response"] = client.get("/api/conversations")


@then("the system should display the list of conversations with employers")
def verify_conversation_list(context):
    response = context["response"]

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) > 0, response.text

    conversation = next(
        (item for item in data if item.get("conversationId") == CONVERSATION_ID),
        None,
    )

    assert conversation is not None


@then("the system should display the latest message and conversation details")
def verify_latest_information(context):
    response = context["response"]

    assert response.status_code == 200, response.text

    data = response.json()

    conversation = next(
        (item for item in data if item.get("conversationId") == CONVERSATION_ID),
        None,
    )

    assert conversation is not None, data
    assert conversation["lastMessage"] == ("Your interview has been scheduled")
    assert conversation["employerId"] == EMPLOYER_ID
    assert conversation["jobSeekerId"] == JOB_SEEKER_ID


@then('the system should display a "No conversations available" message')
def verify_no_conversation(context):
    response = context["response"]

    assert response.status_code == 200
    assert response.json() == []
