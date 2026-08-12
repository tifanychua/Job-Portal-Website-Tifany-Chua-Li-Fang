import importlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when

# ============================================================
# LOAD ACTUAL ROUTE WITHOUT REAL FIREBASE CONNECTION
# ============================================================


def load_transaction_module():
    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def employer_transactions(" in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client
            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)
            finally:
                firestore_module.client = original_client

    raise ImportError("Could not find the employer transaction route file.")


transaction_module = load_transaction_module()

scenarios("features/viewEmployerTransactions.feature")


COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

TEMPLATE_PATH = Path("src/job_portal_web/ui/employerTransactions.html")


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeSnapshot:

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


class FakeDocument:

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
            return FakeSnapshot(
                self.document_id,
                {},
                False,
            )

        return FakeSnapshot(
            self.document_id,
            data,
            True,
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
            field, operator, value = args

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
        result = []

        for document_id, data in self.documents.items():
            matched = True

            for (
                field,
                operator,
                expected,
            ) in self.filters:

                if operator == "==" and data.get(field) != expected:
                    matched = False
                    break

            if matched:
                result.append(
                    FakeSnapshot(
                        document_id,
                        data,
                        True,
                    )
                )

        return result


class FakeCollection:

    def __init__(
        self,
        documents=None,
    ):
        self.documents = documents.copy() if documents else {}

    def document(
        self,
        document_id,
    ):
        return FakeDocument(
            self,
            document_id,
        )

    def where(
        self,
        *args,
        **kwargs,
    ):
        return FakeQuery(self.documents).where(
            *args,
            **kwargs,
        )


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
# FAKE TEMPLATE / REQUEST
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
        self.error = None
        self.html = ""


@pytest.fixture
def context():
    return Context()


# ============================================================
# DEFAULT TEST DATA
# ============================================================


@pytest.fixture
def companies():
    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
        }
    }


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
            "stripe_invoice_id": "in_001",
            "created_at": datetime(
                2026,
                1,
                9,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            "completed_at": datetime(
                2026,
                1,
                10,
                11,
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
            "status": "PENDING",
            "created_at": datetime(
                2026,
                2,
                15,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        },
        "TXN003": {
            "company_id": COMPANY_ID,
            "package": "Enterprise Pack",
            "payment_method": "Card",
            "amount": 229.00,
            "credits": 60,
            "currency": "MYR",
            "status": "FAILED",
            "created_at": datetime(
                2026,
                3,
                20,
                15,
                45,
                tzinfo=timezone.utc,
            ),
        },
        "OTHER001": {
            "company_id": "OTHER-COMPANY",
            "package": "Enterprise Pack",
            "payment_method": "Card",
            "amount": 229.00,
            "credits": 60,
            "currency": "MYR",
            "status": "COMPLETED",
            "created_at": datetime(
                2026,
                4,
                1,
                tzinfo=timezone.utc,
            ),
        },
    }


# ============================================================
# INSTALL FAKE DB
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
# HELPERS
# ============================================================


def open_transactions(
    page=1,
    status="",
    keyword="",
):
    return transaction_module.employer_transactions(
        request=FakeRequest(),
        page=page,
        status=status,
        keyword=keyword,
    )


def create_payments(count):
    result = {}

    for number in range(
        1,
        count + 1,
    ):
        result[f"TXN{number:03d}"] = {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "amount": 49.00,
            "credits": 10,
            "status": "COMPLETED",
            "created_at": datetime(
                2026,
                1,
                min(number, 28),
                number % 24,
                0,
                tzinfo=timezone.utc,
            ),
        }

    return result


def read_template():
    return TEMPLATE_PATH.read_text(encoding="utf-8")


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_transaction_page(
    setup_db,
):
    response = open_transactions()

    assert response["template"] == "employerTransactions.html"


def test_only_current_company_transactions(
    setup_db,
):
    response = open_transactions()

    ids = {item["transaction_id"] for item in response["context"]["transactions"]}

    assert ids == {
        "TXN001",
        "TXN002",
        "TXN003",
    }


def test_transaction_summary(
    setup_db,
):
    data = open_transactions()["context"]

    assert data["total_transactions"] == 3
    assert data["completed_count"] == 1
    assert data["pending_count"] == 1
    assert data["failed_count"] == 1
    assert data["total_spent"] == 49.00


@pytest.mark.parametrize(
    "keyword,expected",
    [
        ("TXN001", 1),
        ("txn001", 1),
        ("Starter", 1),
        ("starter", 1),
        ("Business", 1),
        ("Card", 3),
        ("   TXN001   ", 1),
        ("DOES-NOT-EXIST", 0),
        ("", 3),
    ],
)
def test_search(
    setup_db,
    keyword,
    expected,
):
    response = open_transactions(keyword=keyword)

    assert response["context"]["total_transactions"] == expected


@pytest.mark.parametrize(
    "status,expected",
    [
        ("COMPLETED", 1),
        ("PENDING", 1),
        ("FAILED", 1),
        ("completed", 1),
        ("pending", 1),
        ("failed", 1),
        ("INVALID", 0),
        ("", 3),
    ],
)
def test_status_filter(
    setup_db,
    status,
    expected,
):
    response = open_transactions(status=status)

    assert response["context"]["total_transactions"] == expected


def test_search_and_filter(
    setup_db,
):
    response = open_transactions(
        keyword="Starter",
        status="COMPLETED",
    )

    assert response["context"]["total_transactions"] == 1

    assert response["context"]["transactions"][0]["transaction_id"] == "TXN001"


def test_completed_date_priority(
    setup_db,
):
    response = open_transactions(keyword="TXN001")

    transaction = response["context"]["transactions"][0]

    assert transaction["date"] == "10 Jan 2026"
    assert transaction["time"] == "11:30 AM"


def test_created_date_fallback(
    setup_db,
):
    response = open_transactions(keyword="TXN002")

    transaction = response["context"]["transactions"][0]

    assert transaction["date"] == "15 Feb 2026"
    assert transaction["time"] == "12:00 PM"


def test_newest_first(
    setup_db,
):
    transactions = open_transactions()["context"]["transactions"]

    assert transactions[0]["transaction_id"] == "TXN003"

    assert transactions[-1]["transaction_id"] == "TXN001"


def test_21_transactions_two_pages(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(21),
    )

    response = open_transactions()

    assert response["context"]["total_pages"] == 2

    assert len(response["context"]["transactions"]) == 20


def test_page_two_remaining_records(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(25),
    )

    response = open_transactions(page=2)

    assert len(response["context"]["transactions"]) == 5

    assert response["context"]["current_page"] == 2


def test_page_boundaries(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(25),
    )

    assert open_transactions(page=0)["context"]["current_page"] == 1

    assert open_transactions(page=-10)["context"]["current_page"] == 1

    assert open_transactions(page=999)["context"]["current_page"] == 2


def test_missing_company(
    monkeypatch,
    payments,
):
    install_fake_db(
        monkeypatch,
        {},
        payments,
    )

    with pytest.raises(HTTPException) as exc:
        open_transactions()

    assert exc.value.status_code == 404
    assert exc.value.detail == "Company not found"


# ============================================================
# BDD GIVEN
# ============================================================


@given("an employer company exists")
def employer_company_exists(
    setup_db,
):
    pass


@given("payments belonging to different companies exist")
def different_company_payments(
    setup_db,
):
    pass


@given("an employer company has payment transactions")
def employer_has_transactions(
    setup_db,
):
    pass


@given("completed pending and failed payments exist")
def different_statuses(
    setup_db,
):
    pass


@given("a transaction has both completed and created dates")
def transaction_both_dates(
    setup_db,
):
    pass


@given("a transaction has only a created date")
def transaction_created_only(
    setup_db,
):
    pass


@given("a transaction has no completed or created date")
def no_transaction_date(
    monkeypatch,
    companies,
):
    payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "amount": 49,
            "credits": 10,
            "status": "COMPLETED",
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a transaction has no package")
def no_package(
    monkeypatch,
    companies,
):
    payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a transaction has no payment method")
def no_payment_method(
    monkeypatch,
    companies,
):
    payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "amount": 49,
            "status": "COMPLETED",
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a transaction has no amount")
def no_amount(
    monkeypatch,
    companies,
):
    payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "status": "COMPLETED",
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("a transaction has no credits")
def no_credits(
    monkeypatch,
    companies,
):
    payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter Pack",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
        }
    }

    install_fake_db(
        monkeypatch,
        companies,
        payments,
    )


@given("transactions exist with different payment dates")
def transactions_different_dates(
    setup_db,
):
    pass


@given("fewer than twenty transactions exist")
def fewer_than_twenty(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(10),
    )


@given("exactly twenty transactions exist")
def exactly_twenty(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(20),
    )


@given("twenty one transactions exist")
def twenty_one(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(21),
    )


@given("twenty five transactions exist")
def twenty_five(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        create_payments(25),
    )


@given("the employer company has no payment transactions")
def no_payments(
    monkeypatch,
    companies,
):
    install_fake_db(
        monkeypatch,
        companies,
        {},
    )


@given("the current employer company does not exist")
def company_missing(
    monkeypatch,
    payments,
):
    install_fake_db(
        monkeypatch,
        {},
        payments,
    )


@given("the transaction history template is available")
def template_available(
    context,
):
    context.html = read_template()


# ============================================================
# BDD WHEN
# ============================================================


@when("the employer opens the transaction history page")
def open_transaction_history(
    context,
):
    context.response = open_transactions()


@when("the employer searches using a transaction ID")
def search_transaction_id(
    context,
):
    context.response = open_transactions(keyword="TXN001")


@when("the employer searches using a plan name")
def search_plan(
    context,
):
    context.response = open_transactions(keyword="Starter")


@when("the employer searches using the payment method")
def search_method(
    context,
):
    context.response = open_transactions(keyword="Card")


@when("the employer searches using lowercase text")
def search_lowercase(
    context,
):
    context.response = open_transactions(keyword="starter")


@when("the employer searches with surrounding spaces")
def search_spaces(
    context,
):
    context.response = open_transactions(keyword="   TXN001   ")


@when("the employer searches for a transaction that does not exist")
def search_missing(
    context,
):
    context.response = open_transactions(keyword="NOT-FOUND")


@when("the employer searches without a keyword")
def search_empty(
    context,
):
    context.response = open_transactions(keyword="")


@when("the employer filters by completed status")
def filter_completed(
    context,
):
    context.response = open_transactions(status="COMPLETED")


@when("the employer filters by pending status")
def filter_pending(
    context,
):
    context.response = open_transactions(status="PENDING")


@when("the employer filters by failed status")
def filter_failed(
    context,
):
    context.response = open_transactions(status="FAILED")


@when("the employer filters using lowercase completed status")
def filter_lowercase(
    context,
):
    context.response = open_transactions(status="completed")


@when("the employer filters using an invalid status")
def filter_invalid(
    context,
):
    context.response = open_transactions(status="INVALID")


@when("the employer searches and filters by status")
def search_and_filter_step(
    context,
):
    context.response = open_transactions(
        keyword="Starter",
        status="COMPLETED",
    )


@when("the employer opens transaction page two")
def page_two(
    context,
):
    context.response = open_transactions(page=2)


@when("transaction page zero is requested")
def page_zero(
    context,
):
    context.response = open_transactions(page=0)


@when("a negative transaction page is requested")
def negative_page(
    context,
):
    context.response = open_transactions(page=-5)


@when("a transaction page above the final page is requested")
def page_above_final(
    context,
):
    context.response = open_transactions(page=999)


@when("the employer opens the transaction history page expecting an error")
def open_error(
    context,
):
    try:
        context.response = open_transactions()

    except HTTPException as exc:
        context.error = exc


@when("the transaction history template is inspected")
def inspect_template(
    context,
):
    if not context.html:
        context.html = read_template()


# ============================================================
# BDD THEN
# ============================================================


@then("the transaction history page should be displayed")
def page_displayed(
    context,
):
    assert context.response["template"] == "employerTransactions.html"


@then("only the current company transactions should be displayed")
def current_company_only(
    context,
):
    ids = {item["transaction_id"] for item in context.response["context"]["transactions"]}

    assert ids == {
        "TXN001",
        "TXN002",
        "TXN003",
    }


@then("each transaction should contain the required transaction information")
def required_transaction_fields(
    context,
):
    required = {
        "transaction_id",
        "package",
        "amount",
        "currency",
        "status",
        "payment_method",
        "credits",
        "date",
        "time",
        "sort_date",
        "stripe_invoice_id",
    }

    for transaction in context.response["context"]["transactions"]:
        assert required.issubset(transaction.keys())


@then("only completed payment amounts should contribute to total spent")
def completed_spent_only(
    context,
):
    assert context.response["context"]["total_spent"] == 49.00


@then("the completed pending and failed counts should be correct")
def status_counts(
    context,
):
    data = context.response["context"]

    assert data["completed_count"] == 1
    assert data["pending_count"] == 1
    assert data["failed_count"] == 1


@then("only the matching transaction should be displayed")
def matching_id(
    context,
):
    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1
    assert transactions[0]["transaction_id"] == "TXN001"


@then("transactions matching the plan should be displayed")
def matching_plan(
    context,
):
    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1
    assert transactions[0]["package"] == "Starter Pack"


@then("transactions matching the payment method should be displayed")
def matching_method(
    context,
):
    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 3

    assert all(item["payment_method"] == "Card" for item in transactions)


@then("the transaction search should be case insensitive")
def search_case_insensitive(
    context,
):
    assert context.response["context"]["total_transactions"] == 1


@then("the surrounding search spaces should be ignored")
def spaces_ignored(
    context,
):
    assert context.response["context"]["total_transactions"] == 1


@then("the transaction result should be empty")
def empty_result(
    context,
):
    assert context.response["context"]["transactions"] == []


@then("all current company transactions should remain available")
def all_transactions(
    context,
):
    assert context.response["context"]["total_transactions"] == 3


def assert_only_status(
    context,
    expected,
):
    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    assert all(item["status"] == expected for item in transactions)


@then("only completed transactions should be displayed")
def only_completed(
    context,
):
    assert_only_status(
        context,
        "COMPLETED",
    )


@then("only pending transactions should be displayed")
def only_pending(
    context,
):
    assert_only_status(
        context,
        "PENDING",
    )


@then("only failed transactions should be displayed")
def only_failed(
    context,
):
    assert_only_status(
        context,
        "FAILED",
    )


@then("the status filter should be case insensitive")
def filter_case_insensitive(
    context,
):
    assert_only_status(
        context,
        "COMPLETED",
    )


@then("no transactions should match the invalid status")
def invalid_status_empty(
    context,
):
    assert context.response["context"]["transactions"] == []


@then("only transactions matching both criteria should be displayed")
def combined_filter(
    context,
):
    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1
    assert transactions[0]["transaction_id"] == "TXN001"
    assert transactions[0]["status"] == "COMPLETED"


@then("the completed date should be used")
def completed_date(
    context,
):
    transaction = context.response["context"]["transactions"][0]

    # Default data includes multiple records,
    # locate the completed transaction explicitly.
    transaction = next(
        item
        for item in context.response["context"]["transactions"]
        if item["transaction_id"] == "TXN001"
    )

    assert transaction["date"] == "10 Jan 2026"
    assert transaction["time"] == "11:30 AM"


@then("the created date should be used")
def created_date(
    context,
):
    transaction = next(
        item
        for item in context.response["context"]["transactions"]
        if item["transaction_id"] == "TXN002"
    )

    assert transaction["date"] == "15 Feb 2026"


@then("the missing transaction date should be represented safely")
def missing_date_safe(
    context,
):
    transaction = context.response["context"]["transactions"][0]

    assert transaction["date"] == "-"
    assert transaction["time"] == ""


@then("the missing package should be represented with a dash")
def missing_package_safe(
    context,
):
    assert context.response["context"]["transactions"][0]["package"] == "-"


@then("the missing payment method should be represented with a dash")
def missing_method_safe(
    context,
):
    assert context.response["context"]["transactions"][0]["payment_method"] == "-"


@then("the missing amount should default to zero")
def missing_amount_zero(
    context,
):
    assert context.response["context"]["transactions"][0]["amount"] == 0


@then("the missing credits should default to zero")
def missing_credits_zero(
    context,
):
    assert context.response["context"]["transactions"][0]["credits"] == 0


@then("the newest transaction should be displayed first")
def newest_first(
    context,
):
    assert context.response["context"]["transactions"][0]["transaction_id"] == "TXN003"


@then("only one transaction page should be required")
def one_page(
    context,
):
    assert context.response["context"]["total_pages"] == 1


@then("two transaction pages should be required")
def two_pages(
    context,
):
    assert context.response["context"]["total_pages"] == 2


@then("five transactions should be displayed on page two")
def five_on_second_page(
    context,
):
    assert len(context.response["context"]["transactions"]) == 5


@then("the current transaction page should be one")
def page_is_one(
    context,
):
    assert context.response["context"]["current_page"] == 1


@then("the final transaction page should be used")
def final_page(
    context,
):
    assert context.response["context"]["current_page"] == 2


@then("the transaction list should be empty")
def transaction_list_empty(
    context,
):
    data = context.response["context"]

    assert data["transactions"] == []
    assert data["total_transactions"] == 0
    assert data["total_spent"] == 0
    assert data["completed_count"] == 0
    assert data["pending_count"] == 0
    assert data["failed_count"] == 0
    assert data["total_pages"] == 1


@then("company not found should be returned")
def company_not_found(
    context,
):
    assert context.error is not None
    assert context.error.status_code == 404
    assert context.error.detail == "Company not found"


@then("completed transactions should provide a receipt link")
def receipt_link(
    context,
):
    assert "/payment-receipt/{{ transaction.transaction_id }}" in context.html

    assert 'transaction.status == "COMPLETED"' in context.html


@then("search and status filter controls should exist")
def filter_controls(
    context,
):
    assert 'id="transactionSearch"' in context.html
    assert 'id="statusFilter"' in context.html

    assert 'value="COMPLETED"' in context.html
    assert 'value="PENDING"' in context.html
    assert 'value="FAILED"' in context.html


@then("the no transactions message should exist")
def empty_state(
    context,
):
    assert "No transactions found" in context.html
