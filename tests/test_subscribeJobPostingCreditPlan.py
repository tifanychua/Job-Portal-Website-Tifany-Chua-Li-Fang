import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD EMPLOYER PLAN MODULE
# ============================================================
#
# Handles:
# - start_subscription()
# - Stripe Checkout
# - Stripe customer creation
#
# ============================================================


def load_subscription_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def start_subscription(" in text and "def employer_plans(" in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client

            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)

            finally:
                firestore_module.client = original_client

    raise ImportError("Cannot find subscription plan module.")


# ============================================================
# LOAD STRIPE PAYMENT / WEBHOOK MODULE
# ============================================================
#
# Handles:
# - stripe_webhook()
# - handle_invoice_paid()
# - handle_invoice_failed()
#
# ============================================================


def load_payment_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    matches = []

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if (
            "def stripe_webhook(" in text
            and "def handle_invoice_paid(" in text
            and "def handle_invoice_failed(" in text
        ):
            matches.append(path)

    if not matches:
        raise ImportError("Cannot find Stripe payment module.")

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
            sys.modules.pop(
                "job_portal_web.backend.database",
                None,
            )


subscription_module = load_subscription_module()

payment_module = load_payment_module()


# ============================================================
# FEATURE
# ============================================================

scenarios("features/subscribeJobPostingCreditPlan.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

CUSTOMER_ID = "cus_test"

SUBSCRIPTION_ID = "sub_test"

INVOICE_ID = "in_test"

STARTER_PRICE = "price_starter_test"


# ============================================================
# FAKE FIRESTORE SNAPSHOT
# ============================================================


class FakeSnapshot:
    def __init__(
        self,
        document_id,
        data=None,
        reference=None,
    ):

        self.id = document_id

        self._data = data

        self.reference = reference

        self.exists = data is not None

    def to_dict(self):

        return dict(self._data or {})


# ============================================================
# FAKE FIRESTORE DOCUMENT
# ============================================================


class FakeDocument:
    def __init__(
        self,
        collection,
        document_id,
    ):

        self.collection = collection

        self.id = document_id

    def get(self):

        data = self.collection.documents.get(self.id)

        return FakeSnapshot(
            self.id,
            data,
            self,
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

        document.update(values)


# ============================================================
# FAKE FIRESTORE QUERY
# ============================================================


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
            self.limit_count,
        )

    def limit(
        self,
        count,
    ):

        return FakeQuery(
            self.collection,
            self.filters,
            count,
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
                reference = FakeDocument(
                    self.collection,
                    document_id,
                )

                results.append(
                    FakeSnapshot(
                        document_id,
                        data,
                        reference,
                    )
                )

        if self.limit_count is not None:
            results = results[: self.limit_count]

        return iter(results)


# ============================================================
# FAKE FIRESTORE COLLECTION
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

            document_id = f"{self.prefix}{self.counter:03d}"

        return FakeDocument(
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

        return FakeQuery(self).stream()

    def add(
        self,
        data,
    ):

        self.counter += 1

        document_id = f"{self.prefix}{self.counter:03d}"

        saved = dict(data)

        self.documents[document_id] = saved

        self.added.append(saved)

        return (
            FakeDocument(
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
        company,
    ):

        self.collections = {
            "company": FakeCollection(
                {COMPANY_ID: company},
                prefix="COMPANY",
            ),
            "payment": FakeCollection(prefix="PAYMENT"),
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
        }


# ============================================================
# CONTEXT
# ============================================================


class Context:
    def __init__(self):

        self.db = None

        self.company = None

        self.response = None

        self.checkout_args = None

        self.created_customer = False

        self.selected_plan = "starter"

        self.old_credit = 0


@pytest.fixture
def context():

    return Context()


# ============================================================
# COMMON SETUP
# ============================================================


@pytest.fixture(autouse=True)
def common_setup(
    monkeypatch,
):

    monkeypatch.setattr(
        subscription_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    monkeypatch.setitem(
        subscription_module.PLANS["starter"],
        "stripe_price_id",
        STARTER_PRICE,
    )

    if hasattr(
        payment_module,
        "PLANS",
    ):
        monkeypatch.setitem(
            payment_module.PLANS["starter"],
            "stripe_price_id",
            STARTER_PRICE,
        )


# ============================================================
# INSTALL COMPANY
# ============================================================


def install_company(
    monkeypatch,
    context,
    company,
):

    context.company = company

    context.db = FakeDB(company)

    monkeypatch.setattr(
        subscription_module,
        "db",
        context.db,
    )

    monkeypatch.setattr(
        payment_module,
        "db",
        context.db,
    )

    def fake_get_company_by_customer_id(
        customer_id,
    ):

        company_data = context.db.collection("company").documents[COMPANY_ID]

        if company_data.get("stripe_customer_id") != customer_id:
            return None

        reference = context.db.collection("company").document(COMPANY_ID)

        return FakeSnapshot(
            COMPANY_ID,
            company_data,
            reference,
        )

    monkeypatch.setattr(
        payment_module,
        "get_company_by_customer_id",
        fake_get_company_by_customer_id,
    )

    monkeypatch.setitem(
        payment_module.handle_invoice_paid.__globals__,
        "get_company_by_customer_id",
        fake_get_company_by_customer_id,
    )

    monkeypatch.setitem(
        payment_module.handle_invoice_failed.__globals__,
        "get_company_by_customer_id",
        fake_get_company_by_customer_id,
    )


# ============================================================
# HELPER: COMPANY RECORD
# ============================================================


def company_record(
    context,
):

    return context.db.collection("company").documents[COMPANY_ID]


# ============================================================
# HELPER: INSTALL STRIPE CHECKOUT
# ============================================================


def install_checkout(
    monkeypatch,
    context,
):

    def create_checkout(
        **kwargs,
    ):

        context.checkout_args = kwargs

        return SimpleNamespace(url=("https://checkout.stripe.test/session"))

    monkeypatch.setattr(
        subscription_module.stripe.checkout.Session,
        "create",
        create_checkout,
    )


# ============================================================
# HELPER: INSTALL STRIPE SUBSCRIPTION
# ============================================================


def install_stripe_subscription(
    monkeypatch,
    plan_name="starter",
):

    subscription = SimpleNamespace(
        id=SUBSCRIPTION_ID,
        metadata={"plan": plan_name},
        items=SimpleNamespace(
            data=[
                SimpleNamespace(
                    current_period_start=1767225600,
                    current_period_end=1769904000,
                )
            ]
        ),
    )

    monkeypatch.setattr(
        payment_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id: subscription,
    )


# ============================================================
# HELPER: SUCCESSFUL STRIPE INVOICE
# ============================================================


def paid_invoice():

    return SimpleNamespace(
        id=INVOICE_ID,
        customer=CUSTOMER_ID,
        subscription=SUBSCRIPTION_ID,
        amount_paid=4900,
        currency="myr",
        parent=None,
    )


# ============================================================
# HELPER: FAILED STRIPE INVOICE
# ============================================================


def failed_invoice():

    return SimpleNamespace(
        id="in_failed",
        customer=CUSTOMER_ID,
        subscription=SUBSCRIPTION_ID,
    )


# ============================================================
# HELPER: PROCESS SUCCESSFUL PAYMENT
# ============================================================


def process_successful_payment(
    monkeypatch,
    context,
):

    install_stripe_subscription(
        monkeypatch,
        "starter",
    )

    payment_module.handle_invoice_paid(paid_invoice())


# ============================================================
# GIVEN
# ============================================================


@given("the employer has selected a job posting credit plan")
def selected_plan(
    monkeypatch,
    context,
):

    context.selected_plan = "starter"

    # Do not overwrite company if
    # another Given already installed it
    if context.db is None:
        install_company(
            monkeypatch,
            context,
            {
                "companyName": "ABC Technology",
                "businessEmail": "abc@example.com",
                "stripe_customer_id": CUSTOMER_ID,
                "stripe_subscription_id": "",
                "subscription_plan": "",
                "subscription_status": "",
                "total_credit": 0,
                "available_credit": 0,
                "used_credit": 0,
                "expired_credit": 0,
            },
        )


@given("the employer is subscribing to a job posting credit plan")
def subscribing_to_plan(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": CUSTOMER_ID,
            "stripe_subscription_id": "",
            "subscription_plan": "",
            "subscription_status": "",
            "total_credit": 0,
            "available_credit": 0,
            "used_credit": 0,
            "expired_credit": 0,
        },
    )

    context.selected_plan = "starter"


@given("the employer has successfully subscribed to a job posting credit plan")
def successfully_subscribed(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": CUSTOMER_ID,
            "stripe_subscription_id": "",
            "subscription_plan": "",
            "subscription_status": "",
            "total_credit": 0,
            "available_credit": 0,
            "used_credit": 0,
            "expired_credit": 0,
        },
    )

    process_successful_payment(
        monkeypatch,
        context,
    )


@given("the employer already has a Stripe customer account")
def existing_customer(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": CUSTOMER_ID,
            "stripe_subscription_id": "",
            "subscription_plan": "",
            "subscription_status": "",
            "total_credit": 0,
            "available_credit": 0,
            "used_credit": 0,
            "expired_credit": 0,
        },
    )


@given("the employer does not have a Stripe customer account")
def no_customer(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": "",
            "stripe_subscription_id": "",
            "subscription_plan": "",
            "subscription_status": "",
            "total_credit": 0,
            "available_credit": 0,
            "used_credit": 0,
            "expired_credit": 0,
        },
    )

    def create_customer(
        **kwargs,
    ):

        context.created_customer = True

        return SimpleNamespace(id="cus_new")

    monkeypatch.setattr(
        subscription_module.stripe.Customer,
        "create",
        create_customer,
    )


# ============================================================
# WHEN
# ============================================================


@when("the employer completes the subscription payment successfully")
def complete_successful_payment(
    monkeypatch,
    context,
):

    process_successful_payment(
        monkeypatch,
        context,
    )


@when("the employer proceeds to payment")
def proceed_to_payment(
    monkeypatch,
    context,
):

    install_checkout(
        monkeypatch,
        context,
    )

    context.response = subscription_module.start_subscription(
        FakeRequest(),
        context.selected_plan,
    )


@when("the subscription payment is unsuccessful")
def payment_unsuccessful(
    monkeypatch,
    context,
):

    # Save credit before failed payment
    context.old_credit = company_record(context).get(
        "available_credit",
        0,
    )

    # Get fake company reference
    company_reference = context.db.collection("company").document(COMPANY_ID)

    company_snapshot = FakeSnapshot(
        COMPANY_ID,
        company_record(context),
        company_reference,
    )

    # Fake Stripe customer -> company lookup
    def fake_company_lookup(
        customer_id,
    ):

        if customer_id == CUSTOMER_ID:
            return company_snapshot

        return None

    monkeypatch.setattr(
        payment_module,
        "get_company_by_customer_id",
        fake_company_lookup,
    )

    monkeypatch.setitem(
        payment_module.handle_invoice_failed.__globals__,
        "get_company_by_customer_id",
        fake_company_lookup,
    )

    # Execute real backend failure handler
    payment_module.handle_invoice_failed(failed_invoice())


@when("the employer views the credit management page")
def view_credit_page(
    context,
):

    assert context.db is not None


@when("the employer proceeds with the subscription")
def proceed_subscription(
    monkeypatch,
    context,
):

    install_checkout(
        monkeypatch,
        context,
    )

    context.response = subscription_module.start_subscription(
        FakeRequest(),
        "starter",
    )


# ============================================================
# THEN
# ============================================================


@then("the system should activate the selected subscription plan")
def plan_activated(
    context,
):

    company = company_record(context)

    assert company["subscription_plan"] == "starter"

    assert company["subscription_status"] == "ACTIVE"

    assert company["stripe_subscription_id"] == SUBSCRIPTION_ID


@then("the system should add the plan credits to the employer's account balance")
def credits_added(
    context,
):

    company = company_record(context)

    assert company["total_credit"] == 10

    assert company["available_credit"] == 10

    assert company["used_credit"] == 0

    payment = context.db.collection("payment").documents.get(INVOICE_ID)

    assert payment is not None

    assert payment["status"] == "COMPLETED"

    assert payment["payment_method"] == "Card"

    assert payment["credits"] == 10


@then("the system should process the payment securely through Stripe Checkout using card payment")
def secure_payment(
    context,
):

    assert context.checkout_args is not None

    assert context.checkout_args["payment_method_types"] == ["card"]

    assert context.checkout_args["mode"] == "subscription"

    assert context.checkout_args["line_items"][0]["price"] == STARTER_PRICE


@then("the system should not directly expose or store sensitive card information")
def card_information_not_exposed(
    context,
):

    sensitive_fields = {
        "card_number",
        "cardNumber",
        "cvv",
        "cvc",
        "expiry",
        "expiry_date",
    }

    for field in sensitive_fields:
        assert field not in context.checkout_args

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "https://checkout.stripe.test/session"


@then("the system should mark the subscription payment as unsuccessful")
def subscription_failed(
    context,
):

    company = company_record(context)

    assert company["subscription_status"] == "PAYMENT_FAILED"


@then("the system should not add the plan credits to the employer's account balance")
def failure_does_not_add_credit(
    context,
):

    company = company_record(context)

    # Balance should remain unchanged
    assert (
        company.get(
            "available_credit",
            0,
        )
        == context.old_credit
    )

    # Still zero
    assert (
        company.get(
            "available_credit",
            0,
        )
        == 0
    )

    # Failed payment should not create
    # successful invoice payment
    assert INVOICE_ID not in (context.db.collection("payment").documents)


@then("the system should display the updated job posting credit balance")
def updated_balance(
    context,
):

    company = company_record(context)

    assert company["available_credit"] == 10

    assert company["total_credit"] == 10

    assert company["subscription_status"] == "ACTIVE"


@then("the system should reuse the existing Stripe customer for the subscription")
def customer_reused(
    context,
):

    assert context.checkout_args is not None

    assert context.checkout_args["customer"] == CUSTOMER_ID


@then("the system should create a Stripe customer for the employer")
def customer_created(
    context,
):

    assert context.created_customer is True


@then("the Stripe customer ID should be saved to the employer account")
def new_customer_saved(
    context,
):

    company = company_record(context)

    assert company["stripe_customer_id"] == "cus_new"
