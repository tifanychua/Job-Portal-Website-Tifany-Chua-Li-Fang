from pytest_bdd import scenarios, given, when, then

from fastapi.testclient import TestClient

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


# Load feature file

scenarios("features/view_job_seeker_conversation_list.feature")


# =====================================
# Test Data Setup
# =====================================


def insert_test_data():

    # Employer information
    db.collection("company").document("C000001").set({"companyName": "ABC Company", "test": True})

    # Conversation message
    db.collection("messages").document("TEST_JOBSEEKER_MESSAGE_001").set(
        {
            "conversationId": "C000001_J000001",
            "message": "Your interview has been scheduled",
            "time": "2026-07-30T10:00:00",
            "senderId": "C000001",
            "senderType": "employer",
            "test": True,
        }
    )


def remove_test_data():

    collections = ["messages", "company"]

    for collection in collections:

        docs = db.collection(collection).stream()

        for doc in docs:

            data = doc.to_dict()

            if data.get("test"):

                doc.reference.delete()


# =====================================
# Given
# =====================================


@given("the job seeker is logged in and has existing conversations with employers")
def job_seeker_has_conversations():

    insert_test_data()


@given("the job seeker is viewing the conversation list")
def job_seeker_view_list():

    insert_test_data()


@given("the job seeker has no conversations with employers")
def job_seeker_no_conversations():

    remove_test_data()


# =====================================
# When
# =====================================


@when("the job seeker opens the Messages page")
def open_messages_page():

    response = client.get(
        "/api/conversations", params={"userId": "J000001", "userType": "job_seeker"}
    )

    return response


@when("the conversations are loaded")
def load_conversations():

    response = client.get(
        "/api/conversations", params={"userId": "J000001", "userType": "job_seeker"}
    )

    return response


# =====================================
# Then
# =====================================


@then("the system should display the list of conversations with employers")
def verify_conversation_list():

    response = client.get(
        "/api/conversations", params={"userId": "J000001", "userType": "job_seeker"}
    )

    print("\nRESPONSE:")
    print(response.text)

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0

    assert data[0]["conversationId"] == "C000001_J000001"


@then("the system should display the latest message and conversation details")
def verify_latest_information():

    response = client.get(
        "/api/conversations", params={"userId": "J000001", "userType": "job_seeker"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data[0]["lastMessage"] == ("Your interview has been scheduled")

    assert data[0]["employerId"] == "C000001"

    assert data[0]["jobSeekerId"] == "J000001"


@then('the system should display a "No conversations available" message')
def verify_no_conversation():

    response = client.get(
        "/api/conversations", params={"userId": "J999999", "userType": "job_seeker"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []

    remove_test_data()
