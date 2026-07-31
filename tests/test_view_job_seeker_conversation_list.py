import json
import base64

from pytest_bdd import scenarios, given, when, then

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.main import app
from job_portal_web.backend.database import db

client = TestClient(app)


# Load feature file
scenarios("features/view_job_seeker_conversation_list.feature")


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

        raise Exception("SessionMiddleware secret key not found")

    json_data = json.dumps(data)

    encoded_data = base64.b64encode(json_data.encode()).decode()

    signer = TimestampSigner(secret_key)

    cookie_value = signer.sign(encoded_data).decode()

    client.cookies.set("session", cookie_value)


def set_job_seeker_session():

    create_session(
        {
            "user_type": "job_seeker",
            "applicant_id": "J000001",
        }
    )


def set_empty_job_seeker_session():

    create_session(
        {
            "user_type": "job_seeker",
            "applicant_id": "J999999",
        }
    )


# =====================================
# Test Data Setup
# =====================================


def insert_test_data():

    remove_test_data()

    # Remove existing conversation
    # Prevent old Firestore messages affecting latest message

    messages = db.collection("messages").stream()

    for msg in messages:

        data = msg.to_dict()

        if data.get("conversationId") == "C000001_J000001":

            msg.reference.delete()

    # Employer information

    db.collection("company").document("C000001").set(
        {
            "companyName": "ABC Company",
            "test": True,
        }
    )

    # Conversation message

    db.collection("messages").document("TEST_JOBSEEKER_MESSAGE_001").set(
        {
            "conversationId": "C000001_J000001",
            "message": "Your interview has been scheduled",
            "time": "2099-07-30T10:00:00",
            "senderId": "C000001",
            "senderType": "employer",
            "test": True,
        }
    )


# =====================================
# Remove Test Data
# =====================================


def remove_test_data():

    collections = [
        "messages",
        "company",
    ]

    for collection in collections:

        docs = db.collection(collection).stream()

        for doc in docs:

            data = doc.to_dict()

            if data.get("test") is True:

                doc.reference.delete()


# =====================================
# Given
# =====================================


@given("the job seeker is logged in and has existing conversations with employers")
def job_seeker_has_conversations():

    insert_test_data()

    set_job_seeker_session()


@given("the job seeker is viewing the conversation list")
def job_seeker_view_list():

    insert_test_data()

    set_job_seeker_session()


@given("the job seeker has no conversations with employers")
def job_seeker_no_conversations():

    remove_test_data()

    set_empty_job_seeker_session()


# =====================================
# When
# =====================================


@when("the job seeker opens the Messages page")
def open_messages_page():

    return client.get("/api/conversations")


@when("the conversations are loaded")
def load_conversations():

    return client.get("/api/conversations")


# =====================================
# Then
# =====================================


@then("the system should display the list of conversations with employers")
def verify_conversation_list():

    response = client.get("/api/conversations")

    print("\nRESPONSE:")
    print(response.text)

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0

    assert data[0]["conversationId"] == "C000001_J000001"


@then("the system should display the latest message and conversation details")
def verify_latest_information():

    response = client.get("/api/conversations")

    assert response.status_code == 200

    data = response.json()

    assert len(data) > 0

    assert data[0]["lastMessage"] == "Your interview has been scheduled"

    assert data[0]["employerId"] == "C000001"

    assert data[0]["jobSeekerId"] == "J000001"


@then('the system should display a "No conversations available" message')
def verify_no_conversation():

    response = client.get("/api/conversations")

    assert response.status_code == 200

    data = response.json()

    assert data == []

    remove_test_data()
