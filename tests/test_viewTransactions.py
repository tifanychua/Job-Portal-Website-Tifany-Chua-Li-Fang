from datetime import datetime, timezone

import pytest

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

from job_portal_web.backend.routes import adminTransaction as transaction_module

# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/viewTransactions.feature")


# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

COMPANY_NAME = "ABC Technology Sdn Bhd"

COMPANY_EMAIL = "hr@abctech.com"


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


class FakeCollection:

    def __init__(
        self,
        documents=None,
    ):

        self.documents = documents or {}

    def stream(self):

        return [
            FakeDocumentSnapshot(
                document_id,
                data,
                exists=True,
            )
            for (
                document_id,
                data,
            ) in self.documents.items()
        ]

    def document(
        self,
        document_id,
    ):

        return FakeDocumentReference(
            self,
            document_id,
        )


class FakeDB:

    def __init__(
        self,
        payments=None,
        companies=None,
    ):

        self.collections = {
            "payment": FakeCollection(payments or {}),
            "company": FakeCollection(companies or {}),
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
# TEST CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.response = None

        self.selected_transaction = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# COMPANY FIXTURE
# ============================================================


@pytest.fixture
def companies():

    return {
        COMPANY_ID: {
            "companyName": COMPANY_NAME,
            "businessEmail": COMPANY_EMAIL,
        },
        "COMPANY002": {
            "companyName": "XYZ Solutions",
            "businessEmail": "finance@xyz.com",
        },
    }


# ============================================================
# PAYMENT FIXTURE
# ============================================================


@pytest.fixture
def payments():

    year = datetime.now(timezone.utc).year

    return {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "amount": 49.00,
            "status": "COMPLETED",
            "created_at": datetime(
                year,
                1,
                10,
                tzinfo=timezone.utc,
            ),
            "completed_at": datetime(
                year,
                1,
                11,
                tzinfo=timezone.utc,
            ),
        },
        "TXN002": {
            "company_id": COMPANY_ID,
            "package": "Business Pack",
            "payment_method": "Card",
            "amount": 129.00,
            "status": "PENDING",
            "created_at": datetime(
                year,
                2,
                15,
                tzinfo=timezone.utc,
            ),
        },
        "TXN003": {
            "company_id": "COMPANY002",
            "package": "Enterprise Pack",
            "payment_method": "Card",
            "amount": 249.00,
            "status": "FAILED",
            "created_at": datetime(
                year,
                3,
                20,
                tzinfo=timezone.utc,
            ),
        },
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(
    monkeypatch,
    payments,
    companies,
):

    fake_db = FakeDB(
        payments=payments,
        companies=companies,
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

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    payments,
    companies,
):

    return install_fake_db(
        monkeypatch,
        payments,
        companies,
    )


# ============================================================
# HELPER
# ============================================================


def get_page(
    status="",
    keyword="",
    page=1,
):

    return transaction_module.transaction_management(
        request=None,
        status=status,
        keyword=keyword,
        page=page,
    )


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_admin_can_view_all_employer_transactions(
    setup_db,
):

    response = get_page()

    data = response["context"]

    assert response["template"] == "adminTransactions.html"

    assert data["total_transactions"] == 3

    assert len(data["transactions"]) == 3


def test_admin_can_view_transaction_details(
    setup_db,
):

    response = get_page(keyword="TXN001")

    transactions = response["context"]["transactions"]

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction["transaction_id"] == "TXN001"

    assert transaction["company_name"] == COMPANY_NAME

    assert transaction["company_email"] == COMPANY_EMAIL

    assert transaction["package"] == "Starter Pack"

    assert transaction["amount"] == 49.00

    assert transaction["status"] == "COMPLETED"

    assert transaction["display_date"] is not None


def test_admin_can_filter_transactions(
    setup_db,
):

    response = get_page(
        status="COMPLETED",
        keyword=COMPANY_NAME,
    )

    transactions = response["context"]["transactions"]

    assert len(transactions) == 1

    assert transactions[0]["transaction_id"] == "TXN001"

    assert transactions[0]["status"] == "COMPLETED"

    assert transactions[0]["company_name"] == COMPANY_NAME


def test_pending_and_failed_transactions_are_visible(
    setup_db,
):

    response = get_page()

    transactions = response["context"]["transactions"]

    statuses = {transaction["status"] for transaction in transactions}

    assert "PENDING" in statuses

    assert "FAILED" in statuses


# ============================================================
# BDD GIVEN
# ============================================================


@given("the admin is logged into the admin dashboard")
def admin_logged_in(
    setup_db,
):

    pass


@given("the admin is viewing the employer payment transaction list")
def admin_viewing_transaction_list(
    setup_db,
    context,
):

    context.response = get_page()


@given("the admin is viewing the payment transaction management section")
def admin_viewing_management(
    setup_db,
    context,
):

    context.response = get_page()


@given("there are failed or pending employer payment transactions")
def unsuccessful_transactions_exist(
    setup_db,
):

    pass


# ============================================================
# BDD WHEN
# ============================================================


@when("the admin accesses the payment transaction management section")
def access_payment_transactions(
    context,
):

    context.response = get_page()


@when("the admin selects a specific transaction")
def select_transaction(
    context,
):

    transactions = context.response["context"]["transactions"]

    context.selected_transaction = next(
        transaction for transaction in transactions if (transaction["transaction_id"] == "TXN001")
    )


@when("the admin applies payment transaction filters")
def apply_transaction_filters(
    context,
):

    # Filter by:
    # 1. Completed status
    # 2. Employer/company account

    context.response = get_page(
        status="COMPLETED",
        keyword=COMPANY_NAME,
    )


# ============================================================
# BDD THEN
# ============================================================


@then("the system should display a list of all employer payment transactions")
def display_all_transactions(
    context,
):

    data = context.response["context"]

    transactions = data["transactions"]

    assert context.response["template"] == "adminTransactions.html"

    assert data["total_transactions"] == 3

    assert len(transactions) == 3

    transaction_ids = {transaction["transaction_id"] for transaction in transactions}

    assert transaction_ids == {
        "TXN001",
        "TXN002",
        "TXN003",
    }


@then(
    "the system should display the transaction details including employer information payment date purchased credit package payment amount and payment status"
)
def display_transaction_details(
    context,
):

    transaction = context.selected_transaction

    assert transaction is not None

    # Employer information
    assert transaction["company_name"] == COMPANY_NAME

    assert transaction["company_email"] == COMPANY_EMAIL

    # Payment date
    assert transaction["display_date"] is not None

    # Purchased package
    assert transaction["package"] == "Starter Pack"

    # Amount
    assert transaction["amount"] == 49.00

    # Status
    assert transaction["status"] == "COMPLETED"

    # Card-only system
    assert transaction["payment_method"] == "Card"


@then("the system should display only transactions that match the selected criteria")
def filtered_transactions_displayed(
    context,
):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction["status"] == "COMPLETED"

    assert transaction["company_name"] == COMPANY_NAME

    assert transaction["transaction_id"] == "TXN001"


@then(
    "the system should display the payment transactions with their respective statuses for monitoring"
)
def unsuccessful_statuses_displayed(
    context,
):

    transactions = context.response["context"]["transactions"]

    pending = [transaction for transaction in transactions if (transaction["status"] == "PENDING")]

    failed = [transaction for transaction in transactions if (transaction["status"] == "FAILED")]

    assert len(pending) == 1

    assert len(failed) == 1

    assert pending[0]["transaction_id"] == "TXN002"

    assert failed[0]["transaction_id"] == "TXN003"