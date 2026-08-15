import asyncio
import importlib
import os
from datetime import UTC, datetime
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
# LOAD PAYMENT RECEIPT MODULE
# ============================================================


def load_receipt_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if (
            "def payment_receipt(" in text
            and "def download_receipt(" in text
            and "PayPal Sandbox" not in text
        ):
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client

            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)

            finally:
                firestore_module.client = original_client

    # Fallback
    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def download_receipt(" in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client

            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)

            finally:
                firestore_module.client = original_client

    raise ImportError("Could not find payment receipt route module.")


receipt_module = load_receipt_module()


# ============================================================
# FEATURE
# ============================================================

scenarios("features/downloadPaymentReceipt.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

OTHER_COMPANY_ID = "OTHER-COMPANY"

ORDER_ID = "in_test_receipt"


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeSnapshot:
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


class FakeDocument:
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
            return FakeSnapshot(
                self.document_id,
                {},
                False,
            )

        return FakeSnapshot(
            self.document_id,
            data,
            True,
        )


class FakeCollection:
    def __init__(
        self,
        documents=None,
    ):

        self.documents = documents.copy() if documents else {}

    def document(
        self,
        document_id,
    ):

        return FakeDocument(
            self,
            document_id,
        )


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
# FAKE REQUEST
# ============================================================


class FakeRequest:
    def __init__(self):

        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


# ============================================================
# CONTEXT
# ============================================================


class Context:
    def __init__(self):

        self.response = None

        self.error = None

        self.db = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# COMPANY DATA
# ============================================================


@pytest.fixture
def companies():

    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
        }
    }


# ============================================================
# DEFAULT PAYMENT
# ============================================================


@pytest.fixture
def payments():

    return {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "COMPLETED",
            "amount": 129.00,
            "completed_at": datetime(
                2026,
                8,
                10,
                9,
                30,
                tzinfo=UTC,
            ),
        }
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(
    monkeypatch,
    companies,
    payments,
):

    fake_db = FakeDB(
        companies=companies,
        payments=payments,
    )

    monkeypatch.setattr(
        receipt_module,
        "db",
        fake_db,
    )

    monkeypatch.setattr(
        receipt_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    companies,
    payments,
):

    return install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


# ============================================================
# HELPER
# ============================================================


def download_receipt(
    order_id=ORDER_ID,
):

    return asyncio.run(
        receipt_module.download_receipt(
            request=FakeRequest(),
            order_id=order_id,
        )
    )


def capture_download_error(
    context,
):

    try:
        context.response = download_receipt()

    except HTTPException as exc:
        context.error = exc


# ============================================================
# GIVEN
# ============================================================


@given("a completed card payment exists for the current company")
def completed_payment(
    setup_db,
    context,
):

    context.db = setup_db


@given("a completed payment belongs to another company")
def another_company(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": OTHER_COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "COMPLETED",
            "amount": 129.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a pending card payment exists for the current company")
def pending_payment(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "PENDING",
            "amount": 129.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a failed card payment exists for the current company")
def failed_payment(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "FAILED",
            "amount": 129.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a completed card payment has no completed date")
def completed_without_date(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "COMPLETED",
            "amount": 129.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a completed card payment has no package")
def payment_without_package(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "credits": 30,
            "payment_method": "Card",
            "status": "COMPLETED",
            "amount": 129.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a completed card payment has no amount")
def payment_without_amount(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": "COMPLETED",
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


# ============================================================
# WHEN
# ============================================================


@when("the employer downloads the payment receipt")
def employer_downloads_receipt(
    context,
):

    context.response = download_receipt()


@when("the employer downloads the payment receipt expecting an error")
def employer_downloads_error(
    context,
):

    capture_download_error(context)


# ============================================================
# THEN
# ============================================================


@then("the system should return a PDF receipt")
def return_pdf(
    context,
):

    assert context.response is not None

    assert os.path.exists(context.response.path)


@then("the downloaded receipt filename should contain the receipt number")
def receipt_filename(
    context,
):

    assert context.response.filename == f"Receipt_{ORDER_ID}.pdf"


@then("the downloaded receipt content type should be application pdf")
def receipt_content_type(
    context,
):

    assert context.response.media_type == "application/pdf"


@then("receipt access should be denied")
def access_denied(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 403

    assert context.error.detail == "Access denied."


@then("completed payment receipt should be required")
def completed_payment_required(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 400

    assert context.error.detail == "Receipt is only available for completed payments."


@then("the PDF receipt should still be generated successfully")
def pdf_generated_safely(
    context,
):

    assert context.response is not None

    assert context.response.media_type == "application/pdf"

    assert os.path.exists(context.response.path)
