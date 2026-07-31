from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from job_portal_web.backend.main import app
from job_portal_web.backend import job_application


# ==================================================
# Fake Login
# ==================================================

APPLICATION_ID = "FAKE_APPLICATION"


@pytest.fixture(autouse=True)
def fake_login(monkeypatch):

    def fake_current_user(request):

        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = "J000001"

        return (
            "J000001",
            {
                "uid": "J000001",
                "full_name": "Test User",
                "headline": "Software Engineer",
                "photo": "user.png",
            },
        )

    monkeypatch.setattr(
        job_application,
        "_get_current_job_seeker",
        fake_current_user,
    )


# ==================================================
# Fake Firestore
# ==================================================

class FakeSnapshot:

    def __init__(self, data=None, exists=True):
        self._data = data or {}
        self.exists = exists
        self.id = APPLICATION_ID

    def to_dict(self):
        return self._data


class FakeDocument:

    def __init__(self):

        self.data = {
            "job_id": "JOB001",
            "job_seeker_id": "J000001",
            "status": "Submitted",
            "resume_filename": "resume.pdf",
            "resume_path": "resume.pdf",
            "cover_letter": "Test Cover Letter",
            "answers": {},
            "created_at": None,
            "updated_at": None,
        }

    def get(self):
        return FakeSnapshot(self.data, True)

    def update(self, values):
        self.data.update(values)

    def set(self, values):
        self.data = values

    def delete(self):
        self.data = {}

    @property
    def id(self):
        return APPLICATION_ID


class FakeCollection:

    def __init__(self):
        self.documents = {
            APPLICATION_ID: FakeDocument()
        }

    def document(self, doc_id):

        if doc_id not in self.documents:
            self.documents[doc_id] = FakeDocument()

        return self.documents[doc_id]

    def where(self, *args, **kwargs):
        return self

    def stream(self):

        snapshots = []

        for doc_id, doc in self.documents.items():

            snap = FakeSnapshot(doc.data, True)
            snap.id = doc_id

            snapshots.append(snap)

        return snapshots


class FakeDB:

    def __init__(self):

        self.collections = {
            "application": FakeCollection(),
            "job_list": FakeCollection(),
            "job_seeker": FakeCollection(),
            "company": FakeCollection(),
        }

    def collection(self, name):

        if name not in self.collections:
            self.collections[name] = FakeCollection()

        return self.collections[name]


class FakeBlob:

    def generate_signed_url(self, **kwargs):
        return "https://example.com/resume.pdf"


class FakeBucket:

    def blob(self, path):
        return FakeBlob()


# ==================================================
# Fixtures
# ==================================================

@pytest.fixture(autouse=True)
def fake_firestore(monkeypatch):

    monkeypatch.setattr(
        job_application,
        "db",
        FakeDB(),
    )

    monkeypatch.setattr(
        job_application,
        "bucket",
        FakeBucket(),
    )
    
# ==================================================
# Fake Backend Helpers
# ==================================================

@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):

    monkeypatch.setattr(
        job_application,
        "_get_job_summary",
        lambda job_id: {
            "id": "JOB001",
            "job_title": "QA Automation Engineer",
            "company_id": "COMP001",
            "companyName": "TARUMT",
            "location": "Kuala Lumpur",
            "employment_type": "Full-time",
            "category": "IT",
            "company_verified": True,
            "company_logo": "logo.png",
        },
    )

    monkeypatch.setattr(
        job_application,
        "_find_company",
        lambda company_id: {
            "companyName": "TARUMT",
            "verified": True,
            "logo": "logo.png",
        },
    )

    monkeypatch.setattr(
        job_application,
        "_get_screening_questions",
        lambda job: [],
    )

    monkeypatch.setattr(
        job_application,
        "_get_resume_url",
        lambda path: "https://example.com/resume.pdf",
    )

    monkeypatch.setattr(
        job_application,
        "_format_timestamp",
        lambda ts: "July 31, 2026",
    )


# ==================================================
# Test Client Fixture
# ==================================================

@pytest.fixture
def client():
    return TestClient(app)


# ==================================================
# Acceptance Tests
# ==================================================

def test_cancel_application_success(client):
    """
    Acceptance Test:
    Job seeker withdraws a submitted application.
    """

    response = client.post(
        f"/application/{APPLICATION_ID}/cancel"
    )

    if response.status_code == 200:
        print("✅ SUCCESS: Application withdrawn successfully")
    else:
        print("❌ FAILED:", response.status_code)
        print(response.text)

    assert response.status_code == 200
    assert "Cancelled" in response.text


def test_cancel_application_saved(client):
    """
    Acceptance Test:
    Withdrawn application status is saved.
    """

    client.post(
        f"/application/{APPLICATION_ID}/cancel"
    )

    response = client.get(
        f"/application/{APPLICATION_ID}"
    )

    if response.status_code == 200:
        print("✅ SUCCESS: Withdrawal saved")
    else:
        print("❌ FAILED:", response.status_code)
        print(response.text)

    assert response.status_code == 200
    assert "Cancelled" in response.text


def test_cancel_already_cancelled_application(client):
    """
    Negative Acceptance Test:
    Reject duplicate withdrawal.
    """

    client.post(
        f"/application/{APPLICATION_ID}/cancel"
    )

    response = client.post(
        f"/application/{APPLICATION_ID}/cancel"
    )

    if response.status_code == 409:
        print("✅ SUCCESS: Duplicate cancellation rejected")
    else:
        print("❌ FAILED:", response.status_code)
        print(response.text)

    assert response.status_code == 409
    
    
# ==================================================
# Load BDD Feature
# ==================================================

scenarios("features/cancelApplication.feature")


# ==================================================
# BDD Context
# ==================================================

class Context:

    def __init__(self):

        self.response = None
        self.application_id = APPLICATION_ID


@pytest.fixture
def context():

    return Context()


# ==================================================
# Scenario 1
# Job seeker withdraws a submitted application
# ==================================================

@given("the job seeker has submitted a job application")
def submitted_application():
    """
    Fake application already exists in Fake Firestore.
    """
    pass


@when("the job seeker selects the withdraw application option")
def withdraw_application(client, context):

    context.response = client.post(
        f"/application/{context.application_id}/cancel"
    )


# ==================================================
# Scenario 2
# Save withdrawn application status
# ==================================================

@given("the job seeker has withdrawn an application")
def withdrawn_application(client, context):

    client.post(
        f"/application/{context.application_id}/cancel"
    )


@when("the withdrawal request is processed")
def process_request(client, context):

    context.response = client.get(
        f"/application/{context.application_id}"
    )
    
# ==================================================
# Scenario 1 Verification
# ==================================================

@then('the application status should be updated to "Cancelled"')
def verify_cancelled(client, context):

    assert context.response is not None

    assert context.response.status_code == 200

    assert "Cancelled" in context.response.text

    print("✅ SUCCESS: Application status updated to Cancelled")


# ==================================================
# Scenario 2 Verification
# ==================================================

@then("the updated application status should be saved in the database")
def verify_database(context):

    assert context.response is not None

    assert context.response.status_code == 200

    assert "Cancelled" in context.response.text

    print("✅ SUCCESS: Updated application status saved in database")