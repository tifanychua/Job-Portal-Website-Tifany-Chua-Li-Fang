import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD ACTUAL JOB PUBLISH MODULE
# ============================================================


def load_job_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if (
            "async def publish_job_confirm(" in text
            and "CREDIT_RULES" in text
            and "credit_history" in text
        ):

            module_name = "job_portal_web.backend.routes." + path.stem

            # Prevent real DB use during import
            fake_database = types.ModuleType("job_portal_web.backend.database")

            fake_database.db = None

            original_database = sys.modules.get("job_portal_web.backend.database")

            sys.modules["job_portal_web.backend.database"] = fake_database

            try:

                return importlib.import_module(module_name)

            finally:

                if original_database is not None:

                    sys.modules["job_portal_web.backend.database"] = original_database

                else:

                    sys.modules.pop(
                        "job_portal_web.backend.database",
                        None,
                    )

    raise ImportError("Could not find publish_job_confirm().")


job_module = load_job_module()


# ============================================================
# FEATURE
# ============================================================

scenarios("features/deductJobPostingCredit.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

JOB_TITLE = "Software Engineer"


# ============================================================
# FAKE FIRESTORE INCREMENT
# ============================================================


class FakeIncrement:

    def __init__(
        self,
        amount,
    ):

        self.amount = amount


# ============================================================
# FAKE DOCUMENT SNAPSHOT
# ============================================================


class FakeDocumentSnapshot:

    def __init__(
        self,
        document_id,
        data=None,
        exists=True,
    ):

        self.id = document_id

        self._data = data if data is not None else {}

        self.exists = exists

    def to_dict(self):

        return dict(self._data)


# ============================================================
# FAKE DOCUMENT REFERENCE
# ============================================================


class FakeDocumentReference:

    def __init__(
        self,
        collection,
        document_id,
    ):

        self.collection = collection

        self.id = document_id

    def get(self):

        data = self.collection.documents.get(self.id)

        return FakeDocumentSnapshot(
            self.id,
            data,
            exists=(data is not None),
        )

    def set(
        self,
        data,
    ):

        self.collection.documents[self.id] = dict(data)

    def update(
        self,
        values,
    ):

        document = self.collection.documents.setdefault(
            self.id,
            {},
        )

        for (
            key,
            value,
        ) in values.items():

            if isinstance(
                value,
                FakeIncrement,
            ):

                current = (
                    document.get(
                        key,
                        0,
                    )
                    or 0
                )

                document[key] = current + value.amount

            else:

                document[key] = value


# ============================================================
# FAKE COLLECTION
# ============================================================


class FakeCollection:

    def __init__(
        self,
        documents=None,
        prefix="DOC",
    ):

        self.documents = dict(documents or {})

        self.prefix = prefix

        self.counter = 0

        self.added = []

    def document(
        self,
        document_id=None,
    ):

        if document_id is None:

            self.counter += 1

            document_id = f"{self.prefix}" f"{self.counter:03d}"

        return FakeDocumentReference(
            self,
            document_id,
        )

    def add(
        self,
        data,
    ):

        self.counter += 1

        document_id = f"{self.prefix}" f"{self.counter:03d}"

        saved = dict(data)

        self.documents[document_id] = saved

        self.added.append(saved)

        return (
            FakeDocumentReference(
                self,
                document_id,
            ),
            None,
        )


# ============================================================
# FAKE DATABASE
# ============================================================


class FakeDB:

    def __init__(
        self,
        available_credit,
    ):

        self.collections = {
            "company": FakeCollection(
                {
                    COMPANY_ID: {
                        "companyName": "ABC Technology Sdn Bhd",
                        "available_credit": available_credit,
                        "used_credit": 0,
                    }
                },
                prefix="COMPANY",
            ),
            "job_list": FakeCollection(prefix="JOB"),
            "credit_history": FakeCollection(prefix="CREDIT"),
        }

    def collection(
        self,
        name,
    ):

        return self.collections[name]


# ============================================================
# FAKE REQUEST
# ============================================================


class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
            "job": {
                "job_title": JOB_TITLE,
                "category": "Information Technology",
                "employment_type": "Full-time",
                "position": "Software Engineer",
                "vacancies": 1,
                "location": "Kuala Lumpur",
                "job_desc": "Develop software applications.",
                "job_responsibility": "Develop and maintain systems.",
                "job_req": "Python",
                "salaryType": "fixed",
                "salary": "5000",
                "benefits": [],
            },
        }


# ============================================================
# CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.db = None

        self.request = None

        self.response = None

        self.credit_history = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# INSTALL TEST DATABASE
# ============================================================


def install_db(
    monkeypatch,
    context,
    available_credit,
):

    context.db = FakeDB(available_credit=available_credit)

    context.request = FakeRequest()

    monkeypatch.setattr(
        job_module,
        "db",
        context.db,
    )

    monkeypatch.setattr(
        job_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    # Firestore helpers used by production code
    monkeypatch.setattr(
        job_module.firestore,
        "Increment",
        lambda amount: FakeIncrement(amount),
    )

    monkeypatch.setattr(
        job_module.firestore,
        "SERVER_TIMESTAMP",
        "TEST_TIMESTAMP",
    )


# ============================================================
# HELPER
# ============================================================


def publish_job(
    context,
):

    context.response = asyncio.run(
        job_module.publish_job_confirm(
            request=context.request,
            # 30 days = exactly 1 credit
            duration=30,
            # Backend calculates its own
            # required credit from duration.
            credit_used=1,
        )
    )


def company_data(
    context,
):

    return context.db.collection("company").documents[COMPANY_ID]


def published_jobs(
    context,
):

    return list(context.db.collection("job_list").documents.values())


def credit_records(
    context,
):

    return list(context.db.collection("credit_history").documents.values())


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_one_credit_is_deducted_after_job_publish(
    monkeypatch,
):

    context = Context()

    install_db(
        monkeypatch,
        context,
        available_credit=5,
    )

    publish_job(context)

    company = company_data(context)

    assert company["available_credit"] == 4

    assert company["used_credit"] == 1

    jobs = published_jobs(context)

    assert len(jobs) == 1

    assert jobs[0]["status"] == "Active"

    assert jobs[0]["credit_used"] == 1


def test_zero_credit_prevents_job_publication(
    monkeypatch,
):

    context = Context()

    install_db(
        monkeypatch,
        context,
        available_credit=0,
    )

    publish_job(context)

    company = company_data(context)

    # No credit deduction
    assert company["available_credit"] == 0

    assert company["used_credit"] == 0

    jobs = published_jobs(context)

    assert len(jobs) == 1

    # Backend saves it as Draft
    assert jobs[0]["status"] == "Draft"

    assert jobs[0]["credit_used"] == 0

    assert context.response.status_code == 303

    assert "error=insufficient_credit" in context.response.headers["location"]


def test_credit_history_created_after_job_publish(
    monkeypatch,
):

    context = Context()

    install_db(
        monkeypatch,
        context,
        available_credit=5,
    )

    publish_job(context)

    records = credit_records(context)

    assert len(records) == 1

    record = records[0]

    assert record["company_id"] == COMPANY_ID

    assert record["type"] == "JOB_POST"

    assert record["credit"] == -1

    assert record["balance"] == 4

    assert JOB_TITLE in record["description"]

    assert record["date"] is not None

    assert record["reference"] != ""


# ============================================================
# BDD GIVEN
# ============================================================


@given("the employer has available job posting credits")
def employer_has_credit(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
        available_credit=5,
    )


@given("the employer has no available job posting credits")
def employer_has_no_credit(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
        available_credit=0,
    )


@given("one credit has been deducted after a job post is published")
def credit_already_deducted(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
        available_credit=5,
    )

    publish_job(context)

    assert company_data(context)["available_credit"] == 4


# ============================================================
# BDD WHEN
# ============================================================


@when("the employer successfully publishes a job post")
def employer_publishes_job(
    context,
):

    publish_job(context)


@when("the employer attempts to publish a job post")
def employer_attempts_publish(
    context,
):

    publish_job(context)


@when("the admin views the credit usage records")
def admin_views_credit_records(
    context,
):

    records = credit_records(context)

    assert len(records) > 0

    context.credit_history = records


# ============================================================
# BDD THEN
# ============================================================


@then("the system should deduct one credit from the employer's credit balance")
def one_credit_deducted(
    context,
):

    company = company_data(context)

    # Started with 5
    assert company["available_credit"] == 4

    assert company["used_credit"] == 1

    jobs = published_jobs(context)

    assert len(jobs) == 1

    assert jobs[0]["status"] == "Active"

    assert jobs[0]["credit_used"] == 1

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/manage-jobs?success=posted"


@then(
    "the system should prevent the publication and display a message indicating insufficient credits"
)
def insufficient_credit_prevents_publish(
    context,
):

    company = company_data(context)

    # Balance remains zero
    assert company["available_credit"] == 0

    assert company["used_credit"] == 0

    jobs = published_jobs(context)

    assert len(jobs) == 1

    # Your backend preserves the
    # unsuccessful publication as Draft.
    assert jobs[0]["status"] == "Draft"

    assert jobs[0]["publish_date"] is None

    assert jobs[0]["expiry_date"] is None

    assert context.response.status_code == 303

    location = context.response.headers["location"]

    assert "error=insufficient_credit" in location

    assert "saved=draft" in location


@then(
    "the system should display the credit deduction details including employer information job post details and transaction date"
)
def credit_deduction_details(
    context,
):

    assert context.credit_history is not None

    assert len(context.credit_history) == 1

    record = context.credit_history[0]

    # Employer information
    assert record["company_id"] == COMPANY_ID

    # Job posting details
    assert record["type"] == "JOB_POST"

    assert JOB_TITLE in record["description"]

    assert record["credit"] == -1

    assert record["balance"] == 4

    assert record["reference"] != ""

    # Transaction date
    assert record["date"] is not None
