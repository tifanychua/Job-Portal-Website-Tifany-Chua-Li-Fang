import asyncio
import importlib
import json
import sys
import types
from pathlib import Path

import pytest
import stripe
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when


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
            "Could not find the Stripe route module in src/job_portal_web/backend/routes."
        )

    module_name = "job_portal_web.backend.routes." + matches[0].stem

    # Prevent the route import from requiring a real Firebase connection.
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


scenarios("features/stripeWebhook.feature")


class FakeRequest:
    def __init__(self):
        self.headers = {"stripe-signature": "test-signature"}

    async def body(self):
        return b'{"id":"evt_test"}'


class Context:
    def __init__(self):
        self.response = None
        self.error = None
        self.called = []
        self.event = None


@pytest.fixture
def context():
    return Context()


def run_webhook():
    return asyncio.run(stripe_module.stripe_webhook(FakeRequest()))


def process_error(context):
    try:
        context.response = run_webhook()
    except HTTPException as exc:
        context.error = exc


# ============================================================
# NORMAL PYTEST TESTS
# ============================================================


@pytest.mark.parametrize(
    "event_type,handler_name",
    [
        (
            "checkout.session.completed",
            "handle_checkout_completed",
        ),
        (
            "invoice.paid",
            "handle_invoice_paid",
        ),
        (
            "invoice.payment_failed",
            "handle_invoice_failed",
        ),
        (
            "customer.subscription.updated",
            "handle_subscription_updated",
        ),
        (
            "customer.subscription.deleted",
            "handle_subscription_deleted",
        ),
    ],
)
def test_webhook_routes_known_events(
    monkeypatch,
    event_type,
    handler_name,
):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        "whsec_test",
    )

    event_object = {"id": "object_001"}

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        lambda **kwargs: {
            "type": event_type,
            "data": {"object": event_object},
        },
    )

    called = []

    monkeypatch.setattr(
        stripe_module,
        handler_name,
        lambda obj: called.append(obj),
    )

    response = run_webhook()

    assert called == [event_object]
    assert json.loads(response.body) == {"received": True}


def test_unknown_webhook_event_is_acknowledged(
    monkeypatch,
):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        "whsec_test",
    )

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        lambda **kwargs: {
            "type": "customer.created",
            "data": {"object": {"id": "cus_1"}},
        },
    )

    response = run_webhook()

    assert json.loads(response.body) == {"received": True}


def test_missing_webhook_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        None,
    )

    with pytest.raises(HTTPException) as exc:
        run_webhook()

    assert exc.value.status_code == 500


def test_invalid_payload(
    monkeypatch,
):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        "whsec_test",
    )

    def invalid(**kwargs):
        raise ValueError("bad payload")

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        invalid,
    )

    with pytest.raises(HTTPException) as exc:
        run_webhook()

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid Stripe payload"


def test_invalid_signature(
    monkeypatch,
):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        "whsec_test",
    )

    def invalid(**kwargs):
        raise stripe.error.SignatureVerificationError(
            "bad signature",
            "sig",
        )

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        invalid,
    )

    with pytest.raises(HTTPException) as exc:
        run_webhook()

    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid Stripe signature"


# ============================================================
# BDD STEPS
# ============================================================


@given("a valid Stripe webhook secret is configured")
def valid_secret(monkeypatch):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        "whsec_test",
    )


@given("the Stripe webhook secret is missing")
def missing_secret(monkeypatch):
    monkeypatch.setattr(
        stripe_module,
        "STRIPE_WEBHOOK_SECRET",
        None,
    )


def install_event(
    monkeypatch,
    context,
    event_type,
):
    event_object = {"id": "object_001"}

    context.event = event_object

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        lambda **kwargs: {
            "type": event_type,
            "data": {"object": event_object},
        },
    )

    handlers = [
        "handle_checkout_completed",
        "handle_invoice_paid",
        "handle_invoice_failed",
        "handle_subscription_updated",
        "handle_subscription_deleted",
    ]

    for handler in handlers:
        monkeypatch.setattr(
            stripe_module,
            handler,
            lambda obj, name=handler: context.called.append((name, obj)),
        )


@given("Stripe returns a checkout completed event")
def checkout_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "checkout.session.completed",
    )


@given("Stripe returns an invoice paid event")
def invoice_paid_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "invoice.paid",
    )


@given("Stripe returns an invoice failed event")
def invoice_failed_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "invoice.payment_failed",
    )


@given("Stripe returns a subscription updated event")
def subscription_updated_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "customer.subscription.updated",
    )


@given("Stripe returns a subscription deleted event")
def subscription_deleted_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "customer.subscription.deleted",
    )


@given("Stripe returns an unknown event")
def unknown_event(
    monkeypatch,
    context,
):
    install_event(
        monkeypatch,
        context,
        "customer.created",
    )


@given("Stripe rejects the webhook payload")
def reject_payload(monkeypatch):
    def invalid(**kwargs):
        raise ValueError("bad payload")

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        invalid,
    )


@given("Stripe rejects the webhook signature")
def reject_signature(monkeypatch):
    def invalid(**kwargs):
        raise stripe.error.SignatureVerificationError(
            "bad signature",
            "sig",
        )

    monkeypatch.setattr(
        stripe_module.stripe.Webhook,
        "construct_event",
        invalid,
    )


@when("the Stripe webhook is processed")
def process_webhook(context):
    context.response = run_webhook()


@when("the Stripe webhook is processed expecting an error")
def process_webhook_error(context):
    process_error(context)


@then("the checkout completed handler should be called")
def checkout_handler_called(context):
    assert context.called == [
        (
            "handle_checkout_completed",
            context.event,
        )
    ]


@then("the invoice paid handler should be called")
def invoice_paid_called(context):
    assert context.called == [
        (
            "handle_invoice_paid",
            context.event,
        )
    ]


@then("the invoice failed handler should be called")
def invoice_failed_called(context):
    assert context.called == [
        (
            "handle_invoice_failed",
            context.event,
        )
    ]


@then("the subscription updated handler should be called")
def subscription_updated_called(context):
    assert context.called == [
        (
            "handle_subscription_updated",
            context.event,
        )
    ]


@then("the subscription deleted handler should be called")
def subscription_deleted_called(context):
    assert context.called == [
        (
            "handle_subscription_deleted",
            context.event,
        )
    ]


@then("no subscription handler should be called")
def no_handler_called(context):
    assert context.called == []


@then("the webhook response should confirm receipt")
def webhook_received(context):
    assert json.loads(context.response.body) == {"received": True}


@then("the webhook should return a configuration error")
def configuration_error(context):
    assert context.error is not None
    assert context.error.status_code == 500


@then("the webhook should return invalid payload")
def invalid_payload_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert context.error.detail == "Invalid Stripe payload"


@then("the webhook should return invalid signature")
def invalid_signature_error(context):
    assert context.error is not None
    assert context.error.status_code == 400
    assert context.error.detail == "Invalid Stripe signature"
