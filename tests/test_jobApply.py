from fastapi.testclient import TestClient
from pytest_bdd import scenarios, given, when, then
import pytest

from main import app

scenarios("features/jobApply.feature")


@pytest.fixture
def client():

    return TestClient(app)


class Context:

    def __init__(self):

        self.response = None
        self.application_id = None


@pytest.fixture
def context():

    return Context()


# Scenario 1


@given("the job seeker is viewing a job posting")
def view_job():

    pass


@when("the job seeker submits an application")
def submit_application(client, context):

    job_id = "0ZWvjQqV3DMLANrbIRUs"

    context.response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )


@then("the application should be successfully created")
def verify_application_created(context):

    if context.response.status_code in [200, 201]:

        print("✅ SUCCESS: Job application created successfully")

        data = context.response.json()

        context.application_id = data.get("application_id")

    else:

        print("❌ FAILED:", context.response.status_code, context.response.text)

    assert context.response.status_code in [200, 201]


# Scenario 2


@given("the job seeker has submitted a job application")
def submitted_application(client, context):

    job_id = "0ZWvjQqV3DMLANrbIRUs"

    response = client.post(
        f"/jobs/{job_id}/apply",
        data={"applicant_id": "J000001"},
        files={"resume": ("resume.pdf", b"test resume content", "application/pdf")},
    )

    assert response.status_code in [200, 201]

    data = response.json()

    context.application_id = data.get("application_id")


@when("the application is processed")
def process_application(client, context):

    context.response = client.get(f"/application/{context.application_id}")


@then("the application details should be stored in the database")
def verify_saved(context):

    if context.response.status_code == 200:

        print("✅ SUCCESS: Application information stored in database")

    else:

        print("❌ FAILED: Application not found")

    assert context.response.status_code == 200
