from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then

from job_portal_web.backend.main import app

# --------------------------------------------------
# Test Client Fixture
# --------------------------------------------------


@pytest.fixture
def client() -> TestClient:

    return TestClient(app)


# --------------------------------------------------
# Acceptance Test 1
# Employer Sends Message
# --------------------------------------------------


def test_employer_send_message_success(client: TestClient):
    """
    Given the employer has opened a chat conversation with a job seeker
    When the employer enters and sends a message
    Then the message should appear in the chat conversation
    """

    message_data = {
        "conversationId": "C000001_J000001",
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your interview has been scheduled.",
    }

    response = client.post("/api/messages", json=message_data)

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Message sent successfully"


# --------------------------------------------------
# Acceptance Test 2
# Employer Receives Job Seeker Message
# --------------------------------------------------


def test_employer_receive_job_seeker_message(client: TestClient):
    """
    Given the job seeker has sent a message
    When the employer opens the chat conversation
    Then the job seeker's message should be displayed
    """

    conversation_id = "C000001_J000001"

    job_seeker_message = {
        "conversationId": conversation_id,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more details about the interview?",
    }

    send_response = client.post("/api/messages", json=job_seeker_message)

    assert send_response.status_code == 200

    response = client.get(f"/api/messages/{conversation_id}")

    assert response.status_code == 200

    messages = response.json()

    assert any(
        message["message"] == "Can I know more details about the interview?" for message in messages
    )


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/employer_chat.feature")


# --------------------------------------------------
# BDD Context
# --------------------------------------------------


class Context:

    def __init__(self):

        self.response = None
        self.conversation_id = None


@pytest.fixture
def context():

    return Context()


# --------------------------------------------------
# Scenario 1:
# Employer Sends Message
# --------------------------------------------------


@given("the employer has opened a chat conversation with a job seeker")
def employer_open_chat(context):

    context.conversation_id = "C000001_J000001"


@when("the employer enters and sends a message")
def employer_send_message(client, context):

    message_data = {
        "conversationId": context.conversation_id,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your interview has been scheduled.",
    }

    context.response = client.post("/api/messages", json=message_data)


@then("the message should appear in the chat conversation")
def verify_employer_message(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Message sent successfully"


# --------------------------------------------------
# Scenario 2:
# Employer Receives Job Seeker Message
# --------------------------------------------------


@given("the job seeker has sent a message")
def job_seeker_send_message(client, context):

    context.conversation_id = "C000001_J000001"

    message_data = {
        "conversationId": context.conversation_id,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more details about the interview?",
    }

    client.post("/api/messages", json=message_data)


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
