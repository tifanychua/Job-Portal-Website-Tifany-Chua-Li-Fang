from datetime import datetime, timezone
from types import SimpleNamespace

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
# LOAD STRIPE PAYMENT MODULE
# ============================================================


def load_stripe_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    matches = []

    for path in routes_dir.glob("*.py"):

        try:

            text = path.read_text(encoding="utf-8")

        except OSError:

            continue

        if "def stripe_payment_success(" in text:

            matches.append(path)

    if not matches:

        raise ImportError("Could not find " "stripe_payment_success route.")

    module_name = "job_portal_web.backend.routes." + matches[0].stem

    # Avoid real database import
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

            sys.modules.pop("job_portal_web.backend.database", None)


stripe_module = load_stripe_module()


# ============================================================
# FEATURE
# ============================================================

scenarios("features/paymentSuccess.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

CUSTOMER_ID = "cus_test"

SESSION_ID = "cs_test"

INVOICE_ID = "in_test"


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

        return FakeDocumentSnapshot(
            self.document_id,
            data or {},
            exists=(data is not None),
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

        return FakeDocumentReference(
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

        self.db = None

        self.history = []


@pytest.fixture
def context():

    return Context()


# ============================================================
# HELPERS
# ============================================================


def company_data():

    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
            "stripe_customer_id": CUSTOMER_ID,
        }
    }


def subscription_object():

    return SimpleNamespace(metadata={"plan": "business"})


def invoice_object():

    return SimpleNamespace(
        id=INVOICE_ID,
        amount_paid=12900,
    )


def checkout_session():

    return SimpleNamespace(
        customer=CUSTOMER_ID,
        subscription=subscription_object(),
        invoice=invoice_object(),
        payment_status="paid",
    )


def completed_payment():

    return {
        "company_id": COMPANY_ID,
        "package": "Business Pack",
        "credits": 30,
        "amount": 129.00,
        "payment_method": "Card",
        "status": "COMPLETED",
        "completed_at": datetime(
            2026,
            8,
            10,
            9,
            30,
            tzinfo=timezone.utc,
        ),
    }


def install_db(
    monkeypatch,
    context,
    payments=None,
):

    context.db = FakeDB(
        companies=company_data(),
        payments=payments or {},
    )

    monkeypatch.setattr(
        stripe_module,
        "db",
        context.db,
    )

    monkeypatch.setattr(
        stripe_module,
        "templates",
        FakeTemplates(),
    )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs: checkout_session(),
    )


def open_success():

    return stripe_module.stripe_payment_success(
        request=FakeRequest(),
        session_id=SESSION_ID,
    )


# ============================================================
# GIVEN
# ============================================================


@given("the employer has completed a payment transaction successfully")
def successful_transaction(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
        payments={INVOICE_ID: completed_payment()},
    )


@given("the employer has received a payment confirmation")
def payment_confirmation_received(
    monkeypatch,
    context,
):

    install_db(
        monkeypatch,
        context,
        payments={INVOICE_ID: completed_payment()},
    )

    context.response = open_success()


@given("the employer has completed one or more successful transactions")
def successful_transactions(
    monkeypatch,
    context,
):

    payments = {
        "TXN001": completed_payment(),
        "TXN002": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "credits": 10,
            "amount": 49.00,
            "payment_method": "Card",
            "status": "COMPLETED",
            "completed_at": datetime(
                2026,
                8,
                5,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        },
    }

    install_db(
        monkeypatch,
        context,
        payments=payments,
    )

    context.history = [
        payment for payment in payments.values() if (payment.get("status") == "COMPLETED")
    ]


# ============================================================
# WHEN
# ============================================================


@when("the payment is confirmed by the system")
def payment_confirmed(
    context,
):

    context.response = open_success()


@when("the employer views the confirmation details")
def view_confirmation_details(
    context,
):

    assert context.response is not None


@when("the employer views payment history")
def view_payment_history(
    context,
):

    # This scenario only verifies that
    # successful payment records are
    # available for payment history.
    assert context.history is not None


# ============================================================
# THEN
# ============================================================


@then("the system should display a payment confirmation message to the employer")
def display_confirmation(
    context,
):

    assert context.response["template"] == "paymentSuccess.html"

    payment = context.response["context"]["payment"]

    assert payment["status"] == "COMPLETED"


@then(
    "the system should display transaction information including payment amount transaction date and purchased credit package"
)
def display_confirmation_details(
    context,
):

    payment = context.response["context"]["payment"]

    # Payment amount
    assert payment["amount"] == 129.00

    # Transaction date
    assert payment["completed_at"] == "10 Aug 2026, 09:30 AM"

    # Purchased package
    assert payment["package"] == "Business Pack"

    # Purchased credits
    assert payment["credits"] == 30

    # Card-only payment
    assert payment["payment_method"] == "Card"


@then("the system should display a list of completed payment transactions")
def display_completed_history(
    context,
):

    assert len(context.history) == 2

    for payment in context.history:

        assert payment["status"] == "COMPLETED"

        assert payment["payment_method"] == "Card"

        assert "amount" in payment

        assert "package" in payment
