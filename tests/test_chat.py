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
# Helper Function
# --------------------------------------------------


def create_test_message(client):

    message_data = {
        "conversationId": "C000001_J000001",
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more about the job details?",
    }

    response = client.post("/api/messages", json=message_data)

    assert response.status_code == 200

    return response.json()


# --------------------------------------------------
# 1. Acceptance Test
# --------------------------------------------------


def test_job_seeker_send_message_success(client: TestClient):
    """
    Given the job seeker has opened a chat conversation with an employer
    When the job seeker enters and sends a message
    Then the message should appear in the chat conversation
    """

    response = create_test_message(client)

    assert response["message"] == "Message sent successfully"


# --------------------------------------------------
# 2. Verify Job Seeker Receives Employer Message
# --------------------------------------------------


def test_job_seeker_receive_employer_message(client: TestClient):
    """
    Given the employer has sent a message
    When the job seeker opens the chat conversation
    Then the employer's message should be displayed
    """

    conversation_id = "C000001_J000001"

    employer_message = {
        "conversationId": conversation_id,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your application has been reviewed.",
    }

    send_response = client.post("/api/messages", json=employer_message)

    assert send_response.status_code == 200

    response = client.get(f"/api/messages/{conversation_id}")

    assert response.status_code == 200

    messages = response.json()

    assert any(message["message"] == "Your application has been reviewed." for message in messages)


# --------------------------------------------------
# 3. Negative Test
# --------------------------------------------------


def test_invalid_chat_conversation(client: TestClient):
    """
    Given the chat conversation does not exist
    When the job seeker opens the conversation
    Then the system should return an empty conversation
    """

    response = client.get("/api/messages/INVALID_ID")

    assert response.status_code == 200

    assert response.json() == []


# --------------------------------------------------
# BDD Feature Loading
# --------------------------------------------------

scenarios("features/chat_job_seeker.feature")


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
# Job Seeker Sends Message
# --------------------------------------------------


@given("the job seeker has opened a chat conversation with an employer")
def open_chat(client, context):

    context.conversation_id = "C000001_J000001"


@when("the job seeker enters and sends a message")
def send_message(client, context):

    message_data = {
        "conversationId": context.conversation_id,
        "senderId": "J000001",
        "senderType": "job_seeker",
        "receiverId": "C000001",
        "message": "Can I know more about the job details?",
    }

    context.response = client.post("/api/messages", json=message_data)


@then("the message should appear in the chat conversation")
def verify_message(context):

    assert context.response.status_code == 200

    assert context.response.json()["message"] == "Message sent successfully"


# --------------------------------------------------
# Scenario 2:
# Job Seeker Receives Employer Message
# --------------------------------------------------


@given("the employer has sent a message")
def employer_send_message(client, context):

    context.conversation_id = "C000001_J000001"

    message_data = {
        "conversationId": context.conversation_id,
        "senderId": "C000001",
        "senderType": "employer",
        "receiverId": "J000001",
        "message": "Your application has been reviewed.",
    }

    response = client.post("/api/messages", json=message_data)

    assert response.status_code == 200


@when("the job seeker opens the chat conversation")
def open_conversation(client, context):

    context.response = client.get(f"/api/messages/{context.conversation_id}")


@then("the employer's message should be displayed")
def verify_employer_message(context):

    assert context.response.status_code == 200

    messages = context.response.json()

    assert any(message["message"] == "Your application has been reviewed." for message in messages)
