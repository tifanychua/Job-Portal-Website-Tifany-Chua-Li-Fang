import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==========================================
# FEATURE FILE
# ==========================================

scenarios("features/view_job_seeker_conversation_list.feature")


# ==========================================
# TEST CONSTANTS
# ==========================================

JOB_SEEKER_ID = "J000001"
EMPTY_JOB_SEEKER_ID = "J999999"

EMPLOYER_ID = "C000001"
COMPANY_ID = EMPLOYER_ID

CONVERSATION_ID = f"{EMPLOYER_ID}_{JOB_SEEKER_ID}"
MESSAGE_ID = "TEST_JOBSEEKER_MESSAGE_001"

LATEST_MESSAGE = "Your interview has been scheduled"
LATEST_MESSAGE_TIME = "2099-07-30T10:00:00"


# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def context():
    return {
        "response": None,
    }


# ==========================================
# SESSION HELPERS
# ==========================================


def create_session(client, data):
    secret_key = None

    for middleware in app.user_middleware:
        if middleware.cls == SessionMiddleware:
            secret_key = middleware.kwargs["secret_key"]
            break

    if secret_key is None:
        raise RuntimeError("SessionMiddleware secret key not found")

    encoded_data = base64.b64encode(json.dumps(data).encode("utf-8"))

    signer = TimestampSigner(str(secret_key))
    cookie_value = signer.sign(encoded_data).decode("utf-8")

    client.cookies.set(
        "session",
        cookie_value,
    )


def set_job_seeker_session(client):
    create_session(
        client,
        {
            "user_type": "job_seeker",
            "role": "job_seeker",
            "user_id": JOB_SEEKER_ID,
            "applicant_id": JOB_SEEKER_ID,
            "job_seeker_id": JOB_SEEKER_ID,
            "jobSeekerId": JOB_SEEKER_ID,
        },
    )


def set_empty_job_seeker_session(client):
    create_session(
        client,
        {
            "user_type": "job_seeker",
            "role": "job_seeker",
            "user_id": EMPTY_JOB_SEEKER_ID,
            "applicant_id": EMPTY_JOB_SEEKER_ID,
            "job_seeker_id": EMPTY_JOB_SEEKER_ID,
            "jobSeekerId": EMPTY_JOB_SEEKER_ID,
        },
    )


# ==========================================
# TEST DATA CLEANUP
# ==========================================


def remove_test_data():
    db.collection("messages").document(MESSAGE_ID).delete()

    db.collection("conversations").document(CONVERSATION_ID).delete()

    db.collection("conversation").document(CONVERSATION_ID).delete()

    db.collection("company").document(COMPANY_ID).delete()

    db.collection("job_seeker").document(JOB_SEEKER_ID).delete()


@pytest.fixture(autouse=True)
def cleanup():
    remove_test_data()

    yield

    remove_test_data()


# ==========================================
# TEST DATA CREATION
# ==========================================


def insert_test_data():
    remove_test_data()

    db.collection("job_seeker").document(JOB_SEEKER_ID).set(
        {
            "applicantId": JOB_SEEKER_ID,
            "jobSeekerId": JOB_SEEKER_ID,
            "name": "James",
            "email": "james@test.com",
            "test": True,
        }
    )

    db.collection("company").document(COMPANY_ID).set(
        {
            "companyId": COMPANY_ID,
            "employerId": EMPLOYER_ID,
            "companyName": "ABC Company",
            "name": "ABC Company",
            "test": True,
        }
    )

    conversation_data = {
        "conversationId": CONVERSATION_ID,
        "employerId": EMPLOYER_ID,
        "companyId": COMPANY_ID,
        "jobSeekerId": JOB_SEEKER_ID,
        "applicantId": JOB_SEEKER_ID,
        "participants": [
            EMPLOYER_ID,
            JOB_SEEKER_ID,
        ],
        "lastMessage": LATEST_MESSAGE,
        "latestMessage": LATEST_MESSAGE,
        "lastMessageTime": LATEST_MESSAGE_TIME,
        "updatedAt": LATEST_MESSAGE_TIME,
        "timestamp": LATEST_MESSAGE_TIME,
        "test": True,
    }

    # Some implementations retrieve conversation summaries from
    # the "conversations" collection.
    db.collection("conversations").document(CONVERSATION_ID).set(conversation_data)

    # Some implementations use the singular collection name.
    db.collection("conversation").document(CONVERSATION_ID).set(conversation_data)

    # Other implementations construct the conversation list
    # directly from message documents.
    db.collection("messages").document(MESSAGE_ID).set(
        {
            "messageId": MESSAGE_ID,
            "conversationId": CONVERSATION_ID,
            "message": LATEST_MESSAGE,
            "content": LATEST_MESSAGE,
            "text": LATEST_MESSAGE,
            "time": LATEST_MESSAGE_TIME,
            "timestamp": LATEST_MESSAGE_TIME,
            "createdAt": LATEST_MESSAGE_TIME,
            "senderId": EMPLOYER_ID,
            "senderType": "employer",
            "receiverId": JOB_SEEKER_ID,
            "receiverType": "job_seeker",
            "employerId": EMPLOYER_ID,
            "companyId": COMPANY_ID,
            "jobSeekerId": JOB_SEEKER_ID,
            "applicantId": JOB_SEEKER_ID,
            "test": True,
        }
    )


# ==========================================
# GIVEN STEPS
# ==========================================


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


# ==========================================
# WHEN STEPS
# ==========================================


@when("the job seeker opens the Messages page")
def open_messages_page(context, client):
    context["response"] = client.get("/api/conversations")


@when("the conversations are loaded")
def load_conversations(context, client):
    context["response"] = client.get("/api/conversations")


# ==========================================
# THEN STEPS
# ==========================================


@then("the system should display the list of conversations with employers")
def verify_conversation_list(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list), data
    assert len(data) > 0, data

    conversation = next(
        (item for item in data if item.get("conversationId") == CONVERSATION_ID),
        None,
    )

    assert conversation is not None, data


@then("the system should display the latest message and conversation details")
def verify_latest_information(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list), data

    conversation = next(
        (item for item in data if item.get("conversationId") == CONVERSATION_ID),
        None,
    )

    assert conversation is not None, data
    assert conversation.get("lastMessage") == LATEST_MESSAGE
    assert conversation.get("employerId") == EMPLOYER_ID
    assert conversation.get("jobSeekerId") == JOB_SEEKER_ID


@then('the system should display a "No conversations available" message')
def verify_no_conversation(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text
    assert response.json() == []
