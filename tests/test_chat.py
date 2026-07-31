from __future__ import annotations

import pytest

from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

# ==================================================
# CLIENT
# ==================================================


@pytest.fixture
def client() -> TestClient:

    return TestClient(app)


# ==================================================
# TEST DATA
# ==================================================

TEST_CONVERSATION_ID = "TEST_CONVERSATION_001"


def delete_test_messages():

    messages = (
        db.collection("messages").where("conversationId", "==", TEST_CONVERSATION_ID).stream()
    )

    for message in messages:
        message.reference.delete()


@pytest.fixture(autouse=True)
def cleanup():

    delete_test_messages()

    yield

    delete_test_messages()


# ==================================================
# HELPER
# ==================================================


def create_test_message(client):

    message_data = {
        "conversationId": TEST_CONVERSATION_ID,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more about the job details?",
    }

    response = client.post("/api/messages", json=message_data)

    assert response.status_code == 200

    return response.json()


# ==================================================
# TEST 1
# ==================================================


def test_job_seeker_send_message_success(client):
    """
    Given the job seeker has opened a chat conversation with an employer

    When the job seeker sends a message

    Then the message should appear successfully
    """

    response = create_test_message(client)

    assert response["message"] == ("Message sent successfully")


# ==================================================
# TEST 2
# ==================================================


def test_job_seeker_receive_employer_message(client):
    """
    Given the employer has sent a message

    When the job seeker opens the conversation

    Then employer message should be displayed
    """

    employer_message = {
        "conversationId": TEST_CONVERSATION_ID,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your application has been reviewed.",
    }

    response = client.post("/api/messages", json=employer_message)

    assert response.status_code == 200

    messages_response = client.get(f"/api/messages/{TEST_CONVERSATION_ID}")

    assert messages_response.status_code == 200

    messages = messages_response.json()

    assert any(message["message"] == "Your application has been reviewed." for message in messages)


# ==================================================
# TEST 3 NEGATIVE
# ==================================================


def test_invalid_chat_conversation(client):
    """
    Given the chat conversation does not exist

    When the job seeker opens the conversation

    Then an empty list should be returned
    """

    response = client.get("/api/messages/INVALID_CONVERSATION_ID")

    assert response.status_code == 200

    assert response.json() == []


# ==================================================
# BDD FEATURE
# ==================================================

scenarios("features/chat_job_seeker.feature")


# ==================================================
# CONTEXT
# ==================================================


class Context:

    def __init__(self):

        self.response = None

        self.conversation_id = TEST_CONVERSATION_ID


@pytest.fixture
def context():

    return Context()


# ==================================================
# BDD SCENARIO 1
# ==================================================


@given("the job seeker has opened a chat conversation with an employer")
def open_chat(context):

    context.conversation_id = TEST_CONVERSATION_ID


@when("the job seeker enters and sends a message")
def send_message(client, context):

    data = {
        "conversationId": context.conversation_id,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more about the job details?",
    }

    context.response = client.post("/api/messages", json=data)


@then("the message should appear in the chat conversation")
def verify_message(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == ("Message sent successfully")


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the employer has sent a message")
def employer_send_message(client, context):

    data = {
        "conversationId": context.conversation_id,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your application has been reviewed.",
    }

    response = client.post("/api/messages", json=data)

    assert response.status_code == 200


@when("the job seeker opens the chat conversation")
def open_conversation(client, context):

    context.response = client.get(f"/api/messages/{context.conversation_id}")


@then("the employer's message should be displayed")
def verify_employer_message(context):

    assert context.response.status_code == 200

    messages = context.response.json()

    assert any(message["message"] == "Your application has been reviewed." for message in messages)
