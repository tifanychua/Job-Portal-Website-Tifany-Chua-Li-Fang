import os
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
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

COMPANY_NAME = "ABC Technology Sdn Bhd"

COMPANY_EMAIL = "hr@abctech.com"

PAYMENT_METHOD = "Card"


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/generateTransactionReport.feature")


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
        self._data = data.copy() if data else {}
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
        self.documents = documents.copy() if documents else {}

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
# CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.response = None


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
            "businessEmail": COMPANY_EMAIL,
        }
    }


# ============================================================
# PAYMENT DATA
# ============================================================


@pytest.fixture
def payments():

    year = datetime.now(timezone.utc).year

    return {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "package_name": "Starter",
            "payment_method": PAYMENT_METHOD,
            "amount": 49.00,
            "status": "COMPLETED",
            "created_at": datetime(
                year,
                1,
                14,
                tzinfo=timezone.utc,
            ),
            "completed_at": datetime(
                year,
                1,
                15,
                tzinfo=timezone.utc,
            ),
        },
        "TXN002": {
            "company_id": COMPANY_ID,
            "package": "Business",
            "package_name": "Business",
            "payment_method": PAYMENT_METHOD,
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
            "company_id": COMPANY_ID,
            "package": "Enterprise",
            "package_name": "Enterprise",
            "payment_method": PAYMENT_METHOD,
            "amount": 249.00,
            "status": "FAILED",
            "created_at": datetime(
                year,
                3,
                15,
                tzinfo=timezone.utc,
            ),
        },
        "TXN004": {
            "company_id": COMPANY_ID,
            "package": "Business",
            "package_name": "Business",
            "payment_method": PAYMENT_METHOD,
            "amount": 129.00,
            "status": "COMPLETED",
            "created_at": datetime(
                year,
                4,
                14,
                tzinfo=timezone.utc,
            ),
            "completed_at": datetime(
                year,
                4,
                15,
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
    patch_templates=True,
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

    if patch_templates:

        monkeypatch.setattr(
            transaction_module,
            "templates",
            FakeTemplates(),
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
        payments,
        companies,
    )


# ============================================================
# HELPERS
# ============================================================


def generate_report(
    from_date="",
    to_date="",
    status="",
    generate="",
):

    return transaction_module.transaction_report_page(
        request=None,
        from_date=from_date,
        to_date=to_date,
        status=status,
        generate=generate,
    )


def download_report(
    from_date="",
    to_date="",
    status="",
):

    return transaction_module.download_transaction_report(
        from_date=from_date,
        to_date=to_date,
        status=status,
    )


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_admin_can_open_transaction_report(
    setup_db,
):

    response = generate_report()

    assert response["template"] == "adminTransactionReport.html"


def test_admin_can_generate_transaction_report(
    setup_db,
):

    response = generate_report(generate="1")

    data = response["context"]

    assert data["generated"] is True

    assert data["total_transactions"] == 4

    assert len(data["transactions"]) == 4


def test_admin_can_filter_transaction_report(
    setup_db,
):

    year = datetime.now(timezone.utc).year

    response = generate_report(
        from_date=f"{year}-01-01",
        to_date=f"{year}-03-31",
        status="COMPLETED",
        generate="1",
    )

    transactions = response["context"]["transactions"]

    assert len(transactions) == 1

    assert transactions[0]["transaction_id"] == "TXN001"

    assert transactions[0]["status"] == "COMPLETED"


def test_admin_can_view_report_summary(
    setup_db,
):

    response = generate_report(generate="1")

    data = response["context"]

    assert data["total_transactions"] == 4

    assert data["successful"] == 2

    assert data["pending"] == 1

    assert data["failed"] == 1

    expected_revenue = 49.00 + 129.00

    assert data["total_revenue"] == expected_revenue


def test_admin_can_download_transaction_report_pdf(
    setup_db,
):

    response = download_report()

    assert response.media_type == "application/pdf"

    assert response.filename.lower().endswith(".pdf")

    assert os.path.exists(response.path)


# ============================================================
# BDD GIVEN
# ============================================================


@given("the admin is logged into the system")
def admin_logged_in(
    setup_db,
):

    pass


@given("the admin is viewing the transaction report page")
def admin_viewing_report_page(
    setup_db,
    context,
):

    context.response = generate_report()


@given("the admin has generated a transaction report")
def admin_generated_report(
    setup_db,
    context,
):

    context.response = generate_report(generate="1")


# ============================================================
# BDD WHEN
# ============================================================


@when("the admin opens the transaction report page")
def admin_opens_report_page(
    context,
):

    context.response = generate_report()


@when("the admin generates the transaction report")
def admin_generates_report(
    context,
):

    context.response = generate_report(generate="1")


@when("the admin selects a payment status and date range")
def admin_filters_report(
    context,
):

    year = datetime.now(timezone.utc).year

    context.response = generate_report(
        from_date=f"{year}-01-01",
        to_date=f"{year}-03-31",
        status="COMPLETED",
        generate="1",
    )


@when("the report summary is displayed")
def report_summary_displayed(
    context,
):

    assert context.response is not None


@when("the admin downloads the transaction report")
def admin_downloads_report(
    context,
):

    context.response = download_report()


# ============================================================
# BDD THEN
# ============================================================


@then("the system should display the transaction report page")
def transaction_report_page_displayed(
    context,
):

    assert context.response["template"] == "adminTransactionReport.html"


@then("the system should display the transaction report with employer payment information")
def transaction_report_generated(
    context,
):

    data = context.response["context"]

    assert data["generated"] is True

    assert data["total_transactions"] == 4

    transactions = data["transactions"]

    assert len(transactions) == 4

    required_fields = [
        "transaction_id",
        "company_name",
        "package",
        "payment_method",
        "amount",
        "status",
        "display_date",
    ]

    for transaction in transactions:

        for field in required_fields:

            assert field in transaction


@then("the system should display only transactions that match the selected criteria")
def filtered_report_displayed(
    context,
):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    transaction = transactions[0]

    assert transaction["transaction_id"] == "TXN001"

    assert transaction["status"] == "COMPLETED"


@then(
    "the system should show total transactions successful payments pending payments failed payments and total revenue"
)
def report_summary_correct(
    context,
):

    data = context.response["context"]

    assert data["total_transactions"] == 4

    assert data["successful"] == 2

    assert data["pending"] == 1

    assert data["failed"] == 1

    assert data["total_revenue"] == 178.00


@then("the system should generate a PDF transaction report")
def pdf_report_generated(
    context,
):

    assert context.response is not None

    assert context.response.media_type == "application/pdf"

    assert context.response.filename.lower().endswith(".pdf")

    assert os.path.exists(context.response.path)
