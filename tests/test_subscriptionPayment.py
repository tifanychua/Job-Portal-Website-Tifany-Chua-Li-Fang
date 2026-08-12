from types import SimpleNamespace

import pytest

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

        if "def stripe_webhook(" in text and "def handle_invoice_paid(" in text:
            matches.append(path)

    if not matches:
        raise ImportError(
            "Could not find the Stripe route module in " "src/job_portal_web/backend/routes."
        )

    module_name = "job_portal_web.backend.routes." + matches[0].stem

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


scenarios("features/subscriptionPayment.feature")

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"
CUSTOMER_ID = "cus_test"
SUBSCRIPTION_ID = "sub_test"


class FakeDocumentSnapshot:
    def __init__(
        self,
        document_id,
        data=None,
        exists=True,
        reference=None,
    ):
        self.id = document_id
        self._data = data or {}
        self.exists = exists
        self.reference = reference

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
            exists=data is not None,
            reference=self,
        )

    def update(self, data):
        current = self.collection.documents.setdefault(
            self.document_id,
            {},
        )
        current.update(data)

    def set(self, data):
        self.collection.documents[self.document_id] = data.copy()


class FakeQuery:
    def __init__(
        self,
        collection,
        filters=None,
        limit_count=None,
    ):
        self.collection = collection
        self.filters = filters or []
        self.limit_count = limit_count

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
            field, operator, value = args

        return FakeQuery(
            self.collection,
            self.filters + [(field, operator, value)],
            self.limit_count,
        )

    def limit(self, count):
        return FakeQuery(
            self.collection,
            self.filters,
            count,
        )

    def stream(self):
        results = []

        for document_id, data in self.collection.documents.items():
            matched = True

            for field, operator, expected in self.filters:
                if operator == "==" and data.get(field) != expected:
                    matched = False
                    break

            if matched:
                ref = FakeDocumentReference(
                    self.collection,
                    document_id,
                )
                results.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        True,
                        ref,
                    )
                )

        if self.limit_count is not None:
            results = results[: self.limit_count]

        return iter(results)


class FakeCollection:
    def __init__(
        self,
        documents=None,
    ):
        self.documents = documents.copy() if documents else {}
        self.added = []

    def document(self, document_id):
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

    def add(self, data):
        self.added.append(data.copy())
        return None


class FakeDB:
    def __init__(
        self,
        companies=None,
        payments=None,
    ):
        self.collections = {
            "company": FakeCollection(companies or {}),
            "payment": FakeCollection(payments or {}),
            "credit_history": FakeCollection(),
        }

    def collection(self, name):
        return self.collections[name]


class Context:
    def __init__(self):
        self.db = None
        self.invoice = None
        self.session = None
        self.subscription = None
        self.plan_name = None


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

    return db


def default_company(
    available_credit=4,
    expired_credit=2,
):
    return {
        COMPANY_ID: {
            "stripe_customer_id": CUSTOMER_ID,
            "stripe_subscription_id": SUBSCRIPTION_ID,
            "available_credit": available_credit,
            "expired_credit": expired_credit,
            "subscription_plan": "starter",
        }
    }


def subscription_for_plan(plan_name):
    return SimpleNamespace(
        metadata={"plan": plan_name},
        items=SimpleNamespace(
            data=[
                SimpleNamespace(
                    current_period_start=1782864000,
                    current_period_end=1785542400,
                )
            ]
        ),
    )


def paid_invoice(
    invoice_id="in_test",
    customer_id=CUSTOMER_ID,
    subscription_id=SUBSCRIPTION_ID,
    amount_paid=12900,
):
    return SimpleNamespace(
        id=invoice_id,
        customer=customer_id,
        subscription=subscription_id,
        amount_paid=amount_paid,
        currency="myr",
    )


# ============================================================
# NORMAL PYTEST TESTS
# ============================================================


def test_checkout_completed_updates_company(
    monkeypatch,
):
    db = install_db(
        monkeypatch,
        companies=default_company(),
    )

    stripe_module.handle_checkout_completed(
        SimpleNamespace(
            customer=CUSTOMER_ID,
            subscription="sub_new",
        )
    )

    company = db.collection("company").documents[COMPANY_ID]

    assert company["stripe_customer_id"] == CUSTOMER_ID
    assert company["stripe_subscription_id"] == "sub_new"


@pytest.mark.parametrize(
    "plan_name,credits",
    [
        ("starter", 10),
        ("business", 30),
        ("enterprise", 60),
    ],
)
def test_paid_invoice_adds_plan_credits(
    monkeypatch,
    plan_name,
    credits,
):
    db = install_db(
        monkeypatch,
        companies=default_company(
            available_credit=4,
            expired_credit=2,
        ),
    )

    monkeypatch.setattr(
        stripe_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id: subscription_for_plan(plan_name),
    )

    stripe_module.handle_invoice_paid(paid_invoice())

    company = db.collection("company").documents[COMPANY_ID]

    assert company["total_credit"] == credits
    assert company["available_credit"] == credits
    assert company["used_credit"] == 0
    assert company["expired_credit"] == 6

    payment = db.collection("payment").documents["in_test"]

    assert payment["status"] == "COMPLETED"
    assert payment["payment_method"] == "Card"
    assert payment["credits"] == credits


def test_duplicate_completed_invoice_is_ignored(
    monkeypatch,
):
    db = install_db(
        monkeypatch,
        companies=default_company(),
        payments={"in_test": {"status": "COMPLETED"}},
    )

    before = db.collection("company").documents[COMPANY_ID].copy()

    stripe_module.handle_invoice_paid(paid_invoice())

    after = db.collection("company").documents[COMPANY_ID]

    assert after == before


def test_failed_invoice_updates_status(
    monkeypatch,
):
    db = install_db(
        monkeypatch,
        companies=default_company(),
    )

    stripe_module.handle_invoice_failed(SimpleNamespace(customer=CUSTOMER_ID))

    company = db.collection("company").documents[COMPANY_ID]

    assert company["subscription_status"] == "PAYMENT_FAILED"


def test_subscription_deleted_expires_remaining(
    monkeypatch,
):
    db = install_db(
        monkeypatch,
        companies=default_company(
            available_credit=5,
            expired_credit=3,
        ),
    )

    stripe_module.handle_subscription_deleted(SimpleNamespace(customer=CUSTOMER_ID))

    company = db.collection("company").documents[COMPANY_ID]

    assert company["subscription_plan"] == ""
    assert company["subscription_status"] == "CANCELLED"
    assert company["available_credit"] == 0
    assert company["expired_credit"] == 8
    assert company["cancel_at_period_end"] is False


# ============================================================
# BDD GIVEN
# ============================================================


@given("a company exists for the Stripe customer")
def company_exists(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(),
    )


@given("checkout data does not contain a customer")
def checkout_without_customer(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(),
    )
    context.session = SimpleNamespace(subscription=SUBSCRIPTION_ID)


@given("a company exists with unused credits")
def company_with_unused_credits(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(
            available_credit=4,
            expired_credit=2,
        ),
    )
    context.invoice = paid_invoice()


def set_plan(
    monkeypatch,
    context,
    plan_name,
):
    context.plan_name = plan_name

    monkeypatch.setattr(
        stripe_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id: subscription_for_plan(plan_name),
    )


@given("Stripe returns a starter subscription")
def starter_plan(
    monkeypatch,
    context,
):
    set_plan(
        monkeypatch,
        context,
        "starter",
    )


@given("Stripe returns a business subscription")
def business_plan(
    monkeypatch,
    context,
):
    set_plan(
        monkeypatch,
        context,
        "business",
    )


@given("Stripe returns an enterprise subscription")
def enterprise_plan(
    monkeypatch,
    context,
):
    set_plan(
        monkeypatch,
        context,
        "enterprise",
    )


@given("the invoice was already processed successfully")
def already_processed(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(),
        payments={"in_test": {"status": "COMPLETED"}},
    )
    context.invoice = paid_invoice()


@given("a paid invoice does not contain an invoice ID")
def missing_invoice_id(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(),
    )
    context.invoice = paid_invoice(invoice_id=None)


@given("a paid invoice does not contain a customer")
def missing_customer(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(),
    )
    context.invoice = paid_invoice(customer_id=None)


@given("Stripe returns an unknown subscription plan")
def unknown_plan(
    monkeypatch,
    context,
):
    context.invoice = paid_invoice()

    set_plan(
        monkeypatch,
        context,
        "unknown",
    )


@given("a company exists with remaining credits")
def company_remaining_credits(
    monkeypatch,
    context,
):
    context.db = install_db(
        monkeypatch,
        companies=default_company(
            available_credit=5,
            expired_credit=3,
        ),
    )


# ============================================================
# BDD WHEN
# ============================================================


@when("checkout completed is handled")
def handle_checkout(context):
    session = context.session or SimpleNamespace(
        customer=CUSTOMER_ID,
        subscription=SUBSCRIPTION_ID,
    )

    stripe_module.handle_checkout_completed(session)


@when("a paid invoice is handled")
def handle_paid(context):
    stripe_module.handle_invoice_paid(context.invoice)


@when("the duplicate paid invoice is handled")
def handle_duplicate(context):
    stripe_module.handle_invoice_paid(context.invoice)


@when("the paid invoice is handled")
def handle_invalid_invoice(context):
    stripe_module.handle_invoice_paid(context.invoice)


@when("a failed invoice is handled")
def handle_failed(context):
    stripe_module.handle_invoice_failed(SimpleNamespace(customer=CUSTOMER_ID))


@when("a subscription update is handled")
def handle_subscription_update(context):
    stripe_module.handle_subscription_updated(
        SimpleNamespace(
            customer=CUSTOMER_ID,
            metadata={"plan": "business"},
            status="active",
            cancel_at_period_end=True,
        )
    )


@when("a subscription deletion is handled")
def handle_subscription_delete(context):
    stripe_module.handle_subscription_deleted(SimpleNamespace(customer=CUSTOMER_ID))


# ============================================================
# BDD THEN
# ============================================================


@then("the company Stripe identifiers should be updated")
def verify_checkout_update(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["stripe_customer_id"] == CUSTOMER_ID
    assert company["stripe_subscription_id"] == SUBSCRIPTION_ID


@then("no company update should occur")
def verify_no_checkout_update(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["stripe_subscription_id"] == SUBSCRIPTION_ID


def expected_credits(context):
    return stripe_module.PLANS[context.plan_name]["credits"]


@then("the company should receive starter credits")
def verify_starter_credits(context):
    assert context.db.collection("company").documents[COMPANY_ID]["available_credit"] == 10


@then("the company should receive business credits")
def verify_business_credits(context):
    assert context.db.collection("company").documents[COMPANY_ID]["available_credit"] == 30


@then("the company should receive enterprise credits")
def verify_enterprise_credits(context):
    assert context.db.collection("company").documents[COMPANY_ID]["available_credit"] == 60


@then("the previous unused credits should become expired")
def verify_expired(context):
    assert context.db.collection("company").documents[COMPANY_ID]["expired_credit"] == 6


@then("a completed card payment should be saved")
def verify_payment_saved(context):
    payment = context.db.collection("payment").documents["in_test"]

    assert payment["status"] == "COMPLETED"
    assert payment["payment_method"] == "Card"


@then("company credits should not be updated again")
def verify_duplicate_ignored(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["available_credit"] == 4
    assert company["expired_credit"] == 2


@then("no payment should be saved")
def verify_no_payment(context):
    assert context.db.collection("payment").documents == {}


@then("the company credits should remain unchanged")
def verify_unknown_plan(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["available_credit"] == 4
    assert company["expired_credit"] == 2


@then("the company subscription status should become payment failed")
def verify_failed_status(context):
    assert (
        context.db.collection("company").documents[COMPANY_ID]["subscription_status"]
        == "PAYMENT_FAILED"
    )


@then("the company subscription status and cancellation flag should be updated")
def verify_subscription_update(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["subscription_status"] == "ACTIVE"
    assert company["cancel_at_period_end"] is True
    assert company["subscription_plan"] == "business"


@then("the subscription should be cancelled")
def verify_cancelled(context):
    company = context.db.collection("company").documents[COMPANY_ID]

    assert company["subscription_plan"] == ""
    assert company["subscription_status"] == "CANCELLED"
    assert company["available_credit"] == 0


@then("remaining credits should become expired")
def verify_remaining_expired(context):
    assert context.db.collection("company").documents[COMPANY_ID]["expired_credit"] == 8
