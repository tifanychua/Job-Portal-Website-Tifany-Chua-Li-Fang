import asyncio

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from fastapi import HTTPException
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# IMPORT ROUTE WITHOUT REAL FIREBASE CONNECTION
# ============================================================

with patch("firebase_admin.firestore.client", return_value=None):
    from job_portal_web.backend.routes import employerCredit as credit_module


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/viewEmployerCredit.feature")


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeDocumentSnapshot:

    def __init__(self, document_id, data=None, exists=True):

        self.id = document_id
        self._data = data or {}
        self.exists = exists

    def to_dict(self):

        return self._data.copy()


class FakeDocumentReference:

    def __init__(self, collection, document_id):

        self.collection = collection
        self.document_id = document_id

    def get(self):

        data = self.collection.documents.get(self.document_id)

        if data is None:

            return FakeDocumentSnapshot(self.document_id, {}, False)

        return FakeDocumentSnapshot(self.document_id, data, True)


class FakeQuery:

    def __init__(self, documents, filters=None):

        self.documents = documents
        self.filters = filters or []

    def where(self, *args, **kwargs):

        # Support Firestore:
        # .where(filter=FieldFilter(...))

        if "filter" in kwargs:

            field_filter = kwargs["filter"]

            field = field_filter.field_path
            operator = field_filter.op_string
            value = field_filter.value

        else:

            field, operator, value = args

        return FakeQuery(self.documents, self.filters + [(field, operator, value)])

    def stream(self):

        result = []

        for document_id, data in self.documents.items():

            matched = True

            for field, operator, expected in self.filters:

                if operator == "==":

                    if data.get(field) != expected:

                        matched = False
                        break

            if matched:

                result.append(FakeDocumentSnapshot(document_id, data, True))

        return result


class FakeCollection:

    def __init__(self, documents=None):

        self.documents = documents or {}

    def document(self, document_id):

        return FakeDocumentReference(self, document_id)

    def where(self, *args, **kwargs):

        return FakeQuery(self.documents).where(*args, **kwargs)

    def stream(self):

        return [
            FakeDocumentSnapshot(document_id, data, True)
            for document_id, data in self.documents.items()
        ]


class FakeDB:

    def __init__(self, companies=None, payments=None):

        self.collections = {
            "company": FakeCollection(companies or {}),
            "payment": FakeCollection(payments or {}),
        }

    def collection(self, name):

        return self.collections[name]


# ============================================================
# FAKE TEMPLATE
# ============================================================


class FakeTemplates:

    def TemplateResponse(self, request, name, context):

        return {"template": name, "context": context}


# ============================================================
# FAKE REQUEST
# ============================================================


class FakeRequest:

    def __init__(self):

        self.session = {"user_type": "employer", "company_id": COMPANY_ID}


# ============================================================
# BDD CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.response = None
        self.error = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# DEFAULT COMPANY
# ============================================================


@pytest.fixture
def companies():

    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
            "total_credit": 30,
            "available_credit": 18,
            "used_credit": 10,
            "expired_credit": 2,
            "subscription_plan": "business",
            "subscription_status": "ACTIVE",
            "cancel_at_period_end": False,
            "subscription_current_period_end": datetime(2026, 9, 30, tzinfo=timezone.utc),
        }
    }


# ============================================================
# DEFAULT PAYMENTS
# ============================================================


@pytest.fixture
def payments():

    return {
        "PAY001": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "status": "COMPLETED",
            "amount": 129.00,
            "created_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "completed_at": datetime(2026, 7, 2, tzinfo=timezone.utc),
        },
        "PAY002": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "status": "PENDING",
            "amount": 129.00,
            "created_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
        },
        "OTHER001": {
            "company_id": "OTHER-COMPANY",
            "package": "Enterprise Pack",
            "status": "COMPLETED",
            "amount": 249.00,
            "created_at": datetime(2026, 8, 5, tzinfo=timezone.utc),
        },
    }


# ============================================================
# INSTALL FAKE DB
# ============================================================


def install_fake_db(monkeypatch, companies, payments):

    fake_db = FakeDB(companies=companies, payments=payments)

    monkeypatch.setattr(credit_module, "db", fake_db)

    monkeypatch.setattr(credit_module, "templates", FakeTemplates())

    return fake_db


@pytest.fixture
def setup_db(monkeypatch, companies, payments):

    return install_fake_db(monkeypatch, companies, payments)


# ============================================================
# HELPER
# ============================================================


def open_credit():

    return asyncio.run(credit_module.employer_credit(request=FakeRequest()))


# ============================================================
# NORMAL PYTEST
# ============================================================


def test_credit_page(setup_db):

    response = open_credit()

    assert response["template"] == "employerCredit.html"


def test_credit_values(setup_db):

    data = open_credit()["context"]

    assert data["total_credit"] == 30
    assert data["available_credit"] == 18
    assert data["used_credit"] == 10
    assert data["expired_credit"] == 2


def test_business_plan_name(setup_db):

    data = open_credit()["context"]

    assert data["current_plan"] == "business"

    assert data["current_plan_name"] == "Business Pack"


def test_subscription_end_format(setup_db):

    data = open_credit()["context"]

    assert data["subscription_end"] == "30 Sep 2026"


def test_only_current_company_payments(setup_db):

    histories = open_credit()["context"]["histories"]

    transaction_ids = {item["transaction_id"] for item in histories}

    assert transaction_ids == {"PAY001", "PAY002"}


def test_history_newest_first(setup_db):

    histories = open_credit()["context"]["histories"]

    assert histories[0]["transaction_id"] == "PAY002"

    assert histories[1]["transaction_id"] == "PAY001"


def test_completed_date_priority(setup_db):

    histories = open_credit()["context"]["histories"]

    payment = next(item for item in histories if item["transaction_id"] == "PAY001")

    assert payment["date"] == "02 Jul 2026"


def test_missing_company(monkeypatch, payments):

    install_fake_db(monkeypatch, {}, payments)

    with pytest.raises(HTTPException) as exc:

        open_credit()

    assert exc.value.status_code == 404


# ============================================================
# HELPER - INSTALL SINGLE COMPANY
# ============================================================


def install_company(monkeypatch, company, payments=None):

    install_fake_db(monkeypatch, {COMPANY_ID: company}, payments or {})


# ============================================================
# HELPER - CREATE PAYMENTS
# ============================================================


def create_payments(count):

    result = {}

    for number in range(1, count + 1):

        result[f"PAY{number:03d}"] = {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "status": "COMPLETED",
            "amount": 129,
            "created_at": datetime(2026, 1, number, tzinfo=timezone.utc),
        }

    return result


# ============================================================
# BDD GIVEN
# ============================================================


@given("an employer company exists")
def employer_company_exists(setup_db):

    pass


@given("the company stores a used credit value")
def company_used_credit(setup_db):

    pass


@given("the company does not store a used credit value")
def company_without_used_credit(monkeypatch):

    install_company(monkeypatch, {"total_credit": 30, "available_credit": 18, "expired_credit": 2})


@given("the company does not contain credit values")
def company_missing_credits(monkeypatch):

    install_company(monkeypatch, {})


@given("the company has a starter subscription")
def starter_subscription(monkeypatch):

    install_company(monkeypatch, {"subscription_plan": "starter"})


@given("the company has a business subscription")
def business_subscription(monkeypatch):

    install_company(monkeypatch, {"subscription_plan": "business"})


@given("the company has an enterprise subscription")
def enterprise_subscription(monkeypatch):

    install_company(monkeypatch, {"subscription_plan": "enterprise"})


@given("the company subscription plan is stored using uppercase letters")
def uppercase_subscription(monkeypatch):

    install_company(monkeypatch, {"subscription_plan": "BUSINESS"})


@given("the company does not have a subscription plan")
def no_subscription(monkeypatch):

    install_company(monkeypatch, {})


@given("the company has a subscription end date")
def subscription_end_exists(monkeypatch):

    install_company(
        monkeypatch, {"subscription_current_period_end": datetime(2026, 9, 30, tzinfo=timezone.utc)}
    )


@given("the company does not have a subscription end date")
def subscription_end_missing(monkeypatch):

    install_company(monkeypatch, {})


@given("the company subscription is scheduled for cancellation")
def subscription_cancelling(monkeypatch):

    install_company(monkeypatch, {"cancel_at_period_end": True})


@given("the company subscription is active and not cancelling")
def subscription_not_cancelling(monkeypatch):

    install_company(monkeypatch, {"cancel_at_period_end": False})


@given("the company has payment records")
def company_payment_records(setup_db):

    pass


@given("a payment contains completed and created dates")
def payment_both_dates(monkeypatch, companies):

    custom = {
        "PAY001": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "status": "COMPLETED",
            "amount": 129,
            "created_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "completed_at": datetime(2026, 7, 2, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, companies, custom)


@given("a payment does not contain a completed date")
def payment_created_only(monkeypatch, companies):

    custom = {
        "PAY001": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "status": "PENDING",
            "amount": 129,
            "created_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, companies, custom)


@given("a payment does not contain a completed or created date")
def payment_without_date(monkeypatch, companies):

    custom = {"PAY001": {"company_id": COMPANY_ID, "status": "PENDING", "amount": 129}}

    install_fake_db(monkeypatch, companies, custom)


@given("a payment amount is stored as a string")
def string_payment_amount(monkeypatch, companies):

    custom = {"PAY001": {"company_id": COMPANY_ID, "status": "COMPLETED", "amount": "129.50"}}

    install_fake_db(monkeypatch, companies, custom)


@given("a payment does not contain an amount")
def missing_payment_amount(monkeypatch, companies):

    custom = {"PAY001": {"company_id": COMPANY_ID, "status": "PENDING"}}

    install_fake_db(monkeypatch, companies, custom)


@given("a payment does not contain a package")
def payment_missing_package(monkeypatch, companies):

    custom = {"PAY001": {"company_id": COMPANY_ID, "status": "COMPLETED", "amount": 129}}

    install_fake_db(monkeypatch, companies, custom)


@given("multiple payment records exist with different dates")
def payment_different_dates(setup_db):

    pass


@given("more than five payment records exist")
def more_than_five_payments(monkeypatch, companies):

    install_fake_db(monkeypatch, companies, create_payments(7))


@given("exactly five payment records exist")
def exactly_five_payments(monkeypatch, companies):

    install_fake_db(monkeypatch, companies, create_payments(5))


@given("the company has no payment records")
def no_payment_records(monkeypatch, companies):

    install_fake_db(monkeypatch, companies, {})


@given("payments belonging to different companies exist")
def multiple_company_payments(setup_db):

    pass


@given("the current employer company does not exist")
def employer_company_missing(monkeypatch, payments):

    install_fake_db(monkeypatch, {}, payments)


# ============================================================
# WHEN
# ============================================================


@when("the employer opens the credit page")
def open_credit_step(context):

    context.response = open_credit()


@when("the employer opens the credit page expecting an error")
def open_credit_error(context):

    try:

        open_credit()

    except HTTPException as exc:

        context.error = exc


# ============================================================
# THEN
# ============================================================


@then("the employer credit page should be displayed")
def verify_credit_page(context):

    assert context.response["template"] == "employerCredit.html"


@then("the total available used and expired credits should be correct")
def verify_credit_summary(context):

    data = context.response["context"]

    assert data["total_credit"] == 30
    assert data["available_credit"] == 18
    assert data["used_credit"] == 10
    assert data["expired_credit"] == 2


@then("the stored used credit should be displayed")
def verify_stored_used_credit(context):

    assert context.response["context"]["used_credit"] == 10


@then("used credit should be calculated from total and available credit")
def verify_calculated_used_credit(context):

    assert context.response["context"]["used_credit"] == 12


@then("all missing credit values should default to zero")
def verify_zero_credits(context):

    data = context.response["context"]

    assert data["total_credit"] == 0
    assert data["available_credit"] == 0
    assert data["used_credit"] == 0
    assert data["expired_credit"] == 0


@then("the current subscription should be Starter Pack")
def verify_starter(context):

    assert context.response["context"]["current_plan_name"] == "Starter Pack"


@then("the current subscription should be Business Pack")
def verify_business(context):

    assert context.response["context"]["current_plan_name"] == "Business Pack"


@then("the current subscription should be Enterprise Pack")
def verify_enterprise(context):

    assert context.response["context"]["current_plan_name"] == "Enterprise Pack"


@then("the subscription plan should still be recognised correctly")
def verify_uppercase_plan(context):

    assert context.response["context"]["current_plan"] == "business"

    assert context.response["context"]["current_plan_name"] == "Business Pack"


@then("the current subscription name should be empty")
def verify_no_plan(context):

    assert context.response["context"]["current_plan"] == ""

    assert context.response["context"]["current_plan_name"] == ""


@then("the subscription end date should be formatted correctly")
def verify_subscription_date(context):

    assert context.response["context"]["subscription_end"] == "30 Sep 2026"


@then("the subscription end date should be empty")
def verify_missing_subscription_end(context):

    assert context.response["context"]["subscription_end"] is None


@then("the cancellation flag should be true")
def verify_cancelling(context):

    assert context.response["context"]["cancel_at_period_end"] is True


@then("the cancellation flag should be false")
def verify_not_cancelling(context):

    assert context.response["context"]["cancel_at_period_end"] is False


@then("the payment history should be displayed")
def verify_history(context):

    assert len(context.response["context"]["histories"]) == 2


@then("the completed date should be used as the payment history date")
def verify_completed_date(context):

    assert context.response["context"]["histories"][0]["date"] == "02 Jul 2026"


@then("the created date should be used as the payment history date")
def verify_created_date(context):

    assert context.response["context"]["histories"][0]["date"] == "01 Aug 2026"


@then("the payment history date should be represented safely")
def verify_missing_date(context):

    assert context.response["context"]["histories"][0]["date"] == "-"


@then("the payment amount should be converted correctly")
def verify_amount_conversion(context):

    assert context.response["context"]["histories"][0]["amount"] == 129.50


@then("the missing payment amount should default to zero")
def verify_missing_amount(context):

    assert context.response["context"]["histories"][0]["amount"] == 0


@then("the missing package should be represented with a dash")
def verify_missing_package(context):

    assert context.response["context"]["histories"][0]["package"] == "-"


@then("the newest payment should be displayed first")
def verify_newest_history(context):

    assert context.response["context"]["histories"][0]["transaction_id"] == "PAY002"


@then("only five recent payments should be displayed")
def verify_five_histories(context):

    assert len(context.response["context"]["histories"]) == 5


@then("the has more payment history flag should be true")
def verify_has_more(context):

    assert context.response["context"]["has_more"] is True


@then("the has more payment history flag should be false")
def verify_no_more(context):

    assert context.response["context"]["has_more"] is False


@then("the recent payment history should be empty")
def verify_empty_history(context):

    assert context.response["context"]["histories"] == []

    assert context.response["context"]["has_more"] is False


@then("only the current company payments should be displayed")
def verify_company_payment_filter(context):

    histories = context.response["context"]["histories"]

    ids = {item["transaction_id"] for item in histories}

    assert ids == {"PAY001", "PAY002"}


@then("the system should return company not found")
def verify_company_not_found(context):

    assert context.error is not None

    assert context.error.status_code == 404

    assert context.error.detail == "Company not found"
