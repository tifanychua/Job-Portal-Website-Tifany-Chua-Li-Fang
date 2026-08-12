import importlib
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD EMPLOYER TRANSACTION MODULE
# ============================================================


def load_payment_history_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def employer_transactions(" in text:

            with patch(
                "firebase_admin.firestore.client",
                return_value=None,
            ):

                return importlib.import_module("job_portal_web.backend.routes." + path.stem)

    raise ImportError("Could not find employer_transactions route.")


transaction_module = load_payment_history_module()


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/viewPaymentHistory.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

COMPANY_NAME = "ABC Technology Sdn Bhd"


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


class FakeDocumentSnapshot:

    def __init__(
        self,
        document_id,
        data=None,
        exists=True,
    ):

        self.id = document_id
        self._data = data or {}
        self.exists = exists

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

        if data is None:

            return FakeDocumentSnapshot(
                self.document_id,
                {},
                exists=False,
            )

        return FakeDocumentSnapshot(
            self.document_id,
            data,
            exists=True,
        )


class FakeQuery:

    def __init__(
        self,
        documents,
        filters=None,
    ):

        self.documents = documents

        self.filters = filters or []

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
            self.documents,
            self.filters
            + [
                (
                    field,
                    operator,
                    value,
                )
            ],
        )

    def stream(self):

        results = []

        for (
            document_id,
            data,
        ) in self.documents.items():

            matched = True

            for (
                field,
                operator,
                expected,
            ) in self.filters:

                if operator == "==":

                    if data.get(field) != expected:

                        matched = False
                        break

            if matched:

                results.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        exists=True,
                    )
                )

        return results


class FakeCollection:

    def __init__(
        self,
        documents=None,
    ):

        self.documents = documents or {}

    def document(
        self,
        document_id,
    ):

        return FakeDocumentReference(
            self,
            document_id,
        )

    def where(
        self,
        *args,
        **kwargs,
    ):

        query = FakeQuery(self.documents)

        return query.where(
            *args,
            **kwargs,
        )

    def stream(self):

        return FakeQuery(self.documents).stream()


class FakeDB:

    def __init__(
        self,
        companies=None,
        payments=None,
    ):

        self.collections = {
            "company": FakeCollection(companies or {}),
            "payment": FakeCollection(payments or {}),
        }

    def collection(
        self,
        name,
    ):

        return self.collections[name]


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
# CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.response = None

        self.selected_transaction = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# COMPANY DATA
# ============================================================


@pytest.fixture
def companies():

    return {
        COMPANY_ID: {
            "companyName": COMPANY_NAME,
            "total_credit": 40,
            "available_credit": 20,
            "used_credit": 20,
        }
    }


# ============================================================
# PAYMENT DATA
# ============================================================


@pytest.fixture
def payments():

    return {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "amount": 49.00,
            "credits": 10,
            "currency": "MYR",
            "status": "COMPLETED",
            "completed_at": datetime(
                2026,
                8,
                1,
                10,
                30,
                tzinfo=timezone.utc,
            ),
        },
        "TXN002": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "payment_method": "Card",
            "amount": 129.00,
            "credits": 30,
            "currency": "MYR",
            "status": "COMPLETED",
            "completed_at": datetime(
                2026,
                8,
                10,
                14,
                15,
                tzinfo=timezone.utc,
            ),
        },
        # Another company's payment.
        # Must not appear.
        "OTHER001": {
            "company_id": "OTHER-COMPANY",
            "package": "Enterprise Pack",
            "payment_method": "Card",
            "amount": 229.00,
            "status": "COMPLETED",
            "completed_at": datetime(
                2026,
                8,
                11,
                tzinfo=timezone.utc,
            ),
        },
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(
    monkeypatch,
    companies,
    payments,
):

    fake_db = FakeDB(
        companies=companies,
        payments=payments,
    )

    monkeypatch.setattr(
        transaction_module,
        "db",
        fake_db,
    )

    monkeypatch.setattr(
        transaction_module,
        "templates",
        FakeTemplates(),
    )

    monkeypatch.setattr(
        transaction_module,
        "get_current_company_id",
        lambda request: COMPANY_ID,
    )

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    companies,
    payments,
):

    return install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


# ============================================================
# HELPER
# ============================================================


def open_payment_history():

    return transaction_module.employer_transactions(
        request=FakeRequest(),
        page=1,
        status="",
        keyword="",
    )


# ============================================================
# GIVEN
# ============================================================


@given("the employer has completed one or more payment transactions")
def employer_has_payments(
    setup_db,
):

    pass


@given("the employer has a recorded payment transaction")
def employer_has_recorded_transaction(
    setup_db,
    context,
):

    context.response = open_payment_history()


@given("the employer has not completed any payment transactions")
def employer_has_no_payments(
    monkeypatch,
    companies,
):

    install_fake_db(
        monkeypatch,
        companies,
        {},
    )


# ============================================================
# WHEN
# ============================================================


@when("the employer accesses the payment history page")
def access_payment_history(
    context,
):

    context.response = open_payment_history()


@when("the employer selects a transaction from the payment history")
def select_transaction(
    context,
):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) > 0

    context.selected_transaction = transactions[0]


# ============================================================
# THEN
# ============================================================


@then("the system should display a list of the employer's previous payment transactions")
def display_payment_history(
    context,
):

    data = context.response["context"]

    transactions = data["transactions"]

    assert context.response["template"] == "employerTransactions.html"

    # Current employer has 2 transactions
    assert data["total_transactions"] == 2

    assert len(transactions) == 2

    transaction_ids = {transaction["transaction_id"] for transaction in transactions}

    assert "TXN001" in transaction_ids

    assert "TXN002" in transaction_ids

    # Other employer's payment
    # must not appear.
    assert "OTHER001" not in transaction_ids


@then(
    "the system should display details including transaction date payment amount payment status and purchased credit package"
)
def display_transaction_details(
    context,
):

    transaction = context.selected_transaction

    assert transaction is not None

    # Transaction date
    assert "date" in transaction

    assert transaction["date"] != "-"

    # Payment amount
    assert "amount" in transaction

    assert isinstance(
        transaction["amount"],
        float,
    )

    # Payment status
    assert transaction["status"] == "COMPLETED"

    # Purchased credit package
    assert "package" in transaction

    assert transaction["package"] in {
        "Starter Pack",
        "Business Pack",
    }

    # Card-only system
    assert transaction["payment_method"] == "Card"


@then("the system should display that no payment records are available")
def no_payment_records(
    context,
):

    data = context.response["context"]

    assert data["transactions"] == []

    assert data["total_transactions"] == 0

    assert data["total_spent"] == 0

    assert data["completed_count"] == 0
