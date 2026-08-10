import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when


def load_subscription_module():
    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")

        if (
            "def change_subscription(" in text
            and "def preview_subscription_change(" in text
        ):
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client
            firestore_module.client = lambda: None

            try:
                return importlib.import_module(
                    "job_portal_web.backend.routes."
                    + path.stem
                )
            finally:
                firestore_module.client = original_client

    raise ImportError("Cannot find subscription route module.")


subscription_module = load_subscription_module()

scenarios("features/changeSubscription.feature")

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


class FakeRequest:
    def __init__(self):
        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


class Context:
    def __init__(self):
        self.company = None
        self.response = None
        self.error = None
        self.modify_args = None
        self.preview = None


@pytest.fixture
def context():
    return Context()


@pytest.fixture(autouse=True)
def common_setup(monkeypatch, context):
    monkeypatch.setattr(
        subscription_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    monkeypatch.setattr(
        subscription_module,
        "get_company",
        lambda company_id: context.company,
    )

    monkeypatch.setitem(
        subscription_module.PLANS["business"],
        "stripe_price_id",
        "price_business_test",
    )

    monkeypatch.setitem(
        subscription_module.PLANS["starter"],
        "stripe_price_id",
        "price_starter_test",
    )


def call_preview(context, plan):
    try:
        context.response = (
            subscription_module.preview_subscription_change(
                FakeRequest(),
                plan,
            )
        )
    except HTTPException as exc:
        context.error = exc


def call_change(context, plan):
    try:
        context.response = (
            subscription_module.change_subscription(
                FakeRequest(),
                plan,
            )
        )
    except HTTPException as exc:
        context.error = exc


def active_subscription():
    return {
        "items": {
            "data": [
                {
                    "id": "si_test"
                }
            ]
        }
    }


@given("the employer currently uses the starter plan")
def starter_company(context):
    context.company = {
        "subscription_plan": "starter",
        "stripe_subscription_id": "sub_test",
        "stripe_customer_id": "cus_test",
    }


@given(
    "the employer currently uses the starter plan without a Stripe subscription"
)
def starter_without_subscription(context):
    context.company = {
        "subscription_plan": "starter",
        "stripe_subscription_id": "",
        "stripe_customer_id": "cus_test",
    }


@given("an active Stripe subscription exists")
def stripe_subscription(monkeypatch):
    monkeypatch.setattr(
        subscription_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id: active_subscription(),
    )


@given("a Stripe subscription without items exists")
def stripe_without_items(monkeypatch):
    monkeypatch.setattr(
        subscription_module.stripe.Subscription,
        "retrieve",
        lambda subscription_id: {
            "items": {"data": []}
        },
    )


def install_preview(monkeypatch, adjustment=-3000):
    proration_parent = SimpleNamespace(
        subscription_item_details=SimpleNamespace(
            proration=True
        )
    )

    normal_parent = SimpleNamespace(
        subscription_item_details=SimpleNamespace(
            proration=False
        )
    )

    preview = SimpleNamespace(
        amount_due=9900,
        subtotal=12900,
        lines=SimpleNamespace(
            data=[
                SimpleNamespace(
                    amount=adjustment,
                    parent=proration_parent,
                ),
                SimpleNamespace(
                    amount=12900,
                    parent=normal_parent,
                ),
            ]
        ),
    )

    monkeypatch.setattr(
        subscription_module.stripe.Invoice,
        "create_preview",
        lambda **kwargs: preview,
    )


def install_card(monkeypatch):
    payment_method = SimpleNamespace(
        card=SimpleNamespace(
            brand="visa",
            last4="4242",
        )
    )

    customer = SimpleNamespace(
        invoice_settings=SimpleNamespace(
            default_payment_method=payment_method
        )
    )

    monkeypatch.setattr(
        subscription_module.stripe.Customer,
        "retrieve",
        lambda *args, **kwargs: customer,
    )


@when("the employer previews the business plan")
def preview_business(monkeypatch, context):
    install_preview(monkeypatch)
    install_card(monkeypatch)
    call_preview(context, "business")


@when(
    "the employer previews the business plan with an unused subscription credit"
)
def preview_proration(monkeypatch, context):
    install_preview(monkeypatch, adjustment=-3000)
    install_card(monkeypatch)
    call_preview(context, "business")


@when("the employer previews an invalid plan")
def preview_invalid(context):
    call_preview(context, "invalid")


@when("the employer previews the starter plan")
def preview_same(context):
    call_preview(context, "starter")


@when("the employer changes to the business plan")
def change_business(monkeypatch, context):
    def modify(subscription_id, **kwargs):
        context.modify_args = {
            "subscription_id": subscription_id,
            **kwargs,
        }
        return {"id": subscription_id}

    monkeypatch.setattr(
        subscription_module.stripe.Subscription,
        "modify",
        modify,
    )

    call_change(context, "business")


@when("the employer changes to the starter plan")
def change_same(context):
    call_change(context, "starter")


@then("the preview should display the business plan information")
def preview_plan_info(context):
    data = context.response.body.decode("utf-8")
    assert '"plan_name":"Business Pack"' in data
    assert '"plan_price":129.0' in data


@then("Stripe amounts should be converted from cents")
def cents_converted(context):
    data = context.response.body.decode("utf-8")
    assert '"subtotal":129.0' in data
    assert '"amount_due":99.0' in data


@then("the saved card should be displayed")
def card_display(context):
    data = context.response.body.decode("utf-8")
    assert "VISA" in data
    assert "4242" in data


@then("the negative proration adjustment should be returned")
def adjustment(context):
    data = context.response.body.decode("utf-8")
    assert '"adjustment":-30.0' in data


@then("plan not found should be returned")
def plan_not_found(context):
    assert context.error is not None
    assert context.error.status_code == 404


@then("current plan preview should be rejected")
def same_preview_rejected(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "already your current plan" in context.error.detail


@then("missing Stripe subscription should be returned")
def no_subscription(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "No active Stripe" in context.error.detail


@then("missing subscription item should be returned")
def no_item(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "Subscription item" in context.error.detail


@then("Stripe should modify the subscription with proration")
def modified_with_proration(context):
    assert context.modify_args is not None
    assert context.modify_args["subscription_id"] == "sub_test"
    assert (
        context.modify_args["proration_behavior"]
        == "always_invoice"
    )
    assert (
        context.modify_args["payment_behavior"]
        == "pending_if_incomplete"
    )
    assert (
        context.modify_args["items"][0]["price"]
        == "price_business_test"
    )


@then(
    "the employer should be redirected while the plan change is processing"
)
def processing_redirect(context):
    assert context.response.status_code == 303
    assert (
        context.response.headers["location"]
        == "/employer-credit?plan_change=processing"
    )


@then(
    "the employer should be redirected back to subscription plans"
)
def same_plan_redirect(context):
    assert context.response.status_code == 303
    assert (
        context.response.headers["location"]
        == "/employer-plans"
    )


@then("starting a Stripe subscription first should be required")
def stripe_required(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "Start a Stripe subscription first" in context.error.detail