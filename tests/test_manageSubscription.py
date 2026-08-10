import importlib
from pathlib import Path

import pytest
import stripe
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when


def load_subscription_module():
    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")

        if (
            "def cancel_subscription(" in text
            and "def resume_subscription(" in text
            and "def manage_payment_method(" in text
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

scenarios("features/manageSubscription.feature")

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


class FakeDocument:
    def __init__(self, company):
        self.company = company

    def update(self, values):
        self.company.update(values)


class FakeCollection:
    def __init__(self, company):
        self.company = company

    def document(self, document_id):
        return FakeDocument(self.company)


class FakeDB:
    def __init__(self, company):
        self.company = company

    def collection(self, name):
        return FakeCollection(self.company)


class FakeRequest:
    def __init__(self):
        self.session = {
            "user_type": "employer",
            "company_id": COMPANY_ID,
        }


class Context:
    def __init__(self):
        self.company = {}
        self.response = None
        self.error = None
        self.modify_kwargs = None
        self.portal_kwargs = None


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

    monkeypatch.setattr(
        subscription_module,
        "db",
        FakeDB(context.company),
    )


def run_action(context, action):
    try:
        context.response = action(FakeRequest())
    except HTTPException as exc:
        context.error = exc


@given("an employer has an active Stripe subscription")
def active_subscription(context):
    context.company.update({
        "stripe_subscription_id": "sub_test",
        "stripe_customer_id": "cus_test",
        "cancel_at_period_end": False,
    })


@given("an employer has no Stripe subscription")
def no_subscription(context):
    context.company.update({
        "stripe_subscription_id": "",
        "stripe_customer_id": "cus_test",
    })


@given(
    "an employer has a Stripe subscription scheduled for cancellation"
)
def scheduled_subscription(context):
    context.company.update({
        "stripe_subscription_id": "sub_test",
        "stripe_customer_id": "cus_test",
        "cancel_at_period_end": True,
    })


@given("an employer has a Stripe customer")
def stripe_customer(context):
    context.company.update({
        "stripe_customer_id": "cus_test",
    })


@given("an employer has no Stripe customer")
def no_customer(context):
    context.company.update({
        "stripe_customer_id": "",
    })


@given("Stripe fails to cancel the subscription")
def stripe_cancel_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise stripe.error.StripeError(
            "Cancellation failed"
        )

    monkeypatch.setattr(
        subscription_module.stripe.Subscription,
        "modify",
        fail,
    )


@given("Stripe fails to create the billing portal")
def portal_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise stripe.error.StripeError(
            "Portal failed"
        )

    monkeypatch.setattr(
        subscription_module.stripe.billing_portal.Session,
        "create",
        fail,
    )


@when("the employer cancels the subscription")
def cancel(monkeypatch, context):
    if context.error is None:
        # Do not overwrite the failure mock installed by the Given.
        current = (
            subscription_module.stripe.Subscription.modify
        )

        if getattr(current, "__name__", "") != "fail":
            def modify(subscription_id, **kwargs):
                context.modify_kwargs = {
                    "subscription_id": subscription_id,
                    **kwargs,
                }
                return {}

            monkeypatch.setattr(
                subscription_module.stripe.Subscription,
                "modify",
                modify,
            )

    run_action(
        context,
        subscription_module.cancel_subscription,
    )


@when("the employer resumes the subscription")
def resume(monkeypatch, context):
    def modify(subscription_id, **kwargs):
        context.modify_kwargs = {
            "subscription_id": subscription_id,
            **kwargs,
        }
        return {}

    monkeypatch.setattr(
        subscription_module.stripe.Subscription,
        "modify",
        modify,
    )

    run_action(
        context,
        subscription_module.resume_subscription,
    )


@when("the employer manages the payment method")
def manage_payment(monkeypatch, context):
    current = (
        subscription_module.stripe.billing_portal.Session.create
    )

    if getattr(current, "__name__", "") != "fail":
        def create(**kwargs):
            context.portal_kwargs = kwargs
            return type(
                "Portal",
                (),
                {
                    "url":
                    "https://billing.stripe.test/session"
                },
            )()

        monkeypatch.setattr(
            subscription_module.stripe.billing_portal.Session,
            "create",
            create,
        )

    run_action(
        context,
        subscription_module.manage_payment_method,
    )


@then("Stripe should schedule cancellation at period end")
def scheduled(context):
    assert context.modify_kwargs is not None
    assert (
        context.modify_kwargs["subscription_id"]
        == "sub_test"
    )
    assert (
        context.modify_kwargs["cancel_at_period_end"]
        is True
    )


@then("the cancellation flag should be saved")
def flag_saved(context):
    assert (
        context.company["cancel_at_period_end"]
        is True
    )


@then("the employer should be redirected to the credit page")
def cancel_redirect(context):
    assert context.response.status_code == 303
    assert (
        context.response.headers["location"]
        == "/employer-credit?cancel=scheduled"
    )


@then("no active subscription error should be returned")
def no_active_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert (
        context.error.detail
        == "No active subscription found."
    )


@then("the Stripe cancellation error should be returned")
def cancel_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "Cancellation failed" in context.error.detail


@then("Stripe should remove scheduled cancellation")
def remove_cancel(context):
    assert context.modify_kwargs is not None
    assert (
        context.modify_kwargs["cancel_at_period_end"]
        is False
    )


@then("the cancellation flag should be cleared")
def flag_cleared(context):
    assert (
        context.company["cancel_at_period_end"]
        is False
    )


@then("the employer should be redirected after resuming")
def resume_redirect(context):
    assert context.response.status_code == 303
    assert (
        context.response.headers["location"]
        == "/employer-credit?subscription=resumed"
    )


@then("no subscription error should be returned")
def no_subscription_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert context.error.detail == "No subscription found."


@then("a Stripe billing portal session should be created")
def portal_created(context):
    assert context.portal_kwargs is not None
    assert context.portal_kwargs["customer"] == "cus_test"


@then(
    "the employer should be redirected to the Stripe billing portal"
)
def portal_redirect(context):
    assert context.response.status_code == 303
    assert (
        context.response.headers["location"]
        == "https://billing.stripe.test/session"
    )


@then("Stripe customer not found should be returned")
def customer_missing(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "Stripe customer account not found" in context.error.detail


@then("the Stripe billing portal error should be returned")
def portal_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert "Portal failed" in context.error.detail