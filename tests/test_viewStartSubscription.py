import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when

# ============================================================
# Load the actual Stripe route without connecting to Firebase
# ============================================================


def load_subscription_module():
    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")

        if (
            "def start_subscription(" in text
            and "def employer_plans(" in text
            and "def preview_subscription_change(" in text
        ):
            module_name = "job_portal_web.backend.routes." + path.stem

            # firestore.client() is called during import.
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client
            firestore_module.client = lambda: None

            try:
                return importlib.import_module(module_name)
            finally:
                firestore_module.client = original_client

    raise ImportError("Cannot find the Stripe subscription route file.")


subscription_module = load_subscription_module()

scenarios("features/viewStartSubscription.feature")

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


# ============================================================
# Fake Firestore
# ============================================================


class FakeSnapshot:
    def __init__(self, data=None):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data or {})


class FakeDocument:
    def __init__(self, collection, document_id):
        self.collection = collection
        self.document_id = document_id

    def get(self):
        return FakeSnapshot(self.collection.data.get(self.document_id))

    def update(self, values):
        self.collection.data.setdefault(self.document_id, {}).update(values)


class FakeCollection:
    def __init__(self, data=None):
        self.data = data or {}

    def document(self, document_id):
        return FakeDocument(self, document_id)


class FakeDB:
    def __init__(self, company=None):
        self.company = FakeCollection({COMPANY_ID: company} if company is not None else {})

    def collection(self, name):
        if name == "company":
            return self.company
        return FakeCollection()


class FakeTemplates:
    def TemplateResponse(self, request, name, context):
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
        self.company = {}
        self.db = None
        self.response = None
        self.error = None
        self.checkout_args = None
        self.created_customer = False


@pytest.fixture
def context():
    return Context()


@pytest.fixture(autouse=True)
def common_setup(monkeypatch):
    monkeypatch.setattr(
        subscription_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    monkeypatch.setattr(
        subscription_module,
        "templates",
        FakeTemplates(),
    )


def install_company(monkeypatch, context, company):
    context.company = company
    context.db = FakeDB(company)

    monkeypatch.setattr(
        subscription_module,
        "db",
        context.db,
    )


def call_start(context, plan_name):
    try:
        context.response = subscription_module.start_subscription(
            FakeRequest(),
            plan_name,
        )
    except HTTPException as exc:
        context.error = exc


# ============================================================
# BDD GIVEN
# ============================================================


@given("an employer company exists")
def employer_exists(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "subscription_plan": "",
        },
    )


@given("an employer company has a business subscription")
def business_subscription(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "subscription_plan": "Business",
            "subscription_status": "ACTIVE",
        },
    )


@given("an employer company has no Stripe subscription")
def no_subscription(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": "cus_existing",
            "stripe_subscription_id": "",
            "subscription_plan": "",
        },
    )


@given("an employer company has no Stripe customer")
def no_customer(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "businessEmail": "abc@example.com",
            "stripe_customer_id": "",
            "stripe_subscription_id": "",
        },
    )

    def create_customer(**kwargs):
        context.created_customer = True
        return SimpleNamespace(id="cus_new")

    monkeypatch.setattr(
        subscription_module.stripe.Customer,
        "create",
        create_customer,
    )


@given("an employer company already has a Stripe customer")
def existing_customer(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "stripe_customer_id": "cus_existing",
            "stripe_subscription_id": "",
        },
    )


@given("an employer company already has a Stripe subscription")
def existing_subscription(monkeypatch, context):
    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "stripe_customer_id": "cus_existing",
            "stripe_subscription_id": "sub_existing",
        },
    )


@given("the starter Stripe price is configured")
def starter_price(monkeypatch):
    monkeypatch.setitem(
        subscription_module.PLANS["starter"],
        "stripe_price_id",
        "price_starter_test",
    )


@given("the starter Stripe price is not configured")
def missing_price(monkeypatch):
    monkeypatch.setitem(
        subscription_module.PLANS["starter"],
        "stripe_price_id",
        None,
    )


# ============================================================
# BDD WHEN
# ============================================================


@when("the employer opens the subscription plans page")
def open_plans(context):
    context.response = subscription_module.employer_plans(FakeRequest())


@when("the employer starts the starter subscription")
def start_starter(monkeypatch, context):
    def create_checkout(**kwargs):
        context.checkout_args = kwargs
        return SimpleNamespace(url="https://checkout.stripe.test/session")

    monkeypatch.setattr(
        subscription_module.stripe.checkout.Session,
        "create",
        create_checkout,
    )

    call_start(context, "starter")


@when("the employer starts an invalid subscription plan")
def start_invalid(context):
    call_start(context, "not-a-plan")


# ============================================================
# BDD THEN
# ============================================================


@then("the system should display all available subscription plans")
def plans_displayed(context):
    assert context.response["template"] == "employerPlans.html"
    plans = context.response["context"]["plans"]

    assert "starter" in plans
    assert "business" in plans
    assert "enterprise" in plans
    assert plans["starter"]["credits"] == 10
    assert plans["business"]["credits"] == 30
    assert plans["enterprise"]["credits"] == 60


@then("the business plan should be identified as the current plan")
def current_plan(context):
    assert context.response["context"]["current_plan"] == "business"


@then("Stripe Checkout should be created using card payment")
def checkout_card(context):
    assert context.checkout_args is not None
    assert context.checkout_args["payment_method_types"] == ["card"]
    assert context.checkout_args["mode"] == "subscription"
    assert context.checkout_args["line_items"][0]["price"] == "price_starter_test"


@then("the employer should be redirected to Stripe Checkout")
def redirected_checkout(context):
    assert context.response.status_code == 303
    assert context.response.headers["location"] == "https://checkout.stripe.test/session"


@then("a Stripe customer should be created")
def customer_created(context):
    assert context.created_customer is True


@then("the Stripe customer ID should be saved to the company")
def customer_saved(context):
    company = context.db.company.data[COMPANY_ID]
    assert company["stripe_customer_id"] == "cus_new"


@then("the existing Stripe customer should be used")
def existing_customer_used(context):
    assert context.checkout_args["customer"] == "cus_existing"


@then("plan not found should be returned")
def plan_not_found(context):
    assert context.error is not None
    assert context.error.status_code == 404
    assert context.error.detail == "Plan not found"


@then("Stripe price configuration error should be returned")
def price_error(context):
    assert context.error is not None
    assert context.error.status_code == 500
    assert "Stripe Price ID" in context.error.detail


@then("the employer should be redirected back to subscription plans")
def redirected_plans(context):
    assert context.response.status_code == 303
    assert context.response.headers["location"] == "/employer-plans"


# ============================================================
# EXTRA DIRECT PYTEST
# ============================================================


def test_plan_configuration_values():
    assert subscription_module.PLANS["starter"]["price"] == 49
    assert subscription_module.PLANS["starter"]["credits"] == 10

    assert subscription_module.PLANS["business"]["price"] == 129
    assert subscription_module.PLANS["business"]["credits"] == 30

    assert subscription_module.PLANS["enterprise"]["price"] == 229
    assert subscription_module.PLANS["enterprise"]["credits"] == 60
