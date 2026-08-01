import json
import base64

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


# =====================================
# Session Helper
# =====================================


def create_session(data):

    secret_key = None

    for middleware in app.user_middleware:

        if middleware.cls == SessionMiddleware:

            secret_key = middleware.kwargs["secret_key"]
            break

    if secret_key is None:
        raise Exception("SessionMiddleware secret_key not found")

    json_data = json.dumps(data)

    encoded_data = base64.b64encode(json_data.encode()).decode()

    signer = TimestampSigner(secret_key)

    cookie_value = signer.sign(encoded_data).decode()

    client.cookies.set("session", cookie_value)


def set_employer_session():

    create_session(
        {
            "user_type": "employer",
            "company_id": "EMP001",
        }
    )


def set_empty_employer_session():

    create_session(
        {
            "user_type": "employer",
            "company_id": "EMP999",
        }
    )


# =====================================
# Insert Test Data
# =====================================


def create_test_messages():

    delete_test_data()

    # Message 1

    db.collection("messages").document("TEST_MESSAGE_001").set(
        {
            "conversationId": "EMP001_JS001",
            "message": "Thank you for arranging the interview",
            "time": "2026-07-30T10:00:00",
            "senderId": "EMP001",
            "senderType": "employer",
            "test": True,
        }
    )

    # Message 2

    db.collection("messages").document("TEST_MESSAGE_002").set(
        {
            "conversationId": "EMP001_JS002",
            "message": "I am available for the interview",
            "time": "2026-07-30T11:00:00",
            "senderId": "JS002",
            "senderType": "job_seeker",
            "test": True,
        }
    )

    # Job seeker data

    db.collection("job_seeker").document("JS001").set(
        {
            "name": "John Tan",
            "test": True,
        }
    )

    db.collection("job_seeker").document("JS002").set(
        {
            "name": "Mary Lee",
            "test": True,
        }
    )


# =====================================
# Delete Test Data
# =====================================


def delete_test_data():

    collections = [
        "messages",
        "job_seeker",
    ]

    for collection in collections:

        docs = db.collection(collection).stream()

        for doc in docs:

            data = doc.to_dict()

            if data.get("test") is True:

                doc.reference.delete()


# =====================================
# Test 1
# View Conversation List
# =====================================


def test_view_conversation_list():

    try:

        create_test_messages()

        set_employer_session()

        response = client.get("/api/conversations")

        print("\nRESPONSE:")
        print(response.text)

        assert response.status_code == 200

        data = response.json()

        assert len(data) > 0

        conversation_ids = [item["conversationId"] for item in data]

        assert "EMP001_JS001" in conversation_ids or "EMP001_JS002" in conversation_ids

        assert "name" in data[0]

    finally:

        delete_test_data()


# =====================================
# Test 2
# Latest Message Information
# =====================================


def test_display_latest_conversation_information():

    try:

        create_test_messages()

        set_employer_session()

        response = client.get("/api/conversations")

        assert response.status_code == 200

        data = response.json()

        latest_messages = [item["lastMessage"] for item in data]

        assert (
            "Thank you for arranging the interview" in latest_messages
            or "I am available for the interview" in latest_messages
        )

    finally:

        delete_test_data()


# =====================================
# Test 3
# No Conversation Available
# =====================================


def test_no_conversations_available():

    try:

        delete_test_data()

        set_empty_employer_session()

        response = client.get("/api/conversations")

        assert response.status_code == 200

        data = response.json()

        assert data == []

    finally:

        delete_test_data()
