from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


# =====================================
# Insert test data
# =====================================


def create_test_messages():

    # clear old test data
    messages = db.collection("messages").stream()

    for msg in messages:
        data = msg.to_dict()

        if data.get("test"):
            msg.reference.delete()

    # Insert messages
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

    # Create job seekers
    db.collection("job_seeker").document("JS001").set({"name": "John Tan"})

    db.collection("job_seeker").document("JS002").set({"name": "Mary Lee"})


def delete_test_data():

    collections = ["messages", "job_seeker"]

    for collection in collections:

        docs = db.collection(collection).stream()

        for doc in docs:

            data = doc.to_dict()

            if data.get("test"):
                doc.reference.delete()


# =====================================
# Test 1
# View conversation list
# =====================================


def test_view_conversation_list():

    create_test_messages()

    response = client.get("/api/conversations", params={"userId": "EMP001", "userType": "employer"})

    print("\nRESPONSE:")
    print(response.text)

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0

    assert data[0]["conversationId"] in ["EMP001_JS001", "EMP001_JS002"]

    assert "name" in data[0]

    delete_test_data()


# =====================================
# Test 2
# Latest message information
# =====================================


def test_display_latest_conversation_information():

    create_test_messages()

    response = client.get("/api/conversations", params={"userId": "EMP001", "userType": "employer"})

    assert response.status_code == 200

    data = response.json()

    messages = [item["lastMessage"] for item in data]

    assert (
        "Thank you for arranging the interview" in messages
        or "I am available for the interview" in messages
    )

    delete_test_data()


# =====================================
# Test 3
# No conversation available
# =====================================


def test_no_conversations_available():

    # remove all test data first
    delete_test_data()

    response = client.get("/api/conversations", params={"userId": "EMP999", "userType": "employer"})

    assert response.status_code == 200

    data = response.json()

    assert data == []
