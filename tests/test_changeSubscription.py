import importlib
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when

# ============================================================
# Load Subscription Module
# ============================================================


def load_subscription_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        # We only need the module containing
        # change_subscription()
        if "def change_subscription(" not in text:
            continue

        import firebase_admin.firestore as firestore_module

        original_client = firestore_module.client

        # Prevent real Firestore connection
        # during module import
        firestore_module.client = lambda: None

        try:

            module = importlib.import_module("job_portal_web.backend.routes." + path.stem)

            return module

        finally:

            firestore_module.client = original_client

    raise ImportError("Cannot find subscription route module.")


subscription_module = load_subscription_module()


# ============================================================
# Feature File
# ============================================================

scenarios("features/changeSubscription.feature")


# ============================================================
# Constants
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

SUBSCRIPTION_ID = "sub_test"

SUBSCRIPTION_ITEM_ID = "si_test"

CUSTOMER_ID = "cus_test"

PRORATION_DATE = 1786500000


# ============================================================
# Fake Request
# ============================================================


class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


# ============================================================
# Context
# ============================================================


class Context:

    def __init__(self):

        self.company = None

        self.response = None

        self.error = None

        self.modify_args = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# Common Setup
# ============================================================


@pytest.fixture(autouse=True)
def common_setup(
    monkeypatch,
    context,
):

    # --------------------------------------------------------
    # Fake current employer
    # --------------------------------------------------------

    monkeypatch.setattr(
        subscription_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    # --------------------------------------------------------
    # Fake company retrieval
    # --------------------------------------------------------

    monkeypatch.setattr(
        subscription_module,
        "get_company",
        lambda company_id: context.company,
    )

    # --------------------------------------------------------
    # Stripe Price IDs
    # --------------------------------------------------------

    monkeypatch.setitem(
        subscription_module.PLANS["starter"],
        "stripe_price_id",
        "price_starter_test",
    )

    monkeypatch.setitem(
        subscription_module.PLANS["business"],
        "stripe_price_id",
        "price_business_test",
    )


# ============================================================
# Helper - Call Change Subscription
# ============================================================


def call_change(
    context,
    plan_name,
):

    context.response = None
    context.error = None

    try:

        context.response = subscription_module.change_subscription(
            FakeRequest(),
            plan_name,
            PRORATION_DATE,
        )

    except HTTPException as exc:

        context.error = exc


# ============================================================
# GIVEN
# ============================================================


@given("the employer currently uses the starter plan")
def employer_uses_starter(
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn. Bhd.",
        "subscription_plan": "starter",
        "stripe_subscription_id": SUBSCRIPTION_ID,
        "stripe_customer_id": CUSTOMER_ID,
    }


@given("the employer currently uses the starter plan " "without a Stripe subscription")
def employer_without_subscription(
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn. Bhd.",
        "subscription_plan": "starter",
        "stripe_subscription_id": "",
        "stripe_customer_id": CUSTOMER_ID,
    }


# ============================================================
# GIVEN - Active Stripe Subscription
# ============================================================


@given("an active Stripe subscription exists")
def active_stripe_subscription(
    monkeypatch,
):

    # IMPORTANT:
    # Get the actual stripe object used inside
    # change_subscription().
    route_globals = subscription_module.change_subscription.__globals__

    stripe_used_by_route = route_globals["stripe"]

    def fake_retrieve(
        subscription_id,
    ):

        assert subscription_id == SUBSCRIPTION_ID

        return {
            "id": SUBSCRIPTION_ID,
            "items": {"data": [{"id": SUBSCRIPTION_ITEM_ID}]},
        }

    monkeypatch.setattr(
        stripe_used_by_route.Subscription,
        "retrieve",
        fake_retrieve,
    )


# ============================================================
# WHEN - Change To Business
# ============================================================


@when("the employer changes to the business plan")
def change_to_business(
    monkeypatch,
    context,
):

    # --------------------------------------------------------
    # Get exact Stripe object used by production function
    # --------------------------------------------------------

    route_globals = subscription_module.change_subscription.__globals__

    stripe_used_by_route = route_globals["stripe"]

    # --------------------------------------------------------
    # Fake Stripe modify()
    # --------------------------------------------------------

    def fake_modify(
        subscription_id,
        **kwargs,
    ):

        context.modify_args = {
            "subscription_id": subscription_id,
            **kwargs,
        }

        return {"id": subscription_id}

    monkeypatch.setattr(
        stripe_used_by_route.Subscription,
        "modify",
        fake_modify,
    )

    # --------------------------------------------------------
    # Execute
    # --------------------------------------------------------

    call_change(
        context,
        "business",
    )


# ============================================================
# WHEN - Change To Same Plan
# ============================================================


@when("the employer changes to the starter plan")
def change_to_starter(
    context,
):

    call_change(
        context,
        "starter",
    )


# ============================================================
# WHEN - Change To Invalid Plan
# ============================================================


@when("the employer changes to an invalid plan")
def change_to_invalid_plan(
    context,
):

    call_change(
        context,
        "invalid",
    )


# ============================================================
# THEN - Stripe Modified
# ============================================================


@then("Stripe should modify the subscription " "to the business plan")
def stripe_modifies_subscription(
    context,
):

    # --------------------------------------------------------
    # No HTTPException expected
    # --------------------------------------------------------

    assert context.error is None

    # --------------------------------------------------------
    # modify() must actually be called
    # --------------------------------------------------------

    assert context.modify_args is not None

    # --------------------------------------------------------
    # Correct Stripe subscription
    # --------------------------------------------------------

    assert context.modify_args["subscription_id"] == SUBSCRIPTION_ID

    # --------------------------------------------------------
    # Correct subscription item
    # --------------------------------------------------------

    items = context.modify_args["items"]

    assert len(items) == 1

    assert items[0]["id"] == SUBSCRIPTION_ITEM_ID

    # --------------------------------------------------------
    # Correct Business Stripe Price
    # --------------------------------------------------------

    assert items[0]["price"] == "price_business_test"


# ============================================================
# THEN - Proration
# ============================================================


@then("proration should be applied " "to the plan change")
def proration_should_be_applied(
    context,
):

    assert context.modify_args is not None

    assert context.modify_args["proration_behavior"] == "always_invoice"

    assert context.modify_args["payment_behavior"] == "pending_if_incomplete"

    assert context.modify_args["proration_date"] == PRORATION_DATE


# ============================================================
# THEN - Processing Redirect
# ============================================================


@then("the employer should be redirected " "while the plan change is processing")
def processing_redirect(
    context,
):

    assert context.error is None

    assert context.response is not None

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/employer-credit" "?plan_change=processing"


# ============================================================
# THEN - Same Plan
# ============================================================


@then("the employer should be redirected " "back to subscription plans")
def same_plan_redirect(
    context,
):

    assert context.error is None

    assert context.response is not None

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/employer-plans"


# ============================================================
# THEN - Missing Stripe Subscription
# ============================================================


@then("starting a Stripe subscription first " "should be required")
def stripe_subscription_required(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 400

    assert "Start a Stripe subscription first" in context.error.detail


# ============================================================
# THEN - Invalid Plan
# ============================================================


@then("plan not found should be returned")
def plan_not_found(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 404

    assert context.error.detail == "Plan not found"
