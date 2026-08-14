import base64
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app


# ==========================================
# Feature File
# ==========================================

scenarios(
    "features/view_job_seeker_conversation_list.feature"
)


# ==========================================
# Unique Test Constants
# ==========================================

# Unique values prevent parallel GitHub Actions jobs
# from deleting each other's Firestore test data.
RUN_ID = uuid4().hex[:12].upper()

JOB_SEEKER_ID = f"J{RUN_ID}"
EMPTY_JOB_SEEKER_ID = f"JE{RUN_ID}"

EMPLOYER_ID = f"C{RUN_ID}"
COMPANY_ID = EMPLOYER_ID

# The API expects exactly one underscore because it uses:
# conversation_id.split("_")
CONVERSATION_ID = (
    f"{EMPLOYER_ID}_{JOB_SEEKER_ID}"
)

MESSAGE_ID = f"TESTMSG{RUN_ID}"

LATEST_MESSAGE = "Your interview has been scheduled"
LATEST_MESSAGE_TIME = "2099-07-30T10:00:00+00:00"


# ==========================================
# Fixtures
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
# Session Helpers
# ==========================================

def create_session(client, data):
    secret_key = None

    for middleware in app.user_middleware:
        if middleware.cls == SessionMiddleware:
            secret_key = middleware.kwargs["secret_key"]
            break

    if secret_key is None:
        raise RuntimeError(
            "SessionMiddleware secret key not found"
        )

    encoded_data = base64.b64encode(
        json.dumps(data).encode("utf-8")
    )

    signer = TimestampSigner(str(secret_key))

    cookie_value = signer.sign(
        encoded_data
    ).decode("utf-8")

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
# Test Data Cleanup
# ==========================================

def remove_test_data():
    db.collection(
        "messages"
    ).document(
        MESSAGE_ID
    ).delete()

    db.collection(
        "conversations"
    ).document(
        CONVERSATION_ID
    ).delete()

    db.collection(
        "conversation"
    ).document(
        CONVERSATION_ID
    ).delete()

    db.collection(
        "company"
    ).document(
        COMPANY_ID
    ).delete()

    db.collection(
        "job_seeker"
    ).document(
        JOB_SEEKER_ID
    ).delete()


@pytest.fixture(autouse=True)
def cleanup():
    remove_test_data()

    yield

    remove_test_data()


# ==========================================
# Test Data Creation
# ==========================================

def insert_test_data():
    remove_test_data()

    # Create the test job seeker.
    db.collection(
        "job_seeker"
    ).document(
        JOB_SEEKER_ID
    ).set(
        {
            "applicantId": JOB_SEEKER_ID,
            "jobSeekerId": JOB_SEEKER_ID,
            "name": "James",
            "email": f"{JOB_SEEKER_ID.lower()}@test.com",
            "test": True,
        }
    )

    # Create the test company.
    db.collection(
        "company"
    ).document(
        COMPANY_ID
    ).set(
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

    # Support implementations using the plural collection.
    db.collection(
        "conversations"
    ).document(
        CONVERSATION_ID
    ).set(
        conversation_data
    )

    # Support implementations using the singular collection.
    db.collection(
        "conversation"
    ).document(
        CONVERSATION_ID
    ).set(
        conversation_data
    )

    # The current API constructs the conversation list
    # from the messages collection.
    db.collection(
        "messages"
    ).document(
        MESSAGE_ID
    ).set(
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

    # Confirm the test message was inserted.
    message_snapshot = (
        db.collection("messages")
        .document(MESSAGE_ID)
        .get()
    )

    assert message_snapshot.exists, (
        "The test message was not inserted into Firestore."
    )

    inserted_message = message_snapshot.to_dict() or {}

    assert (
        inserted_message.get("conversationId")
        == CONVERSATION_ID
    )


# ==========================================
# Given Steps
# ==========================================

@given(
    "the job seeker is logged in and has "
    "existing conversations with employers"
)
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
# When Steps
# ==========================================

@when("the job seeker opens the Messages page")
def open_messages_page(context, client):
    context["response"] = client.get(
        "/api/conversations"
    )


@when("the conversations are loaded")
def load_conversations(context, client):
    context["response"] = client.get(
        "/api/conversations"
    )


# ==========================================
# Then Steps
# ==========================================

@then(
    "the system should display the list of "
    "conversations with employers"
)
def verify_conversation_list(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list), data

    conversation = next(
        (
            item
            for item in data
            if item.get("conversationId")
            == CONVERSATION_ID
        ),
        None,
    )

    assert conversation is not None, (
        f"Expected conversation {CONVERSATION_ID}, "
        f"but received: {data}"
    )


@then(
    "the system should display the latest message "
    "and conversation details"
)
def verify_latest_information(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list), data

    conversation = next(
        (
            item
            for item in data
            if item.get("conversationId")
            == CONVERSATION_ID
        ),
        None,
    )

    assert conversation is not None, data

    assert (
        conversation.get("lastMessage")
        == LATEST_MESSAGE
    )

    assert (
        conversation.get("employerId")
        == EMPLOYER_ID
    )

    assert (
        conversation.get("jobSeekerId")
        == JOB_SEEKER_ID
    )

    assert (
        conversation.get("name")
        == "ABC Company"
    )


@then(
    'the system should display a '
    '"No conversations available" message'
)
def verify_no_conversation(context):
    response = context["response"]

    assert response is not None
    assert response.status_code == 200, response.text
    assert response.json() == []