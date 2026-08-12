import importlib
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD SUBSCRIPTION MODULE
# ============================================================


def load_subscription_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def cancel_subscription(" not in text:
            continue

        import firebase_admin.firestore as firestore_module

        original_client = firestore_module.client

        firestore_module.client = lambda: None

        try:

            return importlib.import_module("job_portal_web.backend.routes." + path.stem)

        finally:

            firestore_module.client = original_client

    raise ImportError("Cannot find subscription route module.")


subscription_module = load_subscription_module()


# ============================================================
# FEATURE
# ============================================================

scenarios("features/cancelSubscription.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

SUBSCRIPTION_ID = "sub_test"


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
# FAKE FIRESTORE
# ============================================================


class FakeDocument:

    def __init__(
        self,
        data,
    ):

        self.data = data

    def update(
        self,
        values,
    ):

        self.data.update(values)


class FakeCollection:

    def __init__(
        self,
        company,
    ):

        self.company = company

    def document(
        self,
        document_id,
    ):

        assert document_id == COMPANY_ID

        return FakeDocument(self.company)


class FakeDB:

    def __init__(
        self,
        company,
    ):

        self.company = company

    def collection(
        self,
        name,
    ):

        assert name == "company"

        return FakeCollection(self.company)


# ============================================================
# CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.company = None

        self.response = None

        self.error = None

        self.modify_args = None

        self.stripe_should_fail = False


@pytest.fixture
def context():

    return Context()


# ============================================================
# COMMON SETUP
# ============================================================


@pytest.fixture(autouse=True)
def common_setup(
    monkeypatch,
    context,
):

    # --------------------------------------------------------
    # Current employer
    # --------------------------------------------------------

    monkeypatch.setattr(
        subscription_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    # --------------------------------------------------------
    # Get company
    # --------------------------------------------------------

    monkeypatch.setattr(
        subscription_module,
        "get_company",
        lambda company_id: context.company,
    )


# ============================================================
# HELPER
# ============================================================


def install_fake_db(
    monkeypatch,
    context,
):

    fake_db = FakeDB(context.company)

    monkeypatch.setattr(
        subscription_module,
        "db",
        fake_db,
    )


def call_cancel(
    context,
):

    context.response = None
    context.error = None

    try:

        context.response = subscription_module.cancel_subscription(FakeRequest())

    except HTTPException as exc:

        context.error = exc


# ============================================================
# GIVEN
# ============================================================


@given("an employer has an active Stripe subscription")
def active_subscription(
    monkeypatch,
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn. Bhd.",
        "stripe_subscription_id": SUBSCRIPTION_ID,
        "cancel_at_period_end": False,
    }

    install_fake_db(
        monkeypatch,
        context,
    )


@given("an employer has no Stripe subscription")
def no_subscription(
    monkeypatch,
    context,
):

    context.company = {
        "companyName": "ABC Technology Sdn. Bhd.",
        "stripe_subscription_id": "",
        "cancel_at_period_end": False,
    }

    install_fake_db(
        monkeypatch,
        context,
    )


@given("Stripe fails to cancel the subscription")
def stripe_cancel_failure(
    context,
):

    context.stripe_should_fail = True


# ============================================================
# WHEN
# ============================================================


@when("the employer cancels the subscription")
def cancel_subscription(
    monkeypatch,
    context,
):

    # --------------------------------------------------------
    # Get the exact Stripe object used
    # inside cancel_subscription()
    # --------------------------------------------------------

    route_globals = subscription_module.cancel_subscription.__globals__

    stripe_used_by_route = route_globals["stripe"]

    # --------------------------------------------------------
    # Fake Stripe modify
    # --------------------------------------------------------

    def fake_modify(
        subscription_id,
        **kwargs,
    ):

        if context.stripe_should_fail:

            raise stripe_used_by_route.error.StripeError("Stripe cancellation failed")

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

    call_cancel(context)


# ============================================================
# THEN - STRIPE CANCELLATION
# ============================================================


@then("Stripe should schedule cancellation at period end")
def stripe_schedules_cancellation(
    context,
):

    assert context.error is None

    assert context.modify_args is not None

    assert context.modify_args["subscription_id"] == SUBSCRIPTION_ID

    assert context.modify_args["cancel_at_period_end"] is True


# ============================================================
# THEN - FIRESTORE FLAG
# ============================================================


@then("the cancellation flag should be saved")
def cancellation_flag_saved(
    context,
):

    assert context.company["cancel_at_period_end"] is True

    assert "updatedAt" in context.company


# ============================================================
# THEN - REDIRECT
# ============================================================


@then("the employer should be redirected to the credit page")
def redirected_to_credit_page(
    context,
):

    assert context.error is None

    assert context.response is not None

    assert context.response.status_code == 303

    assert context.response.headers["location"] == "/employer-credit?cancel=scheduled"


# ============================================================
# THEN - NO ACTIVE SUBSCRIPTION
# ============================================================


@then("no active subscription error should be returned")
def no_active_subscription_error(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 400

    assert "No active subscription found" in context.error.detail


# ============================================================
# THEN - STRIPE ERROR
# ============================================================


@then("the Stripe cancellation error should be returned")
def stripe_cancellation_error(
    context,
):

    assert context.error is not None

    assert context.error.status_code == 400

    assert "Stripe cancellation failed" in context.error.detail
