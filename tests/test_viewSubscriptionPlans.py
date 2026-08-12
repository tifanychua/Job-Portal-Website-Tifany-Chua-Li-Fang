import importlib
from pathlib import Path

import pytest

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

        if "def employer_plans(" in text and "def start_subscription(" in text:

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

scenarios("features/viewSubscriptionPlans.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeSnapshot:

    def __init__(
        self,
        data=None,
    ):

        self._data = data

        self.exists = data is not None

    def to_dict(self):

        return dict(self._data or {})


class FakeDocument:

    def __init__(
        self,
        collection,
        document_id,
    ):

        self.collection = collection

        self.document_id = document_id

    def get(self):

        return FakeSnapshot(self.collection.data.get(self.document_id))


class FakeCollection:

    def __init__(
        self,
        data=None,
    ):

        self.data = data or {}

    def document(
        self,
        document_id,
    ):

        return FakeDocument(
            self,
            document_id,
        )


class FakeDB:

    def __init__(
        self,
        company=None,
    ):

        self.company = FakeCollection({COMPANY_ID: company} if company is not None else {})

    def collection(
        self,
        name,
    ):

        if name == "company":

            return self.company

        return FakeCollection()


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

    monkeypatch.setattr(
        subscription_module,
        "templates",
        FakeTemplates(),
    )


def install_company(
    monkeypatch,
    context,
    company,
):

    context.db = FakeDB(company)

    monkeypatch.setattr(
        subscription_module,
        "db",
        context.db,
    )


# ============================================================
# DIRECT PYTEST
# ============================================================


def test_employer_can_view_available_subscription_plans(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "subscription_plan": "",
        },
    )

    response = subscription_module.employer_plans(FakeRequest())

    plans = response["context"]["plans"]

    assert "starter" in plans

    assert "business" in plans

    assert "enterprise" in plans


def test_subscription_plan_prices_and_credits():

    plans = subscription_module.PLANS

    assert plans["starter"]["price"] == 49

    assert plans["starter"]["credits"] == 10

    assert plans["business"]["price"] == 129

    assert plans["business"]["credits"] == 30

    assert plans["enterprise"]["price"] == 229

    assert plans["enterprise"]["credits"] == 60


# ============================================================
# GIVEN
# ============================================================


@given("the employer company exists")
def employer_company_exists(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "subscription_plan": "",
        },
    )


@given("the employer currently has a business subscription")
def business_subscription(
    monkeypatch,
    context,
):

    install_company(
        monkeypatch,
        context,
        {
            "companyName": "ABC Technology",
            "subscription_plan": "Business",
            "subscription_status": "ACTIVE",
        },
    )


# ============================================================
# WHEN
# ============================================================


@when("the employer opens the subscription plans page")
def open_subscription_plans(
    context,
):

    context.response = subscription_module.employer_plans(FakeRequest())


# ============================================================
# THEN
# ============================================================


@then("the system should display all available subscription plans")
def display_all_plans(
    context,
):

    assert context.response["template"] == "employerPlans.html"

    plans = context.response["context"]["plans"]

    assert "starter" in plans
    assert "business" in plans
    assert "enterprise" in plans


@then("each subscription plan should display its price and number of job posting credits")
def display_plan_details(
    context,
):

    plans = context.response["context"]["plans"]

    for plan in plans.values():

        assert "price" in plan

        assert "credits" in plan

        assert plan["price"] > 0

        assert plan["credits"] > 0


@then("the business subscription should be identified as the current plan")
def current_business_plan(
    context,
):

    assert context.response["context"]["current_plan"] == "business"
