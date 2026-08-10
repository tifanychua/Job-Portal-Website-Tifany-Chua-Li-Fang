from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import stripe

from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when


import importlib
import sys
import types
from pathlib import Path


def load_stripe_module():
    routes_dir = Path("src/job_portal_web/backend/routes")
    matches = []

    for path in routes_dir.glob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        if "def stripe_webhook(" in text and "def stripe_payment_success(" in text:
            matches.append(path)

    if not matches:
        raise ImportError(
            "Could not find the Stripe route module in "
            "src/job_portal_web/backend/routes."
        )

    module_name = (
        "job_portal_web.backend.routes."
        + matches[0].stem
    )

    fake_database = types.ModuleType(
        "job_portal_web.backend.database"
    )
    fake_database.db = None

    original_database = sys.modules.get(
        "job_portal_web.backend.database"
    )

    sys.modules[
        "job_portal_web.backend.database"
    ] = fake_database

    try:
        return importlib.import_module(module_name)
    finally:
        if original_database is not None:
            sys.modules[
                "job_portal_web.backend.database"
            ] = original_database
        else:
            sys.modules.pop(
                "job_portal_web.backend.database",
                None
            )


stripe_module = load_stripe_module()


scenarios("features/paymentSuccess.feature")

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"
CUSTOMER_ID = "cus_test"
SESSION_ID = "cs_test"
INVOICE_ID = "in_test"


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
        data = self.collection.documents.get(
            self.document_id
        )

        return FakeDocumentSnapshot(
            self.document_id,
            data or {},
            exists=data is not None,
        )


class FakeCollection:
    def __init__(
        self,
        documents=None,
    ):
        self.documents = (
            documents.copy()
            if documents
            else {}
        )

    def document(self, document_id):
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
            "company": FakeCollection(
                companies or {}
            ),
            "payment": FakeCollection(
                payments or {}
            ),
        }

    def collection(self, name):
        return self.collections[name]


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


class Context:
    def __init__(self):
        self.response = None
        self.error = None
        self.db = None
        self.session = None


@pytest.fixture
def context():
    return Context()


def install_db(
    monkeypatch,
    companies=None,
    payments=None,
):
    db = FakeDB(
        companies=companies,
        payments=payments,
    )

    monkeypatch.setattr(
        stripe_module,
        "db",
        db,
    )

    monkeypatch.setattr(
        stripe_module,
        "templates",
        FakeTemplates(),
    )

    return db


def company_data(
    customer_id=CUSTOMER_ID,
):
    return {
        COMPANY_ID: {
            "companyName":
                "ABC Technology Sdn Bhd",
            "stripe_customer_id":
                customer_id,
        }
    }


def subscription_object(
    plan_name="business",
):
    return SimpleNamespace(
        metadata={
            "plan": plan_name
        }
    )


def invoice_object(
    amount_paid=12900,
    invoice_id=INVOICE_ID,
):
    return SimpleNamespace(
        id=invoice_id,
        amount_paid=amount_paid,
    )


def checkout_session(
    customer_id=CUSTOMER_ID,
    subscription=None,
    invoice=None,
    payment_status="paid",
):
    return SimpleNamespace(
        customer=customer_id,
        subscription=(
            subscription
            if subscription is not None
            else subscription_object()
        ),
        invoice=(
            invoice
            if invoice is not None
            else invoice_object()
        ),
        payment_status=payment_status,
    )


def open_success(
    session_id=SESSION_ID,
):
    return stripe_module.stripe_payment_success(
        request=FakeRequest(),
        session_id=session_id,
    )


def open_success_error(context):
    try:
        context.response = open_success()
    except HTTPException as exc:
        context.error = exc


# ============================================================
# NORMAL PYTEST TESTS
# ============================================================

def test_saved_firestore_payment_is_used(
    monkeypatch,
):
    payments = {
        INVOICE_ID: {
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
    }

    install_db(
        monkeypatch,
        companies=company_data(),
        payments=payments,
    )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs:
            checkout_session(),
    )

    response = open_success()

    assert (
        response["template"]
        == "paymentSuccess.html"
    )

    payment = response["context"]["payment"]

    assert payment["package"] == "Business Pack"
    assert payment["status"] == "COMPLETED"
    assert (
        payment["completed_at"]
        == "10 Aug 2026, 09:30 AM"
    )


def test_fallback_payment_uses_card(
    monkeypatch,
):
    install_db(
        monkeypatch,
        companies=company_data(),
        payments={},
    )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs:
            checkout_session(),
    )

    response = open_success()

    payment = response["context"]["payment"]

    assert payment["package"] == "Business Pack"
    assert payment["credits"] == 30
    assert payment["amount"] == 129.00
    assert payment["payment_method"] == "Card"
    assert payment["status"] == "PAID"


def test_customer_mismatch_is_forbidden(
    monkeypatch,
):
    install_db(
        monkeypatch,
        companies=company_data(
            customer_id="cus_other"
        ),
        payments={},
    )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs:
            checkout_session(
                customer_id=CUSTOMER_ID
            ),
    )

    with pytest.raises(HTTPException) as exc:
        open_success()

    assert exc.value.status_code == 403
    assert exc.value.detail == "Access denied"


def test_missing_company_is_404(
    monkeypatch,
):
    install_db(
        monkeypatch,
        companies={},
        payments={},
    )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs:
            checkout_session(),
    )

    with pytest.raises(HTTPException) as exc:
        open_success()

    assert exc.value.status_code == 404


# ============================================================
# BDD GIVEN
# ============================================================

@given(
    "the current company exists with the matching Stripe customer"
)
def matching_company(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=company_data(),
        payments={},
    )


@given(
    "the current company exists with a different Stripe customer"
)
def different_customer_company(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=company_data(
            customer_id="cus_other"
        ),
        payments={},
    )


@given(
    "the current company does not exist"
)
def missing_company(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies={},
        payments={},
    )


def install_checkout_session(
    monkeypatch,
    context,
    session,
):
    context.session = session

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        lambda *args, **kwargs:
            session,
    )


@given(
    "Stripe returns a valid checkout session"
)
def valid_checkout(
    monkeypatch,
    context,
):
    install_checkout_session(
        monkeypatch,
        context,
        checkout_session(),
    )


@given(
    "Stripe returns a valid checkout session with an amount paid"
)
def checkout_with_amount(
    monkeypatch,
    context,
):
    install_checkout_session(
        monkeypatch,
        context,
        checkout_session(
            invoice=invoice_object(
                amount_paid=12950
            )
        ),
    )


@given(
    "Stripe returns a session containing a subscription ID"
)
def checkout_with_subscription_id(
    monkeypatch,
    context,
):
    session = checkout_session(
        subscription="sub_string"
    )

    install_checkout_session(
        monkeypatch,
        context,
        session,
    )

    monkeypatch.setattr(
        stripe_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id:
            subscription_object(
                "business"
            ),
    )


@given(
    "Stripe returns a valid checkout session without invoice"
)
def checkout_without_invoice(
    monkeypatch,
    context,
):
    session = SimpleNamespace(
        customer=CUSTOMER_ID,
        subscription=subscription_object(),
        invoice=None,
        payment_status="paid",
    )

    install_checkout_session(
        monkeypatch,
        context,
        session,
    )


@given(
    "a completed Firestore payment exists"
)
def completed_payment(
    context,
):
    context.db.collection(
        "payment"
    ).documents[INVOICE_ID] = {
        "package": "Business Pack",
        "credits": 30,
        "amount": 129.00,
        "payment_method": "Card",
        "status": "COMPLETED",
    }


@given(
    "a Firestore payment with completed date exists"
)
def payment_with_date(
    context,
):
    context.db.collection(
        "payment"
    ).documents[INVOICE_ID] = {
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


@given(
    "no Firestore payment exists"
)
def no_firestore_payment(context):
    context.db.collection(
        "payment"
    ).documents.clear()


@given(
    "Stripe checkout session retrieval fails"
)
def checkout_retrieval_fails(
    monkeypatch,
    context,
):
    # Company is needed so the scenario reaches Stripe first;
    # stripe_payment_success retrieves Stripe before loading company.
    context.db = install_db(
        monkeypatch,
        companies=company_data(),
        payments={},
    )

    def fail(*args, **kwargs):
        raise stripe.error.StripeError(
            "Stripe unavailable"
        )

    monkeypatch.setattr(
        stripe_module.stripe.checkout.Session,
        "retrieve",
        fail,
    )


# ============================================================
# BDD WHEN
# ============================================================

@when(
    "the employer opens the payment success page"
)
def open_payment_success(context):
    context.response = open_success()


@when(
    "the employer opens the payment success page expecting an error"
)
def open_payment_success_error(context):
    open_success_error(context)


# ============================================================
# BDD THEN
# ============================================================

@then(
    "the payment success page should be displayed"
)
def verify_page(context):
    assert (
        context.response["template"]
        == "paymentSuccess.html"
    )


@then(
    "the saved Firestore payment should be used"
)
def verify_saved_payment(context):
    payment = context.response[
        "context"
    ]["payment"]

    assert payment["package"] == "Business Pack"
    assert payment["status"] == "COMPLETED"


@then(
    "a fallback card payment should be displayed"
)
def verify_fallback(context):
    payment = context.response[
        "context"
    ]["payment"]

    assert payment["package"] == "Business Pack"
    assert payment["credits"] == 30
    assert payment["payment_method"] == "Card"
    assert payment["status"] == "PAID"


@then(
    "the fallback payment amount should be converted from cents"
)
def verify_amount(context):
    assert (
        context.response["context"]
        ["payment"]["amount"]
        == 129.50
    )


@then(
    "the completed payment date should be formatted for display"
)
def verify_date(context):
    assert (
        context.response["context"]
        ["payment"]["completed_at"]
        == "10 Aug 2026, 09:30 AM"
    )


@then(
    "access to the payment success page should be denied"
)
def verify_forbidden(context):
    assert context.error is not None
    assert context.error.status_code == 403
    assert context.error.detail == "Access denied"


@then(
    "company not found should be returned"
)
def verify_missing_company(context):
    assert context.error is not None
    assert context.error.status_code == 404
    assert context.error.detail == "Company not found"


@then(
    "a Stripe payment success error should be returned"
)
def verify_stripe_error(context):
    assert context.error is not None
    assert context.error.status_code == 400


@then(
    "the subscription should be retrieved and the plan should be displayed"
)
def verify_subscription_retrieval(context):
    payment = context.response[
        "context"
    ]["payment"]

    assert payment["package"] == "Business Pack"
    assert payment["credits"] == 30


@then(
    "the order ID should use the session ID"
)
def verify_order_id_fallback(context):
    assert (
        context.response["context"]
        ["order_id"]
        == SESSION_ID
    )
