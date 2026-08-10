import asyncio
import importlib
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when

# ============================================================
# LOAD ACTUAL RECEIPT ROUTE WITHOUT REAL FIREBASE CONNECTION
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

    # Fallback in case comments still mention PayPal but routes are already cleaned.
    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def payment_receipt(" in text and "def download_receipt(" in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client
            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)
            finally:
                firestore_module.client = original_client

    raise ImportError("Could not find the payment receipt route file.")


receipt_module = load_receipt_module()

scenarios("features/paymentReceipt.feature")


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
# FAKE TEMPLATE / REQUEST
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


class FakeRequest:

    def __init__(self):
        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


# ============================================================
# BDD CONTEXT
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
# DEFAULT DATA
# ============================================================


@pytest.fixture
def companies():
    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
        }
    }


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
                tzinfo=timezone.utc,
            ),
        }
    }


# ============================================================
# INSTALL FAKE DB
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
# HELPERS
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


def download_receipt(
    order_id=ORDER_ID,
):
    return asyncio.run(
        receipt_module.download_receipt(
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


def capture_download_error(
    context,
):
    try:
        context.response = download_receipt()

    except HTTPException as exc:
        context.error = exc


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_valid_receipt_page(
    setup_db,
):
    response = open_receipt()

    assert response["template"] == "paymentReceipt.html"


def test_receipt_information(
    setup_db,
):
    response = open_receipt()

    data = response["context"]

    assert data["order_id"] == ORDER_ID

    assert data["company"]["companyName"] == "ABC Technology Sdn Bhd"

    assert data["payment"]["package"] == "Business Pack"

    assert data["payment"]["credits"] == 30

    assert data["payment"]["payment_method"] == "Card"

    assert data["payment"]["status"] == "COMPLETED"

    assert data["payment"]["amount"] == 129.00


def test_completed_date_formatted(
    setup_db,
):
    response = open_receipt()

    assert response["context"]["payment"]["completed_at"] == "10 Aug 2026, 09:30 AM"


def test_missing_payment_method_defaults_card(
    monkeypatch,
    companies,
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

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )

    response = open_receipt()

    assert response["context"]["payment"]["payment_method"] == "Card"


def test_receipt_not_found(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        {},
    )

    with pytest.raises(HTTPException) as exc:
        open_receipt()

    assert exc.value.status_code == 404
    assert exc.value.detail == "Receipt not found."


def test_other_company_cannot_view(
    monkeypatch,
    companies,
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

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )

    with pytest.raises(HTTPException) as exc:
        open_receipt()

    assert exc.value.status_code == 403
    assert exc.value.detail == "Access denied."


@pytest.mark.parametrize(
    "status",
    [
        "PENDING",
        "FAILED",
    ],
)
def test_non_completed_receipt_rejected(
    monkeypatch,
    companies,
    status,
):
    payments = {
        ORDER_ID: {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "credits": 30,
            "payment_method": "Card",
            "status": status,
            "amount": 129.00,
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )

    with pytest.raises(HTTPException) as exc:
        open_receipt()

    assert exc.value.status_code == 400

    assert exc.value.detail == "Receipt is only available " "for completed payments."


def test_pdf_download(
    setup_db,
):
    response = download_receipt()

    assert response.media_type == "application/pdf"

    assert response.filename == f"Receipt_{ORDER_ID}.pdf"

    assert os.path.exists(response.path)


# ============================================================
# BDD GIVEN
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
def other_company_payment(
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
def company_record_missing(
    monkeypatch,
    context,
):
    payments = context.db.collection("payment").documents.copy()

    context.db = install_fake_db(
        monkeypatch,
        {},
        payments,
    )


@given("a completed card payment has no package")
def no_package(
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
def no_amount(
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
# BDD WHEN
# ============================================================


@when("the employer opens the payment receipt")
def open_payment_receipt(
    context,
):
    context.response = open_receipt()


@when("the employer opens the payment receipt expecting an error")
def open_payment_receipt_error(
    context,
):
    capture_open_error(context)


@when("the employer downloads the payment receipt")
def download_payment_receipt(
    context,
):
    context.response = download_receipt()


@when("the employer downloads the payment receipt expecting an error")
def download_payment_receipt_error(
    context,
):
    capture_download_error(context)


# ============================================================
# BDD THEN
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
def purchase_date(
    context,
):
    assert context.response["context"]["payment"]["completed_at"] == "10 Aug 2026, 09:30 AM"


@then("the purchase date should be represented with a dash")
def missing_date_dash(
    context,
):
    assert context.response["context"]["payment"]["completed_at"] == "-"


@then("the payment method should default to Card")
def default_card(
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
def completed_required(
    context,
):
    assert context.error is not None
    assert context.error.status_code == 400
    assert context.error.detail == "Receipt is only available " "for completed payments."


@then("company not found should be returned")
def company_not_found(
    context,
):
    assert context.error is not None
    assert context.error.status_code == 404
    assert context.error.detail == "Company not found."


@then("the system should return a PDF receipt")
def valid_pdf(
    context,
):
    assert context.response is not None
    assert os.path.exists(context.response.path)


@then("the downloaded receipt filename should contain the receipt number")
def pdf_filename(
    context,
):
    assert context.response.filename == f"Receipt_{ORDER_ID}.pdf"


@then("the downloaded receipt content type should be application pdf")
def pdf_content_type(
    context,
):
    assert context.response.media_type == "application/pdf"


@then("the PDF receipt should still be generated successfully")
def pdf_generated_safely(
    context,
):
    assert context.response is not None

    assert context.response.media_type == "application/pdf"

    assert os.path.exists(context.response.path)
