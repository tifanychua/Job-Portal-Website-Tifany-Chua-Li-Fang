import os
import pytest

from datetime import datetime, timezone

from pytest_bdd import given, scenarios, then, when

from job_portal_web.backend.routes import (
    adminTransaction as transaction_module
)


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

scenarios(
    "features/generateTransactionReport.feature"
)


# ============================================================
# FAKE FIRESTORE
# ============================================================

class FakeDocumentSnapshot:

    def __init__(
        self,
        document_id,
        data=None,
        exists=True
    ):

        self.id = document_id

        self._data = (
            data.copy()
            if data
            else {}
        )

        self.exists = exists


    def to_dict(self):

        return self._data.copy()


class FakeDocumentReference:

    def __init__(
        self,
        collection,
        document_id
    ):

        self.collection = collection

        self.document_id = document_id


    def get(self):

        data = (
            self.collection
            .documents
            .get(self.document_id)
        )

        if data is None:

            return FakeDocumentSnapshot(
                self.document_id,
                {},
                exists=False
            )

        return FakeDocumentSnapshot(
            self.document_id,
            data,
            exists=True
        )


class FakeCollection:

    def __init__(
        self,
        documents=None
    ):

        self.documents = (
            documents.copy()
            if documents
            else {}
        )


    def stream(self):

        return [
            FakeDocumentSnapshot(
                document_id,
                data,
                exists=True
            )
            for document_id, data
            in self.documents.items()
        ]


    def document(
        self,
        document_id
    ):

        return FakeDocumentReference(
            self,
            document_id
        )


class FakeDB:

    def __init__(
        self,
        payments=None,
        companies=None
    ):

        self.collections = {

            "payment": FakeCollection(
                payments or {}
            ),

            "company": FakeCollection(
                companies or {}
            )
        }


    def collection(
        self,
        name
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
        context
    ):

        return {

            "template": name,

            "context": context
        }


# ============================================================
# CONTEXT
# ============================================================

class Context:

    def __init__(self):

        self.response = None

        self.payments = None

        self.companies = None

        self.captured_pdf_text = []

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

            "businessEmail": COMPANY_EMAIL
        }
    }


# ============================================================
# PAYMENT FIXTURE
# ============================================================

@pytest.fixture
def payments():

    year = datetime.now(
        timezone.utc
    ).year

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
                tzinfo=timezone.utc
            ),

            "completed_at": datetime(
                year,
                1,
                15,
                tzinfo=timezone.utc
            )
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
                tzinfo=timezone.utc
            )
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
                tzinfo=timezone.utc
            )
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
                tzinfo=timezone.utc
            ),

            "completed_at": datetime(
                year,
                4,
                15,
                tzinfo=timezone.utc
            )
        }
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================

def install_fake_db(
    monkeypatch,
    payments,
    companies,
    patch_templates=True
):

    fake_db = FakeDB(
        payments=payments,
        companies=companies
    )

    monkeypatch.setattr(
        transaction_module,
        "db",
        fake_db
    )

    if patch_templates:

        monkeypatch.setattr(
            transaction_module,
            "templates",
            FakeTemplates()
        )

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    companies,
    payments
):

    return install_fake_db(
        monkeypatch,
        payments,
        companies
    )


# ============================================================
# REPORT HELPER
# ============================================================

def generate_report(
    from_date="",
    to_date="",
    status="",
    generate=""
):

    return (
        transaction_module
        .transaction_report_page(
            request=None,
            from_date=from_date,
            to_date=to_date,
            status=status,
            generate=generate
        )
    )


# ============================================================
# PDF HELPER
# ============================================================

def download_report(
    from_date="",
    to_date="",
    status=""
):

    return (
        transaction_module
        .download_transaction_report(
            from_date=from_date,
            to_date=to_date,
            status=status
        )
    )


# ============================================================
# CAPTURE TEXT SENT TO REPORTLAB
#
# This allows us to verify things such as:
# - missing company is shown as "-"
# - missing date is shown as "-"
# - correct revenue appears in PDF
# ============================================================

def capture_pdf_paragraphs(
    monkeypatch,
    context
):

    original_paragraph = (
        transaction_module.Paragraph
    )

    def paragraph_spy(
        text,
        style,
        *args,
        **kwargs
    ):

        context.captured_pdf_text.append(
            str(text)
        )

        return original_paragraph(
            text,
            style,
            *args,
            **kwargs
        )

    monkeypatch.setattr(
        transaction_module,
        "Paragraph",
        paragraph_spy
    )


# ============================================================
# ============================================================
#
# NORMAL PYTEST ACCEPTANCE TESTS
#
# ============================================================
# ============================================================


# ============================================================
# 1. OPEN REPORT PAGE
# ============================================================

def test_open_transaction_report_page(
    setup_db
):

    response = generate_report()

    assert (
        response["template"]
        == "adminTransactionReport.html"
    )

    print(
        "✅ SUCCESS: Transaction report page displayed"
    )


# ============================================================
# 2. REPORT INITIAL STATE
# ============================================================

def test_report_not_generated_initially(
    setup_db
):

    response = generate_report()

    assert (
        response["context"]
        ["generated"]
        is False
    )

    print(
        "✅ SUCCESS: Report preview hidden initially"
    )


# ============================================================
# 3. GENERATE FLAG
# ============================================================

def test_generate_flag_displays_report(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["generated"]
        is True
    )

    print(
        "✅ SUCCESS: Generate flag activates report"
    )


# ============================================================
# 4. GENERATE ALL TRANSACTIONS
# ============================================================

def test_generate_all_transactions(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 4
    )

    print(
        "✅ SUCCESS: All transactions included"
    )


# ============================================================
# 5. PAYMENT METHOD IS CARD
# ============================================================

def test_report_payment_method_is_card(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    transactions = (
        response["context"]
        ["transactions"]
    )

    for transaction in transactions:

        assert (
            transaction["payment_method"]
            == "Card"
        )

    print(
        "✅ SUCCESS: Payment method is Card"
    )


# ============================================================
# 6. REQUIRED INFORMATION
# ============================================================

def test_report_transaction_information(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    transaction = (
        response["context"]
        ["transactions"][0]
    )

    required = [

        "transaction_id",

        "company_name",

        "package",

        "payment_method",

        "amount",

        "status",

        "display_date"
    ]

    missing = []

    for field in required:

        if field not in transaction:

            missing.append(field)

    assert missing == []

    print(
        "✅ SUCCESS: Report transaction fields available"
    )


# ============================================================
# 7. COMPANY NAME
# ============================================================

def test_report_company_name(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    for transaction in (
        response["context"]
        ["transactions"]
    ):

        assert (
            transaction["company_name"]
            == COMPANY_NAME
        )

    print(
        "✅ SUCCESS: Company name displayed correctly"
    )


# ============================================================
# 8. STATUS FILTERS
# ============================================================

@pytest.mark.parametrize(
    "status, expected_count",
    [

        ("COMPLETED", 2),

        ("PENDING", 1),

        ("FAILED", 1),

        ("completed", 2),

        ("pending", 1),

        ("failed", 1)
    ]
)
def test_generate_report_status(
    setup_db,
    status,
    expected_count
):

    response = generate_report(
        status=status,
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == expected_count
    )

    print(
        f"✅ SUCCESS: {status} report filter works"
    )


# ============================================================
# 9. INVALID STATUS
# ============================================================

def test_invalid_status_returns_empty_report(
    setup_db
):

    response = generate_report(
        status="INVALID",
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 0
    )

    assert (
        response["context"]
        ["transactions"]
        == []
    )

    print(
        "✅ SUCCESS: Invalid report status handled"
    )


# ============================================================
# 10. FROM DATE
# ============================================================

def test_report_from_date(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = generate_report(

        from_date=f"{year}-03-01",

        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 2
    )

    transaction_ids = {

        transaction["transaction_id"]

        for transaction in

        response["context"]
        ["transactions"]
    }

    assert transaction_ids == {
        "TXN003",
        "TXN004"
    }

    print(
        "✅ SUCCESS: From Date filter works"
    )


# ============================================================
# 11. TO DATE
# ============================================================

def test_report_to_date(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = generate_report(

        to_date=f"{year}-02-28",

        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 2
    )

    transaction_ids = {

        transaction["transaction_id"]

        for transaction in

        response["context"]
        ["transactions"]
    }

    assert transaction_ids == {
        "TXN001",
        "TXN002"
    }

    print(
        "✅ SUCCESS: To Date filter works"
    )


# ============================================================
# 12. DATE RANGE
# ============================================================

def test_report_date_range(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = generate_report(

        from_date=f"{year}-02-01",

        to_date=f"{year}-03-31",

        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 2
    )

    transaction_ids = {

        transaction["transaction_id"]

        for transaction in

        response["context"]
        ["transactions"]
    }

    assert transaction_ids == {
        "TXN002",
        "TXN003"
    }

    print(
        "✅ SUCCESS: Date range filter works"
    )


# ============================================================
# 13. STATUS + DATE
# ============================================================

def test_report_date_and_status_together(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = generate_report(

        from_date=f"{year}-01-01",

        to_date=f"{year}-03-31",

        status="COMPLETED",

        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 1
    )

    assert (
        response["context"]
        ["transactions"][0]
        ["transaction_id"]
        == "TXN001"
    )

    print(
        "✅ SUCCESS: Date and status filters work together"
    )


# ============================================================
# 14. NO RESULTS
# ============================================================

def test_report_date_range_no_results(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = generate_report(

        from_date=f"{year}-11-01",

        to_date=f"{year}-11-30",

        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 0
    )

    assert (
        response["context"]
        ["transactions"]
        == []
    )

    print(
        "✅ SUCCESS: Empty report handled safely"
    )


# ============================================================
# 15. COMPLETED DATE PRIORITY
# ============================================================

def test_report_uses_completed_date_first(
    setup_db
):

    response = generate_report(
        status="COMPLETED",
        generate="1"
    )

    transaction = next(

        item

        for item in

        response["context"]
        ["transactions"]

        if (
            item["transaction_id"]
            == "TXN001"
        )
    )

    assert (
        transaction["display_date"]
        ==
        transaction["completed_at"]
    )

    print(
        "✅ SUCCESS: completed_at used first"
    )


# ============================================================
# 16. CREATED DATE FALLBACK
# ============================================================

def test_report_uses_created_date_as_fallback(
    setup_db
):

    response = generate_report(
        status="PENDING",
        generate="1"
    )

    transaction = (
        response["context"]
        ["transactions"][0]
    )

    assert (
        transaction["display_date"]
        ==
        transaction["created_at"]
    )

    print(
        "✅ SUCCESS: created_at used as fallback"
    )


# ============================================================
# 17. MISSING DATE
# ============================================================

def test_report_missing_transaction_date(
    monkeypatch,
    companies
):

    custom_payments = {

        "TXN999": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "package_name": "Starter",

            "payment_method": "Card",

            "amount": 49,

            "status": "COMPLETED"
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 1
    )

    transaction = (
        response["context"]
        ["transactions"][0]
    )

    assert (
        transaction["display_date"]
        is None
    )

    print(
        "✅ SUCCESS: Missing report date handled safely"
    )


# ============================================================
# 18. MISSING COMPANY
# ============================================================

def test_report_missing_company(
    monkeypatch,
    payments
):

    install_fake_db(
        monkeypatch,
        payments,
        {}
    )

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 4
    )

    for transaction in (
        response["context"]
        ["transactions"]
    ):

        assert (
            transaction["company_name"]
            == ""
        )

    print(
        "✅ SUCCESS: Missing company handled safely"
    )


# ============================================================
# 19. TOTAL TRANSACTIONS
# ============================================================

def test_report_total_transactions(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["total_transactions"]
        == 4
    )

    print(
        "✅ SUCCESS: Report total correct"
    )


# ============================================================
# 20. SUCCESSFUL COUNT
# ============================================================

def test_report_successful_count(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["successful"]
        == 2
    )

    print(
        "✅ SUCCESS: Successful count correct"
    )


# ============================================================
# 21. PENDING COUNT
# ============================================================

def test_report_pending_count(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["pending"]
        == 1
    )

    print(
        "✅ SUCCESS: Pending count correct"
    )


# ============================================================
# 22. FAILED COUNT
# ============================================================

def test_report_failed_count(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    assert (
        response["context"]
        ["failed"]
        == 1
    )

    print(
        "✅ SUCCESS: Failed count correct"
    )


# ============================================================
# 23. REVENUE
# ============================================================

def test_report_revenue_only_completed(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    expected = (
        49.00
        +
        129.00
    )

    assert (
        response["context"]
        ["total_revenue"]
        == expected
    )

    print(
        "✅ SUCCESS: Only completed payments "
        "contribute to report revenue"
    )


# ============================================================
# 24. PENDING REVENUE
# ============================================================

def test_pending_report_revenue_zero(
    setup_db
):

    response = generate_report(

        status="PENDING",

        generate="1"
    )

    assert (
        response["context"]
        ["total_revenue"]
        == 0
    )

    print(
        "✅ SUCCESS: Pending excluded from revenue"
    )


# ============================================================
# 25. FAILED REVENUE
# ============================================================

def test_failed_report_revenue_zero(
    setup_db
):

    response = generate_report(

        status="FAILED",

        generate="1"
    )

    assert (
        response["context"]
        ["total_revenue"]
        == 0
    )

    print(
        "✅ SUCCESS: Failed excluded from revenue"
    )


# ============================================================
# 26. NEWEST FIRST
# ============================================================

def test_report_sorted_newest_first(
    setup_db
):

    response = generate_report(
        generate="1"
    )

    transactions = (
        response["context"]
        ["transactions"]
    )

    assert (
        transactions[0]["transaction_id"]
        == "TXN004"
    )

    assert (
        transactions[-1]["transaction_id"]
        == "TXN001"
    )

    print(
        "✅ SUCCESS: Report sorted newest first"
    )


# ============================================================
# 27. PDF SUCCESS
# ============================================================

def test_download_pdf_success(
    setup_db
):

    response = download_report()

    assert (
        response
        is not None
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: PDF generated"
    )


# ============================================================
# 28. PDF FILENAME
# ============================================================

def test_download_pdf_filename(
    setup_db
):

    response = download_report()

    assert (
        response.filename
        .lower()
        .endswith(".pdf")
    )

    print(
        "✅ SUCCESS: PDF filename correct"
    )


# ============================================================
# 29. PDF FILE EXISTS
# ============================================================

def test_download_pdf_file_exists(
    setup_db
):

    response = download_report()

    assert os.path.exists(
        response.path
    )

    print(
        "✅ SUCCESS: PDF file exists"
    )


# ============================================================
# 30. COMPLETED PDF
# ============================================================

def test_download_completed_pdf(
    setup_db
):

    response = download_report(
        status="COMPLETED"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: Completed PDF generated"
    )


# ============================================================
# 31. PENDING PDF
# ============================================================

def test_download_pending_pdf(
    setup_db
):

    response = download_report(
        status="PENDING"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: Pending PDF generated"
    )


# ============================================================
# 32. FAILED PDF
# ============================================================

def test_download_failed_pdf(
    setup_db
):

    response = download_report(
        status="FAILED"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: Failed PDF generated"
    )


# ============================================================
# 33. PDF FROM DATE
# ============================================================

def test_download_pdf_from_date(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = download_report(
        from_date=f"{year}-02-01"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: From Date PDF generated"
    )


# ============================================================
# 34. PDF TO DATE
# ============================================================

def test_download_pdf_to_date(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = download_report(
        to_date=f"{year}-03-31"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: To Date PDF generated"
    )


# ============================================================
# 35. PDF DATE RANGE
# ============================================================

def test_download_pdf_date_range(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = download_report(

        from_date=f"{year}-01-01",

        to_date=f"{year}-03-31"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: Date range PDF generated"
    )


# ============================================================
# 36. PDF STATUS + DATE
# ============================================================

def test_download_pdf_status_and_date(
    setup_db
):

    year = datetime.now(
        timezone.utc
    ).year

    response = download_report(

        from_date=f"{year}-01-01",

        to_date=f"{year}-04-30",

        status="COMPLETED"
    )

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: Combined filtered PDF generated"
    )


# ============================================================
# 37. EMPTY PDF
# ============================================================

def test_download_pdf_when_no_transactions(
    monkeypatch,
    companies
):

    install_fake_db(
        monkeypatch,
        {},
        companies,
        patch_templates=False
    )

    response = download_report()

    assert (
        response.media_type
        == "application/pdf"
    )

    assert os.path.exists(
        response.path
    )

    print(
        "✅ SUCCESS: Empty report PDF generated"
    )


# ============================================================
# 38. PDF MISSING COMPANY
# ============================================================

def test_download_pdf_missing_company(
    monkeypatch,
    payments
):

    install_fake_db(
        monkeypatch,
        payments,
        {},
        patch_templates=False
    )

    response = download_report()

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: PDF handles missing company"
    )


# ============================================================
# 39. PDF MISSING DATE
# ============================================================

def test_download_pdf_missing_date(
    monkeypatch,
    companies
):

    custom_payments = {

        "TXN999": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "payment_method": "Card",

            "amount": 49,

            "status": "COMPLETED"
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies,
        patch_templates=False
    )

    response = download_report()

    assert (
        response.media_type
        == "application/pdf"
    )

    print(
        "✅ SUCCESS: PDF handles missing date"
    )


# ============================================================
# ============================================================
#
# BDD STEP DEFINITIONS
#
# ============================================================
# ============================================================


# ============================================================
# LOGIN
# ============================================================

@given(
    "the admin is logged into the system"
)
def admin_logged_in():

    print(
        "✅ Admin login assumed for report testing"
    )


# ============================================================
# ADMIN VIEWING REPORT PAGE
# ============================================================

@given(
    "the admin is viewing the transaction report page"
)
def viewing_report_page(
    setup_db,
    context
):

    context.response = generate_report()


# ============================================================
# OPEN REPORT PAGE - WHEN
# ============================================================

@when(
    "the admin opens the transaction report page"
)
def open_report_page(
    setup_db,
    context
):

    context.response = generate_report()


# ============================================================
# OPEN REPORT PAGE - GIVEN
# ============================================================

@given(
    "the admin opens the transaction report page"
)
def admin_opens_report_page(
    setup_db,
    context
):

    context.response = generate_report()


# ============================================================
# VERIFY PAGE
# ============================================================

@then(
    "the system should display the transaction report page"
)
def verify_report_page(
    context
):

    assert (
        context.response["template"]
        == "adminTransactionReport.html"
    )


# ============================================================
# PAGE LOADED
# ============================================================

@when(
    "the report page is loaded"
)
def report_page_loaded(
    context
):

    assert (
        context.response
        is not None
    )


# ============================================================
# FILTER OPTIONS
# ============================================================

@then(
    "the system should display the report filter options"
)
def verify_report_filters(
    context
):

    data = (
        context.response
        ["context"]
    )

    assert "from_date" in data

    assert "to_date" in data

    assert "current_status" in data


# ============================================================
# NO REPORT GENERATED
# ============================================================

@when(
    "no report has been generated"
)
def no_report_generated(
    context
):

    assert (
        context.response["context"]
        ["generated"]
        is False
    )


@then(
    "the transaction report preview should not be displayed"
)
def preview_not_displayed(
    context
):

    assert (
        context.response["context"]
        ["generated"]
        is False
    )


# ============================================================
# GENERATE WITHOUT FILTER
# ============================================================

@when(
    "the admin generates the report without filters"
)
def generate_without_filter(
    setup_db,
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the system should display the generated transaction report"
)
def verify_report_generated(
    context
):

    assert (
        context.response["context"]
        ["generated"]
        is True
    )

    assert (
        context.response["context"]
        ["total_transactions"]
        == 4
    )


# ============================================================
# ALREADY GENERATED
# ============================================================

@given(
    "the admin has generated a transaction report"
)
def report_already_generated(
    setup_db,
    context
):

    context.response = generate_report(
        generate="1"
    )


@when(
    "the transaction report preview is displayed"
)
def report_preview_displayed(
    context
):

    assert (
        context.response["context"]
        ["generated"]
        is True
    )


@then(
    "the report should display the required transaction information"
)
def verify_required_fields(
    context
):

    transaction = (
        context.response["context"]
        ["transactions"][0]
    )

    required = [

        "transaction_id",

        "company_name",

        "package",

        "payment_method",

        "amount",

        "status"
    ]

    for field in required:

        assert field in transaction


# ============================================================
# COMPLETED STATUS
# ============================================================

@when(
    "the admin generates a report with completed status"
)
def generate_completed(
    setup_db,
    context
):

    context.response = generate_report(
        status="COMPLETED",
        generate="1"
    )


@then(
    "the report should contain only completed transactions"
)
def verify_only_completed(
    context
):

    transactions = (
        context.response["context"]
        ["transactions"]
    )

    assert (
        len(transactions)
        == 2
    )

    for transaction in transactions:

        assert (
            transaction["status"]
            == "COMPLETED"
        )


# ============================================================
# PENDING STATUS
# ============================================================

@when(
    "the admin generates a report with pending status"
)
def generate_pending(
    setup_db,
    context
):

    context.response = generate_report(
        status="PENDING",
        generate="1"
    )


@then(
    "the report should contain only pending transactions"
)
def verify_only_pending(
    context
):

    transactions = (
        context.response["context"]
        ["transactions"]
    )

    assert (
        len(transactions)
        == 1
    )

    for transaction in transactions:

        assert (
            transaction["status"]
            == "PENDING"
        )


# ============================================================
# FAILED STATUS
# ============================================================

@when(
    "the admin generates a report with failed status"
)
def generate_failed(
    setup_db,
    context
):

    context.response = generate_report(
        status="FAILED",
        generate="1"
    )


@then(
    "the report should contain only failed transactions"
)
def verify_only_failed(
    context
):

    transactions = (
        context.response["context"]
        ["transactions"]
    )

    assert (
        len(transactions)
        == 1
    )

    for transaction in transactions:

        assert (
            transaction["status"]
            == "FAILED"
        )


# ============================================================
# LOWERCASE STATUS
# ============================================================

@when(
    "the admin generates a report using lowercase completed status"
)
def lowercase_completed(
    setup_db,
    context
):

    context.response = generate_report(
        status="completed",
        generate="1"
    )


@then(
    "the report status filter should be case insensitive"
)
def verify_case_insensitive_status(
    context
):

    transactions = (
        context.response["context"]
        ["transactions"]
    )

    assert (
        len(transactions)
        == 2
    )

    for transaction in transactions:

        assert (
            transaction["status"]
            == "COMPLETED"
        )


# ============================================================
# COMMON DIFFERENT DATES
# ============================================================

@given(
    "transactions exist on different dates"
)
def different_transaction_dates(
    setup_db
):

    pass


# ============================================================
# FROM DATE BDD
# ============================================================

@when(
    "the admin generates a report using a from date"
)
def report_using_from_date(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = generate_report(
        from_date=f"{year}-03-01",
        generate="1"
    )


@then(
    "transactions before the from date should be excluded"
)
def verify_before_from_excluded(
    context
):

    ids = {

        transaction["transaction_id"]

        for transaction in

        context.response["context"]
        ["transactions"]
    }

    assert ids == {
        "TXN003",
        "TXN004"
    }


# ============================================================
# TO DATE
# ============================================================

@when(
    "the admin generates a report using a to date"
)
def report_using_to_date(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = generate_report(
        to_date=f"{year}-02-28",
        generate="1"
    )


@then(
    "transactions after the to date should be excluded"
)
def verify_after_to_excluded(
    context
):

    ids = {

        transaction["transaction_id"]

        for transaction in

        context.response["context"]
        ["transactions"]
    }

    assert ids == {
        "TXN001",
        "TXN002"
    }


# ============================================================
# DATE RANGE
# ============================================================

@given(
    "transactions exist inside and outside a selected date range"
)
def transactions_inside_outside_range(
    setup_db
):

    pass


@when(
    "the admin generates a report using the date range"
)
def generate_date_range(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = generate_report(

        from_date=f"{year}-02-01",

        to_date=f"{year}-03-31",

        generate="1"
    )


@then(
    "only transactions within the selected date range should be included"
)
def verify_range(
    context
):

    ids = {

        transaction["transaction_id"]

        for transaction in

        context.response["context"]
        ["transactions"]
    }

    assert ids == {
        "TXN002",
        "TXN003"
    }


# ============================================================
# STATUS + DATE RANGE
# ============================================================

@given(
    "transactions have different dates and statuses"
)
def different_dates_statuses(
    setup_db
):

    pass


@when(
    "the admin generates a report using status and date filters"
)
def generate_status_and_date(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = generate_report(

        from_date=f"{year}-01-01",

        to_date=f"{year}-03-31",

        status="COMPLETED",

        generate="1"
    )


@then(
    "only transactions matching all selected report criteria should be included"
)
def verify_status_date_combination(
    context
):

    transactions = (
        context.response["context"]
        ["transactions"]
    )

    assert (
        len(transactions)
        == 1
    )

    assert (
        transactions[0]
        ["transaction_id"]
        == "TXN001"
    )

    assert (
        transactions[0]
        ["status"]
        == "COMPLETED"
    )


# ============================================================
# NO MATCHING REPORT
# ============================================================

@given(
    "no transactions match the report criteria"
)
def no_matching_report_transactions(
    setup_db,
    context
):

    context.expected = "no_results"


@when(
    "the admin generates the transaction report"
)
def generate_empty_report(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = generate_report(

        from_date=f"{year}-11-01",

        to_date=f"{year}-11-30",

        generate="1"
    )


@then(
    "the report should display no transactions found"
)
def verify_no_transactions_report(
    context
):

    assert (
        context.response["context"]
        ["total_transactions"]
        == 0
    )

    assert (
        context.response["context"]
        ["transactions"]
        == []
    )


# ============================================================
# INVALID STATUS BDD
# ============================================================

@when(
    "an invalid report status is supplied"
)
def invalid_report_status(
    setup_db,
    context
):

    context.response = generate_report(
        status="INVALID",
        generate="1"
    )


@then(
    "the system should handle the invalid report status without crashing"
)
def verify_invalid_report_status(
    context
):

    assert (
        context.response
        is not None
    )

    assert (
        context.response["context"]
        ["total_transactions"]
        == 0
    )


# ============================================================
# COMPLETED DATE
# ============================================================

@given(
    "a report transaction contains a completed date"
)
def report_transaction_completed_date(
    monkeypatch,
    companies,
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "payment_method": "Card",

            "amount": 49,

            "status": "COMPLETED",

            "created_at": datetime(
                year,
                1,
                1,
                tzinfo=timezone.utc
            ),

            "completed_at": datetime(
                year,
                1,
                2,
                tzinfo=timezone.utc
            )
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@when(
    "the report determines the transaction date"
)
def determine_report_transaction_date(
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the completed date should be used"
)
def completed_date_used(
    context
):

    transaction = (
        context.response["context"]
        ["transactions"][0]
    )

    assert (
        transaction["display_date"]
        ==
        transaction["completed_at"]
    )


# ============================================================
# CREATED DATE FALLBACK
# ============================================================

@given(
    "a report transaction has no completed date but contains a created date"
)
def report_transaction_created_only(
    monkeypatch,
    companies,
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Business",

            "payment_method": "Card",

            "amount": 129,

            "status": "PENDING",

            "created_at": datetime(
                year,
                2,
                1,
                tzinfo=timezone.utc
            )
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@then(
    "the created date should be used"
)
def created_date_used(
    context
):

    transaction = (
        context.response["context"]
        ["transactions"][0]
    )

    assert (
        transaction["display_date"]
        ==
        transaction["created_at"]
    )


# ============================================================
# NO TRANSACTION DATE
# ============================================================

@given(
    "a report transaction has no completed date or created date"
)
def report_transaction_no_date(
    monkeypatch,
    companies,
    context
):

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "payment_method": "Card",

            "amount": 49,

            "status": "COMPLETED"
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@when(
    "the report is generated"
)
def generate_report_bdd(
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the missing report transaction date should be handled safely"
)
def verify_missing_report_date(
    context
):

    transaction = (
        context.response["context"]
        ["transactions"][0]
    )

    assert (
        transaction["display_date"]
        is None
    )


# ============================================================
# VALID COMPANY
# ============================================================

@given(
    "a report transaction contains a valid company ID"
)
def report_valid_company(
    setup_db
):

    pass


@when(
    "the transaction report is generated"
)
def transaction_report_generated(
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the corresponding company name should be included"
)
def verify_report_company(
    context
):

    for transaction in (
        context.response["context"]
        ["transactions"]
    ):

        assert (
            transaction["company_name"]
            == COMPANY_NAME
        )


# ============================================================
# MISSING COMPANY REPORT
# ============================================================

@given(
    "a report transaction references a company that does not exist"
)
def report_missing_company(
    monkeypatch,
    payments
):

    install_fake_db(
        monkeypatch,
        payments,
        {}
    )


@then(
    "the system should handle the missing report company safely"
)
def verify_missing_report_company(
    context
):

    for transaction in (
        context.response["context"]
        ["transactions"]
    ):

        assert (
            transaction["company_name"]
            == ""
        )


# ============================================================
# COMPLETED REVENUE
# ============================================================

@given(
    "a completed transaction exists in the report"
)
def completed_transaction_report(
    monkeypatch,
    companies
):

    year = datetime.now(
        timezone.utc
    ).year

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "payment_method": "Card",

            "amount": 100,

            "status": "COMPLETED",

            "completed_at": datetime(
                year,
                1,
                1,
                tzinfo=timezone.utc
            )
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@when(
    "report summary values are calculated"
)
def calculate_report_summary_values(
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the completed transaction amount should contribute to report revenue"
)
def verify_completed_report_revenue(
    context
):

    assert (
        context.response["context"]
        ["total_revenue"]
        == 100
    )


# ============================================================
# PENDING REVENUE
# ============================================================

@given(
    "a pending transaction exists in the report"
)
def pending_transaction_report(
    monkeypatch,
    companies
):

    year = datetime.now(
        timezone.utc
    ).year

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Business",

            "payment_method": "Card",

            "amount": 129,

            "status": "PENDING",

            "created_at": datetime(
                year,
                1,
                1,
                tzinfo=timezone.utc
            )
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@then(
    "the pending transaction amount should not contribute to report revenue"
)
def verify_pending_report_revenue(
    context
):

    assert (
        context.response["context"]
        ["total_revenue"]
        == 0
    )


# ============================================================
# FAILED REVENUE
# ============================================================

@given(
    "a failed transaction exists in the report"
)
def failed_transaction_report(
    monkeypatch,
    companies
):

    year = datetime.now(
        timezone.utc
    ).year

    custom_payments = {

        "TXN001": {

            "company_id": COMPANY_ID,

            "package": "Enterprise",

            "payment_method": "Card",

            "amount": 249,

            "status": "FAILED",

            "created_at": datetime(
                year,
                1,
                1,
                tzinfo=timezone.utc
            )
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies
    )


@then(
    "the failed transaction amount should not contribute to report revenue"
)
def verify_failed_report_revenue(
    context
):

    assert (
        context.response["context"]
        ["total_revenue"]
        == 0
    )


# ============================================================
# COUNT COMPLETED
# ============================================================

@given(
    "completed transactions match the report criteria"
)
def matching_completed_transactions(
    setup_db,
    context
):

    context.expected = "COMPLETED"


# ============================================================
# COUNT PENDING
# ============================================================

@given(
    "pending transactions match the report criteria"
)
def matching_pending_transactions(
    setup_db,
    context
):

    context.expected = "PENDING"


# ============================================================
# COUNT FAILED
# ============================================================

@given(
    "failed transactions match the report criteria"
)
def matching_failed_transactions(
    setup_db,
    context
):

    context.expected = "FAILED"


@when(
    "the report summary is calculated"
)
def report_summary_calculated(
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the successful transaction count should be correct"
)
def successful_count_correct(
    context
):

    assert (
        context.response["context"]
        ["successful"]
        == 2
    )


@then(
    "the pending transaction count should be correct"
)
def pending_count_correct(
    context
):

    assert (
        context.response["context"]
        ["pending"]
        == 1
    )


@then(
    "the failed transaction count should be correct"
)
def failed_count_correct(
    context
):

    assert (
        context.response["context"]
        ["failed"]
        == 1
    )


# ============================================================
# GENERATE FLAG
# ============================================================

@when(
    "the report generate parameter is enabled"
)
def enable_generate_parameter(
    setup_db,
    context
):

    context.response = generate_report(
        generate="1"
    )


@then(
    "the transaction report preview should be displayed"
)
def report_preview_should_display(
    context
):

    assert (
        context.response["context"]
        ["generated"]
        is True
    )


# ============================================================
# PDF DOWNLOAD
# ============================================================

@when(
    "the admin downloads the transaction report"
)
def admin_download_report(
    context
):

    context.response = download_report()


@then(
    "the system should return a PDF file"
)
def system_returns_pdf(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )

    assert (
        context.response.filename
        .lower()
        .endswith(".pdf")
    )


# ============================================================
# GIVEN DOWNLOAD
# ============================================================

@given(
    "the admin downloads the transaction report"
)
def admin_already_downloads_report(
    setup_db,
    context
):

    context.response = download_report()


@when(
    "the report download response is returned"
)
def report_download_returned(
    context
):

    assert (
        context.response
        is not None
    )


@then(
    "the response content type should be application pdf"
)
def pdf_content_type(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )


@then(
    "the downloaded report filename should end with pdf"
)
def pdf_filename(
    context
):

    assert (
        context.response.filename
        .lower()
        .endswith(".pdf")
    )


# ============================================================
# DIFFERENT PAYMENT STATUSES
# ============================================================

@given(
    "transactions have different payment statuses"
)
def transactions_different_payment_statuses(
    setup_db
):

    pass


@when(
    "the admin downloads a report filtered by completed status"
)
def download_completed_status(
    context
):

    context.response = download_report(
        status="COMPLETED"
    )


@then(
    "the PDF report should be generated successfully"
)
def pdf_generated_successfully(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )


# ============================================================
# PDF FROM DATE
# ============================================================

@when(
    "the admin downloads a report using a from date"
)
def pdf_using_from_date(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = download_report(
        from_date=f"{year}-02-01"
    )


@then(
    "the filtered PDF report should be generated successfully"
)
def filtered_pdf_generated(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )


# ============================================================
# PDF TO DATE
# ============================================================

@when(
    "the admin downloads a report using a to date"
)
def pdf_using_to_date(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = download_report(
        to_date=f"{year}-03-31"
    )


# ============================================================
# PDF DATE RANGE
# ============================================================

@when(
    "the admin downloads a report using a date range"
)
def pdf_using_date_range(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = download_report(

        from_date=f"{year}-02-01",

        to_date=f"{year}-03-31"
    )


@then(
    "the date filtered PDF report should be generated successfully"
)
def date_filtered_pdf_generated(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )


# ============================================================
# PDF STATUS + DATE
# ============================================================

@given(
    "transactions contain different dates and statuses"
)
def transactions_different_dates_statuses(
    setup_db
):

    pass


@when(
    "the admin downloads a report using status and date filters"
)
def download_status_date_pdf(
    context
):

    year = datetime.now(
        timezone.utc
    ).year

    context.response = download_report(

        from_date=f"{year}-01-01",

        to_date=f"{year}-04-30",

        status="COMPLETED"
    )


@then(
    "the combined filtered PDF report should be generated successfully"
)
def combined_pdf_success(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )


# ============================================================
# NO MATCHING PDF
# ============================================================

@given(
    "no transactions match the PDF report criteria"
)
def no_matching_pdf_transactions(
    setup_db,
    context
):

    context.expected = "no_pdf_results"


@when(
    "the admin downloads the transaction report"
)
def download_transaction_report_step(
    context
):

    if (
        context.expected
        == "no_pdf_results"
    ):

        context.response = download_report(
            from_date="2000-01-01",
            to_date="2000-01-02"
        )

    else:

        context.response = download_report()


@then(
    "the system should still generate a valid PDF report"
)
def valid_empty_pdf(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )

    assert os.path.exists(
        context.response.path
    )


# ============================================================
# PDF MISSING COMPANY
# ============================================================

@given(
    "a PDF transaction references a company that does not exist"
)
def pdf_missing_company(
    monkeypatch,
    payments,
    context
):

    install_fake_db(
        monkeypatch,
        payments,
        {},
        patch_templates=False
    )

    capture_pdf_paragraphs(
        monkeypatch,
        context
    )


@when(
    "the PDF transaction report is generated"
)
def generate_pdf_transaction_report(
    context
):

    context.response = download_report()


@then(
    "the missing company should be represented safely in the PDF"
)
def verify_missing_company_pdf(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )

    assert (
        "-"
        in context.captured_pdf_text
    )


# ============================================================
# PDF MISSING DATE
# ============================================================

@given(
    "a PDF transaction does not contain a payment date"
)
def pdf_transaction_no_date(
    monkeypatch,
    companies,
    context
):

    custom_payments = {

        "TXN999": {

            "company_id": COMPANY_ID,

            "package": "Starter",

            "payment_method": "Card",

            "amount": 49,

            "status": "COMPLETED"
        }
    }

    install_fake_db(
        monkeypatch,
        custom_payments,
        companies,
        patch_templates=False
    )

    capture_pdf_paragraphs(
        monkeypatch,
        context
    )


@then(
    "the missing payment date should be represented with a dash"
)
def verify_missing_date_dash(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )

    assert (
        "-"
        in context.captured_pdf_text
    )


# ============================================================
# PDF REVENUE
# ============================================================

@given(
    "completed and unsuccessful transactions exist"
)
def completed_unsuccessful_exist(
    setup_db,
    monkeypatch,
    context
):

    capture_pdf_paragraphs(
        monkeypatch,
        context
    )


@then(
    "only completed transaction amounts should contribute to PDF report revenue"
)
def verify_pdf_completed_revenue(
    context
):

    expected_revenue = (
        49.00
        +
        129.00
    )

    expected_text = (
        f"RM {expected_revenue:,.2f}"
    )

    assert (
        expected_text
        in context.captured_pdf_text
    )


# ============================================================
# EMPTY TRANSACTION LIST PDF
# ============================================================

@given(
    "no transactions exist"
)
def no_transactions_exist(
    monkeypatch,
    companies,
    context
):

    install_fake_db(
        monkeypatch,
        {},
        companies,
        patch_templates=False
    )

    capture_pdf_paragraphs(
        monkeypatch,
        context
    )


@then(
    "a valid PDF containing the empty report message should be generated"
)
def verify_empty_pdf_message(
    context
):

    assert (
        context.response.media_type
        == "application/pdf"
    )

    expected_message = (
        "No transactions found for "
        "the selected report criteria."
    )

    assert (
        expected_message
        in context.captured_pdf_text
    )