from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

# ==================================================
# TEST CLIENT
# ==================================================


@pytest.fixture
def client() -> TestClient:

    return TestClient(app)


# ==================================================
# TEST DATA
# ==================================================

TEST_CONVERSATION_ID = "TEST_EMPLOYER_CHAT_001"


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


def send_message(client, sender_id, sender_type, receiver_id, message):

    data = {
        "conversationId": TEST_CONVERSATION_ID,
        "senderId": sender_id,
        "senderType": sender_type,
        "receiverId": receiver_id,
        "message": message,
    }

    return client.post("/api/messages", json=data)


# ==================================================
# ACCEPTANCE TEST 1
# ==================================================


def test_employer_send_message_success(client):

    response = send_message(
        client, "C000001", "employer", "J000001", "Your interview has been scheduled."
    )

    assert response.status_code == 200

    assert response.json()["message"] == "Message sent successfully"


# ==================================================
# ACCEPTANCE TEST 2
# ==================================================


def test_employer_receive_job_seeker_message(client):

    response = send_message(
        client,
        "J000001",
        "job_seeker",
        "C000001",
        "Can I know more details about the interview?",
    )

    assert response.status_code == 200

    response = client.get(f"/api/messages/{TEST_CONVERSATION_ID}")

    assert response.status_code == 200

    messages = response.json()

    assert any(
        message["message"] == "Can I know more details about the interview?" for message in messages
    )


# ==================================================
# NEGATIVE TEST
# ==================================================


def test_invalid_chat_conversation(client):

    response = client.get("/api/messages/INVALID_CONVERSATION")

    assert response.status_code == 200

    assert response.json() == []


# ==================================================
# BDD FEATURE
# ==================================================

scenarios("features/employer_chat.feature")


# ==================================================
# BDD CONTEXT
# ==================================================


class Context:
    def __init__(self):

        self.response = None

        self.conversation_id = None


@pytest.fixture
def context():

    return Context()


# ==================================================
# BDD SCENARIO 1
# ==================================================


@given("the employer has opened a chat conversation with a job seeker")
def employer_open_chat(context):

    context.conversation_id = TEST_CONVERSATION_ID


@when("the employer enters and sends a message")
def employer_send_message(client, context):

    data = {
        "conversationId": context.conversation_id,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your interview has been scheduled.",
    }

    context.response = client.post("/api/messages", json=data)


@then("the message should appear in the chat conversation")
def verify_employer_message(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Message sent successfully"


# ==================================================
# BDD SCENARIO 2
# ==================================================


@given("the job seeker has sent a message")
def job_seeker_send_message(client, context):

    context.conversation_id = TEST_CONVERSATION_ID

    data = {
        "conversationId": context.conversation_id,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more details about the interview?",
    }

    response = client.post("/api/messages", json=data)

    assert response.status_code == 200


@when("the employer opens the chat conversation")
def employer_open_conversation(client, context):

    context.response = client.get(f"/api/messages/{context.conversation_id}")


@then("the job seeker's message should be displayed")
def verify_job_seeker_message(context):

    assert context.response.status_code == 200

    messages = context.response.json()

    assert any(
        message["message"] == "Can I know more details about the interview?" for message in messages
    )
