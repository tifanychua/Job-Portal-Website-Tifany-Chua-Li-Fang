import pytest
from datetime import datetime, timezone
from pathlib import Path

from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.routes import adminTransaction as transaction_module

# ============================================================
# CONSTANTS
# ============================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

COMPANY_NAME = "ABC Technology Sdn Bhd"

COMPANY_EMAIL = "hr@abctech.com"

TEMPLATE_PATH = Path("src/job_portal_web/ui/adminTransactions.html")


# ============================================================
# LOAD BDD FEATURE
# ============================================================

scenarios("features/viewTransactions.feature")


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

            return FakeDocumentSnapshot(self.document_id, {}, exists=False)

        return FakeDocumentSnapshot(self.document_id, data, exists=True)


class FakeCollection:

    def __init__(self, documents=None):
        self.documents = documents or {}

    def stream(self):

        return [
            FakeDocumentSnapshot(document_id, data, exists=True)
            for document_id, data in self.documents.items()
        ]

    def document(self, document_id):

        return FakeDocumentReference(self, document_id)


class FakeDB:

    def __init__(self, payments=None, companies=None):

        self.collections = {
            "payment": FakeCollection(payments or {}),
            "company": FakeCollection(companies or {}),
        }

    def collection(self, name):

        return self.collections[name]


# ============================================================
# FAKE TEMPLATE RESPONSE
# ============================================================


class FakeTemplates:

    def TemplateResponse(self, request, name, context):

        return {
            "template": name,
            "context": context,
        }


# ============================================================
# BDD CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.response = None

        self.payments = None

        self.companies = None

        self.template_text = ""

        self.expected = None


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
        }
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
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49.00,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 10, tzinfo=timezone.utc),
            "completed_at": datetime(year, 1, 11, tzinfo=timezone.utc),
        },
        "TXN002": {
            "company_id": COMPANY_ID,
            "package_name": "Business",
            "package": "Business",
            "payment_method": "Card",
            "amount": 129.00,
            "status": "PENDING",
            "created_at": datetime(year, 2, 15, tzinfo=timezone.utc),
        },
        "TXN003": {
            "company_id": COMPANY_ID,
            "package_name": "Enterprise",
            "package": "Enterprise",
            "payment_method": "Card",
            "amount": 249.00,
            "status": "FAILED",
            "created_at": datetime(year, 3, 20, tzinfo=timezone.utc),
        },
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(monkeypatch, payments, companies):

    fake_db = FakeDB(payments=payments, companies=companies)

    monkeypatch.setattr(transaction_module, "db", fake_db)

    monkeypatch.setattr(transaction_module, "templates", FakeTemplates())

    return fake_db


@pytest.fixture
def setup_db(monkeypatch, payments, companies):

    return install_fake_db(monkeypatch, payments, companies)


# ============================================================
# HELPER - OPEN TRANSACTION PAGE
# ============================================================


def get_page(status="", keyword="", page=1):

    return transaction_module.transaction_management(
        request=None, status=status, keyword=keyword, page=page
    )


# ============================================================
# HELPER - CREATE MANY TRANSACTIONS
# ============================================================


def create_transactions(count):

    year = datetime.now(timezone.utc).year

    result = {}

    for number in range(1, count + 1):

        result[f"TXN{number:03d}"] = {
            "company_id": COMPANY_ID,
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 10.00,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }

    return result


# ============================================================
# HELPER - READ HTML TEMPLATE
# ============================================================


def read_template():

    return TEMPLATE_PATH.read_text(encoding="utf-8")


# ============================================================
# 1. VIEW TRANSACTION PAGE
# ============================================================


def test_view_transaction_management_page(setup_db):

    response = get_page()

    assert response["template"] == "adminTransactions.html"

    print("✅ SUCCESS: Transaction management page displayed")


# ============================================================
# 2. VIEW ALL TRANSACTIONS
# ============================================================


def test_view_all_transactions(setup_db):

    response = get_page()

    data = response["context"]

    assert data["total_transactions"] == 3

    assert len(data["transactions"]) == 3

    print("✅ SUCCESS: All transactions displayed")


# ============================================================
# 3. REQUIRED TRANSACTION INFORMATION
# ============================================================


def test_transaction_contains_required_information(setup_db):

    response = get_page(keyword="TXN001")

    transaction = response["context"]["transactions"][0]

    required_fields = [
        "transaction_id",
        "company_name",
        "company_email",
        "package",
        "payment_method",
        "amount",
        "status",
        "display_date",
    ]

    missing = []

    for field in required_fields:

        if field not in transaction:
            missing.append(field)

    assert missing == []

    print("✅ SUCCESS: Required transaction " "information available")


# ============================================================
# 4. COMPANY INFORMATION
# ============================================================


def test_valid_company_information_loaded(setup_db):

    response = get_page(keyword="TXN001")

    transaction = response["context"]["transactions"][0]

    assert transaction["company_name"] == COMPANY_NAME

    assert transaction["company_email"] == COMPANY_EMAIL

    print("✅ SUCCESS: Company information retrieved")


# ============================================================
# 5. PAYMENT METHOD
# ============================================================


def test_payment_method_is_card(setup_db):

    response = get_page()

    transactions = response["context"]["transactions"]

    for transaction in transactions:

        assert transaction["payment_method"] == "Card"

    print("✅ SUCCESS: Payment method is Card")


# ============================================================
# 6. MISSING COMPANY
# ============================================================


def test_missing_company_does_not_crash(monkeypatch, payments):

    install_fake_db(monkeypatch, payments, {})

    response = get_page()

    assert response["context"]["total_transactions"] == 3

    for transaction in response["context"]["transactions"]:

        assert transaction["company_name"] == ""

    print("✅ SUCCESS: Missing company handled safely")


# ============================================================
# 7. MISSING COMPANY ID
# ============================================================


def test_missing_company_id_does_not_crash(monkeypatch, companies):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN100": {
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)

    response = get_page()

    transaction = response["context"]["transactions"][0]

    assert transaction["company_name"] == ""

    assert transaction["company_email"] == ""

    print("✅ SUCCESS: Missing company ID handled safely")


# ============================================================
# 8. SEARCH TESTS
# ============================================================


@pytest.mark.parametrize(
    "keyword, expected_count",
    [
        ("TXN001", 1),
        ("txn001", 1),
        ("ABC Technology Sdn Bhd", 3),
        ("abc technology", 3),
        ("ABC", 3),
        ("hr@abctech.com", 3),
        ("Starter", 1),
        ("starter", 1),
        ("Business", 1),
        ("business", 1),
        ("Enterprise", 1),
        ("enterprise", 1),
    ],
)
def test_search_transaction(setup_db, keyword, expected_count):

    response = get_page(keyword=keyword)

    assert response["context"]["total_transactions"] == expected_count

    print(f"✅ SUCCESS: Search '{keyword}' " f"returned {expected_count} result(s)")


# ============================================================
# 9. PARTIAL SEARCH
# ============================================================


def test_search_partial_keyword(setup_db):

    response = get_page(keyword="ABC")

    assert response["context"]["total_transactions"] == 3

    print("✅ SUCCESS: Partial search works")


# ============================================================
# 10. CASE INSENSITIVE SEARCH
# ============================================================


def test_search_case_insensitive(setup_db):

    lower = get_page(keyword="abc technology")

    upper = get_page(keyword="ABC TECHNOLOGY")

    assert lower["context"]["total_transactions"] == upper["context"]["total_transactions"]

    assert lower["context"]["total_transactions"] == 3

    print("✅ SUCCESS: Search is case insensitive")


# ============================================================
# 11. SEARCH WITH EXTRA SPACES
# ============================================================


def test_search_ignores_extra_spaces(setup_db):

    response = get_page(keyword="   TXN001   ")

    assert response["context"]["total_transactions"] == 1

    print("✅ SUCCESS: Extra spaces ignored")


# ============================================================
# 12. EMPTY SEARCH
# ============================================================


def test_empty_search_returns_all_transactions(setup_db):

    response = get_page(keyword="")

    assert response["context"]["total_transactions"] == 3

    print("✅ SUCCESS: Empty search shows all transactions")


# ============================================================
# 13. SEARCH NO RESULT
# ============================================================


def test_non_existing_search_returns_zero(setup_db):

    response = get_page(keyword="DOES-NOT-EXIST")

    assert response["context"]["total_transactions"] == 0

    assert response["context"]["transactions"] == []

    print("✅ SUCCESS: No matching transaction handled")


# ============================================================
# 14. STATUS FILTER
# ============================================================


@pytest.mark.parametrize(
    "status, expected",
    [
        ("COMPLETED", 1),
        ("PENDING", 1),
        ("FAILED", 1),
        ("completed", 1),
        ("pending", 1),
        ("failed", 1),
    ],
)
def test_filter_transaction_status(setup_db, status, expected):

    response = get_page(status=status)

    assert response["context"]["total_transactions"] == expected

    print(f"✅ SUCCESS: {status} filter works")


# ============================================================
# 15. ALL STATUS
# ============================================================


def test_all_status_returns_all_transactions(setup_db):

    response = get_page(status="")

    assert response["context"]["total_transactions"] == 3

    print("✅ SUCCESS: All Status shows all transactions")


# ============================================================
# 16. INVALID STATUS
# ============================================================


def test_invalid_status_returns_no_transaction(setup_db):

    response = get_page(status="INVALID")

    assert response["context"]["total_transactions"] == 0

    print("✅ SUCCESS: Invalid status handled safely")


# ============================================================
# 17. SEARCH + STATUS
# ============================================================


def test_search_and_status_filter_together(setup_db):

    response = get_page(keyword="ABC", status="COMPLETED")

    assert response["context"]["total_transactions"] == 1

    transaction = response["context"]["transactions"][0]

    assert transaction["transaction_id"] == "TXN001"

    assert transaction["status"] == "COMPLETED"

    print("✅ SUCCESS: Search and status filter " "work together")


# ============================================================
# 18. COMPLETED DATE PRIORITY
# ============================================================


def test_completed_date_has_priority(setup_db):

    response = get_page(keyword="TXN001")

    transaction = response["context"]["transactions"][0]

    assert transaction["display_date"] == transaction["completed_at"]

    print("✅ SUCCESS: completed_at used first")


# ============================================================
# 19. CREATED DATE FALLBACK
# ============================================================


def test_created_date_used_when_completed_missing(setup_db):

    response = get_page(keyword="TXN002")

    transaction = response["context"]["transactions"][0]

    assert transaction["display_date"] == transaction["created_at"]

    print("✅ SUCCESS: created_at used as fallback")


# ============================================================
# 20. MISSING TRANSACTION DATE
# ============================================================


def test_missing_transaction_date(monkeypatch, companies):

    custom_payments = {
        "TXN999": {
            "company_id": COMPANY_ID,
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)

    response = get_page()

    transaction = response["context"]["transactions"][0]

    assert transaction["display_date"] is None

    print("✅ SUCCESS: Missing date handled safely")


# ============================================================
# 21. TOTAL TRANSACTIONS
# ============================================================


def test_total_transaction_count(setup_db):

    response = get_page()

    assert response["context"]["total_transactions"] == 3

    print("✅ SUCCESS: Total transaction count correct")


# ============================================================
# 22. SUCCESSFUL COUNT
# ============================================================


def test_successful_transaction_count(setup_db):

    response = get_page()

    assert response["context"]["successful"] == 1

    print("✅ SUCCESS: Successful count correct")


# ============================================================
# 23. PENDING COUNT
# ============================================================


def test_pending_transaction_count(setup_db):

    response = get_page()

    assert response["context"]["pending"] == 1

    print("✅ SUCCESS: Pending count correct")


# ============================================================
# 24. FAILED COUNT
# ============================================================


def test_failed_transaction_count(setup_db):

    response = get_page()

    assert response["context"]["failed"] == 1

    print("✅ SUCCESS: Failed count correct")


# ============================================================
# 25. CURRENT YEAR REVENUE
# ============================================================


def test_only_completed_payment_contributes_revenue(setup_db):

    response = get_page()

    assert response["context"]["total_revenue"] == 49.00

    print("✅ SUCCESS: Only completed current-year " "payment contributes revenue")


# ============================================================
# 26. PENDING NOT REVENUE
# ============================================================


def test_pending_payment_not_in_revenue(setup_db):

    response = get_page(status="PENDING")

    assert response["context"]["total_revenue"] == 0

    print("✅ SUCCESS: Pending payment excluded from revenue")


# ============================================================
# 27. FAILED NOT REVENUE
# ============================================================


def test_failed_payment_not_in_revenue(setup_db):

    response = get_page(status="FAILED")

    assert response["context"]["total_revenue"] == 0

    print("✅ SUCCESS: Failed payment excluded from revenue")


# ============================================================
# 28. PREVIOUS YEAR NOT CURRENT YEAR REVENUE
# ============================================================


def test_previous_year_payment_not_current_revenue(monkeypatch, companies):

    current_year = datetime.now(timezone.utc).year

    custom_payments = {
        "OLD001": {
            "company_id": COMPANY_ID,
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 500,
            "status": "COMPLETED",
            "completed_at": datetime(current_year - 1, 12, 1, tzinfo=timezone.utc),
        },
        "NEW001": {
            "company_id": COMPANY_ID,
            "package_name": "Business",
            "package": "Business",
            "payment_method": "Card",
            "amount": 100,
            "status": "COMPLETED",
            "completed_at": datetime(current_year, 1, 1, tzinfo=timezone.utc),
        },
    }

    install_fake_db(monkeypatch, custom_payments, companies)

    response = get_page()

    assert response["context"]["total_revenue"] == 100

    print("✅ SUCCESS: Previous-year payment excluded")


# ============================================================
# 29. MISSING AMOUNT
# ============================================================


def test_missing_amount_treated_as_zero(monkeypatch, companies):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "status": "COMPLETED",
            "completed_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)

    response = get_page()

    assert response["context"]["total_revenue"] == 0

    print("✅ SUCCESS: Missing amount treated as zero")


# ============================================================
# 30. ZERO AMOUNT
# ============================================================


def test_zero_amount_transaction(monkeypatch, companies):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXNZERO": {
            "company_id": COMPANY_ID,
            "package_name": "Starter",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 0,
            "status": "COMPLETED",
            "completed_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)

    response = get_page()

    assert response["context"]["total_revenue"] == 0

    assert response["context"]["successful"] == 1

    print("✅ SUCCESS: Zero amount handled correctly")


# ============================================================
# 31. NEWEST FIRST
# ============================================================


def test_newest_transaction_first(setup_db):

    response = get_page()

    transactions = response["context"]["transactions"]

    assert transactions[0]["transaction_id"] == "TXN003"

    assert transactions[1]["transaction_id"] == "TXN002"

    assert transactions[2]["transaction_id"] == "TXN001"

    print("✅ SUCCESS: Transactions sorted newest first")


# ============================================================
# 32. LESS THAN 20 = ONE PAGE
# ============================================================


def test_less_than_20_transactions_one_page(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(10), companies)

    response = get_page()

    assert response["context"]["total_pages"] == 1

    assert len(response["context"]["transactions"]) == 10

    print("✅ SUCCESS: Less than 20 records = 1 page")


# ============================================================
# 33. EXACTLY 20 = ONE PAGE
# ============================================================


def test_exactly_20_transactions_one_page(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(20), companies)

    response = get_page()

    assert response["context"]["total_pages"] == 1

    assert len(response["context"]["transactions"]) == 20

    print("✅ SUCCESS: Exactly 20 records = 1 page")


# ============================================================
# 34. 21 = TWO PAGES
# ============================================================


def test_21_transactions_two_pages(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(21), companies)

    response = get_page()

    assert response["context"]["total_pages"] == 2

    print("✅ SUCCESS: 21 records = 2 pages")


# ============================================================
# 35. FIRST PAGE MAXIMUM 20
# ============================================================


def test_first_page_maximum_20_records(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(25), companies)

    response = get_page(page=1)

    assert len(response["context"]["transactions"]) == 20

    print("✅ SUCCESS: First page contains 20 records")


# ============================================================
# 36. SECOND PAGE REMAINING
# ============================================================


def test_second_page_remaining_records(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(25), companies)

    response = get_page(page=2)

    assert len(response["context"]["transactions"]) == 5

    assert response["context"]["current_page"] == 2

    print("✅ SUCCESS: Second page contains remaining 5")


# ============================================================
# 37. PAGE ZERO
# ============================================================


def test_page_zero_becomes_page_one(setup_db):

    response = get_page(page=0)

    assert response["context"]["current_page"] == 1

    print("✅ SUCCESS: Page 0 becomes page 1")


# ============================================================
# 38. NEGATIVE PAGE
# ============================================================


def test_negative_page_becomes_page_one(setup_db):

    response = get_page(page=-5)

    assert response["context"]["current_page"] == 1

    print("✅ SUCCESS: Negative page becomes page 1")


# ============================================================
# 39. PAGE ABOVE LAST
# ============================================================


def test_page_above_total_becomes_last_page(monkeypatch, companies):

    install_fake_db(monkeypatch, create_transactions(25), companies)

    response = get_page(page=999)

    assert response["context"]["current_page"] == 2

    print("✅ SUCCESS: Excessive page becomes last page")


# ============================================================
# 40. EMPTY DATABASE
# ============================================================


def test_no_transactions_available(monkeypatch, companies):

    install_fake_db(monkeypatch, {}, companies)

    response = get_page()

    data = response["context"]

    assert data["total_transactions"] == 0

    assert data["transactions"] == []

    assert data["total_revenue"] == 0

    assert data["successful"] == 0

    assert data["pending"] == 0

    assert data["failed"] == 0

    print("✅ SUCCESS: Empty transaction list handled")


# ============================================================
# FRONTEND DATE FILTER TESTS
#
# The transaction management date filter is JavaScript-side.
# These acceptance tests verify the necessary UI/validation
# controls are present in adminTransactions.html.
# ============================================================


def test_date_filter_controls_exist():

    html = read_template()

    assert 'id="dateFilterBtn"' in html

    assert 'id="fromDate"' in html

    assert 'id="toDate"' in html

    assert 'id="applyDateBtn"' in html

    assert 'id="clearDateBtn"' in html

    print("✅ SUCCESS: Date filter controls available")


def test_future_dates_are_restricted():

    html = read_template()

    assert "const today = " 'new Date().toISOString().split("T")[0]' in html

    assert "fromDate.max = today" in html

    assert "toDate.max = today" in html

    print("✅ SUCCESS: Future transaction dates restricted")


def test_from_date_after_to_date_validation_exists():

    html = read_template()

    assert "activeFromDate > activeToDate" in html

    assert "From Date cannot be later than To Date." in html

    print("✅ SUCCESS: Invalid date range validation exists")


def test_clear_date_filter_exists():

    html = read_template()

    assert 'clearDateBtn.addEventListener("click"' in html

    assert 'activeFromDate = ""' in html

    assert 'activeToDate = ""' in html

    print("✅ SUCCESS: Clear date filter resets values")


def test_no_transaction_message_exists():

    html = read_template()

    assert "No transactions found." in html

    assert 'id="noTransactionMessage"' in html

    print("✅ SUCCESS: No transaction message exists")


# ============================================================
# BDD STEP DEFINITIONS
# ============================================================


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------


@given("the admin is logged into the system")
def admin_logged_in():

    print("✅ Admin login assumed for acceptance testing")


# ------------------------------------------------------------
# VIEW PAGE
# ------------------------------------------------------------


@given("the admin is viewing the transaction management page")
def admin_viewing_transaction_page(setup_db, context):

    context.response = get_page()


@when("the admin opens the transaction management page")
def open_transaction_page(setup_db, context):

    context.response = get_page()


@when("the admin views the transaction management page")
def admin_views_transaction_management_page(context):

    context.response = get_page()


@then("the system should display the transaction management page")
def verify_transaction_page(context):

    assert context.response["template"] == "adminTransactions.html"


# ------------------------------------------------------------
# LOAD RECORDS
# ------------------------------------------------------------


@when("the transaction records are loaded")
def transaction_records_loaded(context):

    # Load/process the transaction records
    # if they have not already been loaded
    if context.response is None:
        context.response = get_page()

    assert context.response is not None


@then("the system should display the transaction records")
def verify_transaction_records(context):

    assert len(context.response["context"]["transactions"]) == 3


@then("each transaction should display the required transaction information")
def verify_required_transaction_information(context):

    transactions = context.response["context"]["transactions"]

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


@then("the transaction payment status should be displayed")
def verify_transaction_status(context):

    transactions = context.response["context"]["transactions"]

    for transaction in transactions:

        assert transaction["status"] in [
            "COMPLETED",
            "PENDING",
            "FAILED",
        ]


@then("the system should display the transaction summary")
def verify_transaction_summary(context):

    data = context.response["context"]

    assert data["total_transactions"] == 3

    assert data["successful"] == 1

    assert data["pending"] == 1

    assert data["failed"] == 1

    assert data["total_revenue"] == 49.00


# ------------------------------------------------------------
# SEARCH TRANSACTION ID
# ------------------------------------------------------------


@when("the admin searches using a transaction ID")
def search_by_transaction_id(setup_db, context):

    context.response = get_page(keyword="TXN001")


@then("the matching transaction should be displayed")
def matching_transaction_displayed(context):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    assert transactions[0]["transaction_id"] == "TXN001"


# ------------------------------------------------------------
# SEARCH COMPANY
# ------------------------------------------------------------


@when("the admin searches using a company name")
def search_company_name(setup_db, context):

    context.response = get_page(keyword=COMPANY_NAME)


@then("the matching company transactions should be displayed")
def matching_company_transactions(context):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 3

    for transaction in transactions:

        assert transaction["company_name"] == COMPANY_NAME


# ------------------------------------------------------------
# LOWERCASE SEARCH
# ------------------------------------------------------------


@when("the admin searches using a lowercase keyword")
def lowercase_search(setup_db, context):

    context.response = get_page(keyword="abc technology")


@then("the search should be case insensitive")
def verify_case_insensitive(context):

    assert context.response["context"]["total_transactions"] == 3


# ------------------------------------------------------------
# PARTIAL SEARCH
# ------------------------------------------------------------


@when("the admin searches using a partial keyword")
def partial_search(setup_db, context):

    context.response = get_page(keyword="ABC")


@then("transactions containing the keyword should be displayed")
def verify_partial_search(context):

    assert context.response["context"]["total_transactions"] == 3


# ------------------------------------------------------------
# INVALID SEARCH
# ------------------------------------------------------------


@when("the admin searches using a non existing transaction")
def search_missing_transaction(setup_db, context):

    context.response = get_page(keyword="NOTEXIST")


@then("the system should return no matching transactions without an error")
def verify_no_search_result(context):

    assert context.response["context"]["total_transactions"] == 0

    assert context.response["context"]["transactions"] == []


# ------------------------------------------------------------
# EMPTY SEARCH
# ------------------------------------------------------------


@when("the admin searches without entering a keyword")
def empty_keyword(setup_db, context):

    context.response = get_page(keyword="")


@then("all available transactions should remain accessible")
def verify_all_available_transactions(context):

    assert context.response["context"]["total_transactions"] == 3


# ------------------------------------------------------------
# COMPLETED FILTER
# ------------------------------------------------------------


@when("the admin selects the completed status")
def select_completed_status(setup_db, context):

    context.response = get_page(status="COMPLETED")


@then("only completed transactions should match the status filter")
def verify_completed_status(context):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    for transaction in transactions:

        assert transaction["status"] == "COMPLETED"


# ------------------------------------------------------------
# PENDING FILTER
# ------------------------------------------------------------


@when("the admin selects the pending status")
def select_pending_status(setup_db, context):

    context.response = get_page(status="PENDING")


@then("only pending transactions should match the status filter")
def verify_pending_status(context):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    for transaction in transactions:

        assert transaction["status"] == "PENDING"


# ------------------------------------------------------------
# FAILED FILTER
# ------------------------------------------------------------


@when("the admin selects the failed status")
def select_failed_status(setup_db, context):

    context.response = get_page(status="FAILED")


@then("only failed transactions should match the status filter")
def verify_failed_status(context):

    transactions = context.response["context"]["transactions"]

    assert len(transactions) == 1

    for transaction in transactions:

        assert transaction["status"] == "FAILED"


# ------------------------------------------------------------
# ALL STATUS
# ------------------------------------------------------------


@when("the admin selects all status")
def select_all_status(setup_db, context):

    context.response = get_page(status="")


@then("transactions of all statuses should be available")
def verify_all_status(context):

    assert context.response["context"]["total_transactions"] == 3


# ------------------------------------------------------------
# INVALID STATUS
# ------------------------------------------------------------


@when("an invalid transaction status is supplied")
def invalid_status(setup_db, context):

    context.response = get_page(status="INVALID")


@then("the system should handle the invalid status without crashing")
def verify_invalid_status(context):

    assert context.response is not None

    assert context.response["context"]["total_transactions"] == 0


# ------------------------------------------------------------
# DATE FILTER UI
# ------------------------------------------------------------


@when("the admin opens the date filter")
def open_date_filter(context):

    context.template_text = read_template()


@then("the system should provide from date and to date filters")
def verify_date_controls(context):

    assert 'id="fromDate"' in context.template_text

    assert 'id="toDate"' in context.template_text


@when("the admin selects a valid transaction date range")
def valid_transaction_date_range(context):

    context.template_text = read_template()


@then("the date filter controls should support the selected range")
def verify_valid_date_filter(context):

    assert "toDate.min = fromDate.value" in context.template_text

    assert "fromDate.max = toDate.value" in context.template_text


@when("the transaction date filter is displayed")
def transaction_date_filter_displayed(context):

    context.template_text = read_template()


@then("future transaction dates should not be allowed")
def verify_future_dates_not_allowed(context):

    assert "fromDate.max = today" in context.template_text

    assert "toDate.max = today" in context.template_text


@when("the from date is later than the to date")
def invalid_transaction_date_range(context):

    context.template_text = read_template()


@then("the invalid transaction date range should be prevented")
def verify_invalid_transaction_date_range(context):

    assert "activeFromDate > activeToDate" in context.template_text

    assert "From Date cannot be later than To Date." in context.template_text


@when("the admin clears the transaction date filter")
def clear_transaction_date_filter(context):

    context.template_text = read_template()


@then("the transaction date filter should return to its default state")
def verify_clear_transaction_date(context):

    assert 'fromDate.value = ""' in context.template_text

    assert 'toDate.value = ""' in context.template_text

    assert 'activeFromDate = ""' in context.template_text

    assert 'activeToDate = ""' in context.template_text


# ------------------------------------------------------------
# BOTH CREATED AND COMPLETED DATE
# ------------------------------------------------------------


@given("a transaction contains both created date and completed date")
def transaction_has_both_dates(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    context.payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
            "completed_at": datetime(year, 1, 2, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, context.payments, companies)


@when("the transaction date is determined")
def determine_transaction_date(context):

    context.response = get_page()


@then("the completed date should be used as the transaction date")
def verify_completed_date_used(context):

    transaction = context.response["context"]["transactions"][0]

    assert transaction["display_date"] == transaction["completed_at"]


# ------------------------------------------------------------
# COMPLETED DATE MISSING
# ------------------------------------------------------------


@given("a transaction does not contain a completed date")
def transaction_without_completed_date(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    context.payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "PENDING",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, context.payments, companies)


@then("the created date should be used as the transaction date")
def verify_created_date_used(context):

    transaction = context.response["context"]["transactions"][0]

    assert transaction["display_date"] == transaction["created_at"]


# ------------------------------------------------------------
# NO DATE
# ------------------------------------------------------------


@given("a transaction does not contain a created date or completed date")
def transaction_without_any_date(monkeypatch, companies, context):

    context.payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
        }
    }

    install_fake_db(monkeypatch, context.payments, companies)


@when("the transaction management page processes the transaction")
def process_transaction(context):

    context.response = get_page()


@then("the system should handle the missing transaction date without crashing")
def verify_missing_transaction_date_safe(context):

    assert context.response["context"]["total_transactions"] == 1

    transaction = context.response["context"]["transactions"][0]

    assert transaction["display_date"] is None


# ------------------------------------------------------------
# VALID COMPANY
# ------------------------------------------------------------


@given("a transaction contains a valid company ID")
def valid_company_id(setup_db, context):

    context.response = get_page(keyword="TXN001")


@then("the corresponding company information should be associated with the transaction")
def verify_company_associated(context):

    transaction = context.response["context"]["transactions"][0]

    assert transaction["company_name"] == COMPANY_NAME


# ------------------------------------------------------------
# UNKNOWN COMPANY
# ------------------------------------------------------------


@given("a transaction contains an unknown company ID")
def transaction_unknown_company(monkeypatch, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": "UNKNOWN-COMPANY",
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, {})


@then("the system should handle the missing company without crashing")
def verify_unknown_company_safe(context):

    transaction = context.response["context"]["transactions"][0]

    assert transaction["company_name"] == ""


# ------------------------------------------------------------
# NO COMPANY ID
# ------------------------------------------------------------


@given("a transaction does not contain a company ID")
def transaction_without_company_id(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "package": "Starter",
            "payment_method": "Card",
            "amount": 49,
            "status": "COMPLETED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@then("the system should handle the missing company ID without crashing")
def verify_missing_company_id_safe(context):

    transaction = context.response["context"]["transactions"][0]

    assert transaction["company_name"] == ""


# ------------------------------------------------------------
# CURRENT YEAR COMPLETED REVENUE
# ------------------------------------------------------------


@given("a completed transaction belongs to the current year")
def completed_current_year(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "amount": 100,
            "status": "COMPLETED",
            "completed_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@when("the transaction summary is calculated")
def calculate_summary(context):

    context.response = get_page()


@then("the completed payment amount should contribute to total revenue")
def verify_completed_contributes_revenue(context):

    assert context.response["context"]["total_revenue"] == 100


# ------------------------------------------------------------
# PENDING REVENUE
# ------------------------------------------------------------


@given("a pending transaction exists")
def pending_transaction_exists(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Business",
            "payment_method": "Card",
            "amount": 129,
            "status": "PENDING",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@then("the pending payment amount should not contribute to total revenue")
def verify_pending_not_revenue(context):

    assert context.response["context"]["total_revenue"] == 0


# ------------------------------------------------------------
# FAILED REVENUE
# ------------------------------------------------------------


@given("a failed transaction exists")
def failed_transaction_exists(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Enterprise",
            "payment_method": "Card",
            "amount": 249,
            "status": "FAILED",
            "created_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@then("the failed payment amount should not contribute to total revenue")
def verify_failed_not_revenue(context):

    assert context.response["context"]["total_revenue"] == 0


# ------------------------------------------------------------
# PREVIOUS YEAR
# ------------------------------------------------------------


@given("a completed transaction belongs to the previous year")
def previous_year_transaction(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "amount": 500,
            "status": "COMPLETED",
            "completed_at": datetime(year - 1, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@then("the previous year payment should not contribute to current year revenue")
def verify_previous_year_not_revenue(context):

    assert context.response["context"]["total_revenue"] == 0


# ------------------------------------------------------------
# MISSING AMOUNT
# ------------------------------------------------------------


@given("a transaction does not contain an amount")
def transaction_without_amount(monkeypatch, companies, context):

    year = datetime.now(timezone.utc).year

    custom_payments = {
        "TXN001": {
            "company_id": COMPANY_ID,
            "package": "Starter",
            "payment_method": "Card",
            "status": "COMPLETED",
            "completed_at": datetime(year, 1, 1, tzinfo=timezone.utc),
        }
    }

    install_fake_db(monkeypatch, custom_payments, companies)


@then("the missing amount should be treated as zero")
def verify_missing_amount_zero(context):

    assert context.response["context"]["total_revenue"] == 0


# ------------------------------------------------------------
# SORTING
# ------------------------------------------------------------


@given("multiple transactions exist with different dates")
def transactions_different_dates(setup_db, context):

    context.response = get_page()


@then("the newest transaction should be displayed before older transactions")
def verify_newest_first(context):

    transactions = context.response["context"]["transactions"]

    assert transactions[0]["transaction_id"] == "TXN003"

    assert transactions[-1]["transaction_id"] == "TXN001"


# ------------------------------------------------------------
# LESS THAN 20
# ------------------------------------------------------------


@given("fewer than twenty transactions exist")
def fewer_than_twenty(monkeypatch, companies, context):

    install_fake_db(monkeypatch, create_transactions(10), companies)


@when("the admin views the first transaction page")
def view_first_transaction_page(context):

    context.response = get_page(page=1)


@then("only one transaction page should be required")
def verify_one_page(context):

    assert context.response["context"]["total_pages"] == 1


# ------------------------------------------------------------
# EXACTLY 20
# ------------------------------------------------------------


@given("exactly twenty transactions exist")
def exactly_twenty(monkeypatch, companies, context):

    install_fake_db(monkeypatch, create_transactions(20), companies)


@when("the admin views the transaction list")
def view_transaction_list(context):

    context.response = get_page()


# ------------------------------------------------------------
# 21 TRANSACTIONS
# ------------------------------------------------------------


@given("twenty one transactions exist")
def twenty_one_transactions(monkeypatch, companies, context):

    install_fake_db(monkeypatch, create_transactions(21), companies)


@then("two transaction pages should be required")
def verify_two_pages(context):

    assert context.response["context"]["total_pages"] == 2


# ------------------------------------------------------------
# PAGE 2
# ------------------------------------------------------------


@given("more than twenty transactions exist")
def more_than_twenty(monkeypatch, companies, context):

    install_fake_db(monkeypatch, create_transactions(25), companies)


@when("the admin opens transaction page two")
def open_transaction_page_two(context):

    context.response = get_page(page=2)


@then("the remaining transactions should be displayed")
def verify_remaining_transactions(context):

    assert context.response["context"]["current_page"] == 2

    assert len(context.response["context"]["transactions"]) == 5


# ------------------------------------------------------------
# RECORDS AVAILABLE
# ------------------------------------------------------------


@given("transaction records are available")
def transaction_records_available(setup_db):

    pass


@when("transaction page zero is requested")
def page_zero_requested(context):

    context.response = get_page(page=0)


@then("the system should use transaction page one")
def verify_page_one(context):

    assert context.response["context"]["current_page"] == 1


@when("a negative transaction page is requested")
def negative_page_requested(context):

    context.response = get_page(page=-5)


@given("transaction records are available")
def transaction_records_available_again(setup_db):

    pass


# ------------------------------------------------------------
# PAGE > FINAL
# ------------------------------------------------------------


@when("a transaction page greater than the final page is requested")
def excessive_page_requested(monkeypatch, companies, context):

    install_fake_db(monkeypatch, create_transactions(25), companies)

    context.response = get_page(page=999)


@then("the system should use the final transaction page")
def verify_final_page(context):

    assert context.response["context"]["current_page"] == 2


# ------------------------------------------------------------
# EMPTY LIST
# ------------------------------------------------------------


@given("no transaction records exist")
def no_transaction_records(monkeypatch, companies, context):

    install_fake_db(monkeypatch, {}, companies)


@then("the system should handle the empty transaction list successfully")
def verify_empty_transaction_list(context):

    data = context.response["context"]

    assert data["total_transactions"] == 0

    assert data["transactions"] == []

    assert data["total_revenue"] == 0
