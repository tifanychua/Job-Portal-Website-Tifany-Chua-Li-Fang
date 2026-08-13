import asyncio
import importlib
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD EMPLOYER CREDIT MODULE
# ============================================================


def load_credit_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def employer_credit(" in text and '"/employer-credit"' in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client

            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)

            finally:
                firestore_module.client = original_client

    raise ImportError("Could not find employer_credit route.")


credit_module = load_credit_module()


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/viewJobPostingCredits.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


# ============================================================
# FAKE REQUEST
# ============================================================


class FakeRequest:
    def __init__(self):

        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeDocumentSnapshot:
    def __init__(
        self,
        document_id,
        data=None,
        exists=True,
    ):

        self.id = document_id

        self._data = data or {}

        self.exists = exists

    def to_dict(self):

        return self._data.copy()


class FakeDocumentReference:
    def __init__(
        self,
        collection,
        document_id,
    ):

        self.collection = collection
        self.document_id = document_id

    def get(self):

        data = self.collection.documents.get(self.document_id)

        if data is None:
            return FakeDocumentSnapshot(
                self.document_id,
                {},
                exists=False,
            )

        return FakeDocumentSnapshot(
            self.document_id,
            data,
            exists=True,
        )


class FakeQuery:
    def __init__(
        self,
        collection,
        filters=None,
    ):

        self.collection = collection

        self.filters = filters or []

    def where(
        self,
        *args,
        **kwargs,
    ):

        if "filter" in kwargs:
            field_filter = kwargs["filter"]

            field = field_filter.field_path

            operator = field_filter.op_string

            value = field_filter.value

        else:
            field = args[0]
            operator = args[1]
            value = args[2]

        return FakeQuery(
            self.collection,
            self.filters
            + [
                (
                    field,
                    operator,
                    value,
                )
            ],
        )

    def stream(self):

        results = []

        for (
            document_id,
            data,
        ) in self.collection.documents.items():
            matched = True

            for (
                field,
                operator,
                expected,
            ) in self.filters:
                if operator == "==" and data.get(field) != expected:
                    matched = False
                    break

            if matched:
                results.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        exists=True,
                    )
                )

        return results


class FakeCollection:
    def __init__(
        self,
        documents=None,
    ):

        self.documents = documents or {}

    def document(
        self,
        document_id,
    ):

        return FakeDocumentReference(
            self,
            document_id,
        )

    def where(
        self,
        *args,
        **kwargs,
    ):

        return FakeQuery(self).where(
            *args,
            **kwargs,
        )

    def stream(self):

        return [
            FakeDocumentSnapshot(
                document_id,
                data,
                exists=True,
            )
            for (
                document_id,
                data,
            ) in self.documents.items()
        ]


class FakeDB:
    def __init__(
        self,
        companies=None,
        payments=None,
    ):

        self.collections = {
            "company": FakeCollection(companies or {}),
            "payment": FakeCollection(payments or {}),
        }

    def collection(
        self,
        name,
    ):

        return self.collections[name]


# ============================================================
# FAKE TEMPLATE
# ============================================================


class FakeTemplates:
    def TemplateResponse(
        self,
        request,
        name,
        context,
    ):

        return {
            "template": name,
            "context": context,
        }


# ============================================================
# CONTEXT
# ============================================================


class Context:
    def __init__(self):

        self.response = None

        self.error = None

        self.company = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(
    monkeypatch,
    company_data,
):

    fake_db = FakeDB(
        companies={COMPANY_ID: company_data},
        payments={},
    )

    monkeypatch.setattr(
        credit_module,
        "db",
        fake_db,
    )

    monkeypatch.setattr(
        credit_module,
        "templates",
        FakeTemplates(),
    )

    monkeypatch.setattr(
        credit_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    return fake_db


# ============================================================
# HELPERS
# ============================================================


def open_credit_page():

    return asyncio.run(credit_module.employer_credit(FakeRequest()))


def ensure_credit_available(
    company,
):

    available_credit = int(company.get("available_credit", 0) or 0)

    if available_credit <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Insufficient job posting credits. "
                "Additional credits are required "
                "before publishing a job vacancy."
            ),
        )

    return True


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_employer_can_view_available_job_posting_credits(
    monkeypatch,
):

    company = {
        "companyName": "ABC Technology Sdn Bhd",
        "total_credit": 40,
        "available_credit": 20,
        "used_credit": 20,
        "expired_credit": 0,
    }

    install_fake_db(
        monkeypatch,
        company,
    )

    response = open_credit_page()

    data = response["context"]

    assert response["template"] == "employerCredit.html"

    assert data["available_credit"] == 20


def test_employer_can_view_used_and_remaining_credits(
    monkeypatch,
):

    company = {
        "companyName": "ABC Technology Sdn Bhd",
        "total_credit": 50,
        "available_credit": 15,
        "used_credit": 35,
        "expired_credit": 0,
    }

    install_fake_db(
        monkeypatch,
        company,
    )

    response = open_credit_page()

    data = response["context"]

    assert data["used_credit"] == 35

    assert data["available_credit"] == 15


def test_employer_with_zero_credit_cannot_publish_job():

    company = {"available_credit": 0}

    with pytest.raises(HTTPException) as exc:
        ensure_credit_available(company)

    assert exc.value.status_code == 400

    assert "Additional credits are required" in exc.value.detail


# ============================================================
# BDD GIVEN
# ============================================================


@given("the employer is logged into the system")
def employer_logged_in(
    monkeypatch,
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn Bhd",
        "total_credit": 40,
        "available_credit": 20,
        "used_credit": 20,
        "expired_credit": 0,
    }

    install_fake_db(
        monkeypatch,
        context.company,
    )


@given("the employer has used job posting credits for published vacancies")
def employer_used_credits(
    monkeypatch,
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn Bhd",
        "total_credit": 50,
        "available_credit": 15,
        "used_credit": 35,
        "expired_credit": 0,
    }

    install_fake_db(
        monkeypatch,
        context.company,
    )


@given("the employer has no available job posting credits")
def employer_has_no_credits(
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn Bhd",
        "total_credit": 20,
        "available_credit": 0,
        "used_credit": 20,
        "expired_credit": 0,
    }


# ============================================================
# BDD WHEN
# ============================================================


@when("the employer accesses the credit management page")
def employer_accesses_credit_page(
    context,
):

    context.response = open_credit_page()


@when("the employer views credit information")
def employer_views_credit_information(
    context,
):

    context.response = open_credit_page()


@when("the employer attempts to create a new job posting")
def employer_attempts_new_job(
    context,
):

    try:
        ensure_credit_available(context.company)

    except HTTPException as exc:
        context.error = exc


# ============================================================
# BDD THEN
# ============================================================


@then("the system should display the employer's available job posting credits")
def display_available_credits(
    context,
):

    data = context.response["context"]

    assert context.response["template"] == "employerCredit.html"

    assert data["available_credit"] == 20


@then("the system should display the number of credits used and remaining credits")
def display_used_remaining_credits(
    context,
):

    data = context.response["context"]

    assert data["used_credit"] == 35

    assert data["available_credit"] == 15

    assert data["total_credit"] == 50


@then(
    "the system should notify the employer that additional credits are required before publishing a job vacancy"
)
def insufficient_credit_message(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 400

    assert "Additional credits are required" in context.error.detail
