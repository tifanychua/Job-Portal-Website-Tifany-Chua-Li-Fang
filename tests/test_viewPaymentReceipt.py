import asyncio
import importlib
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

    # Prefer Stripe/current payment route
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

        if "def payment_receipt(" in text:
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

scenarios("features/viewPaymentReceipt.feature")


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
# DEFAULT COMPANY
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
        "templates",
        FakeTemplates(),
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


def open_receipt(
    order_id=ORDER_ID,
):

    return asyncio.run(
        receipt_module.payment_receipt(
            request=FakeRequest(),
            order_id=order_id,
        )
    )


def capture_open_error(
    context,
):

    try:
        context.response = open_receipt()

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


@given("a completed payment has no payment method")
def payment_without_method(
    monkeypatch,
    companies,
    context,
):

    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "credits": 10,
            "status": "COMPLETED",
            "amount": 49.00,
        }
    }

    context.db = install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("the requested receipt does not exist")
def receipt_missing(
    monkeypatch,
    companies,
    context,
):

    context.db = install_fake_db(
        monkeypatch,
        companies,
        {},
    )


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


@given("the current company record does not exist")
def company_missing(
    monkeypatch,
    context,
):

    payments = context.db.collection("payment").documents.copy()

    context.db = install_fake_db(
        monkeypatch,
        {},
        payments,
    )


# ============================================================
# WHEN
# ============================================================


@when("the employer opens the payment receipt")
def employer_opens_receipt(
    context,
):

    context.response = open_receipt()


@when("the employer opens the payment receipt expecting an error")
def employer_opens_receipt_error(
    context,
):

    capture_open_error(context)


# ============================================================
# THEN
# ============================================================


@then("the payment receipt page should be displayed")
def receipt_page_displayed(
    context,
):

    assert context.response["template"] == "paymentReceipt.html"


@then(
    "the receipt should contain the correct company package credits payment method status and amount"
)
def receipt_information(
    context,
):

    data = context.response["context"]

    assert data["company"]["companyName"] == "ABC Technology Sdn Bhd"

    payment = data["payment"]

    assert payment["package"] == "Business Pack"

    assert payment["credits"] == 30

    assert payment["payment_method"] == "Card"

    assert payment["status"] == "COMPLETED"

    assert payment["amount"] == 129.00


@then("the receipt number should match the payment ID")
def receipt_number(
    context,
):

    assert context.response["context"]["order_id"] == ORDER_ID


@then("the purchase date should be formatted correctly")
def formatted_date(
    context,
):

    assert context.response["context"]["payment"]["completed_at"] == "10 Aug 2026, 09:30 AM"


@then("the purchase date should be represented with a dash")
def missing_date(
    context,
):

    assert context.response["context"]["payment"]["completed_at"] == "-"


@then("the payment method should default to Card")
def default_payment_method(
    context,
):

    assert context.response["context"]["payment"]["payment_method"] == "Card"


@then("receipt not found should be returned")
def receipt_not_found(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 404

    assert context.error.detail == "Receipt not found."


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


@then("company not found should be returned")
def company_not_found(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 404

    assert context.error.detail == "Company not found."
