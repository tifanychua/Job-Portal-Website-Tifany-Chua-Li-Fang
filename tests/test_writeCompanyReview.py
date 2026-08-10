import asyncio
import importlib
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import HTTPException
from pytest_bdd import given, scenarios, then, when

# ============================================================
# LOAD ACTUAL ROUTE WITHOUT REAL FIREBASE CONNECTION
# ============================================================


def load_review_module():
    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def write_company_review(" in text and "def submit_company_review(" in text:
            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client
            firestore_module.client = lambda: None

            try:
                return importlib.import_module("job_portal_web.backend.routes." + path.stem)
            finally:
                firestore_module.client = original_client

    raise ImportError("Could not find the company review route file.")


review_module = load_review_module()

scenarios("features/writeCompanyReview.feature")


APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"
COMPANY_ID = "company001"


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


class FakeCollection:

    def __init__(
        self,
        documents=None,
    ):
        self.documents = documents.copy() if documents else {}

        self.added = []

    def document(
        self,
        document_id,
    ):
        return FakeDocument(
            self,
            document_id,
        )

    def add(
        self,
        data,
    ):
        self.added.append(data.copy())

        document_id = f"REVIEW{len(self.added):03d}"

        self.documents[document_id] = data.copy()

        return (
            FakeDocument(
                self,
                document_id,
            ),
            None,
        )


class FakeDB:

    def __init__(
        self,
        companies=None,
        applicants=None,
        reviews=None,
    ):
        self.collections = {
            "company": FakeCollection(companies or {}),
            "job_seeker": FakeCollection(applicants or {}),
            "company_review": FakeCollection(reviews or {}),
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
# FAKE REQUEST
# ============================================================


class FakeRequest:

    def __init__(
        self,
        user_type="job_seeker",
        applicant_id=APPLICANT_ID,
    ):
        self.session = {
            "user_type": user_type,
        }

        if applicant_id is not None:
            self.session["applicant_id"] = applicant_id


# ============================================================
# BDD CONTEXT
# ============================================================


class Context:

    def __init__(self):
        self.response = None
        self.error = None
        self.db = None
        self.request = FakeRequest()


@pytest.fixture
def context():
    return Context()


# ============================================================
# DEFAULT DATA
# ============================================================


@pytest.fixture
def companies():
    return {
        COMPANY_ID: {
            "companyName": "ABC Technology Sdn Bhd",
            "city": "Kuala Lumpur",
            "state": "Kuala Lumpur",
            "status": "Active",
        }
    }


@pytest.fixture
def applicants():
    return {
        APPLICANT_ID: {
            "uid": APPLICANT_ID,
            "company_name": "ABC Technology Sdn. Bhd.",
            "email": "hr@abctech.com",
        }
    }


# ============================================================
# INSTALL FAKE DB
# ============================================================


def install_fake_db(
    monkeypatch,
    companies,
    applicants,
    reviews=None,
):
    fake_db = FakeDB(
        companies=companies,
        applicants=applicants,
        reviews=reviews or {},
    )

    monkeypatch.setattr(
        review_module,
        "db",
        fake_db,
    )

    monkeypatch.setattr(
        review_module,
        "templates",
        FakeTemplates(),
    )

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    companies,
    applicants,
):
    return install_fake_db(
        monkeypatch,
        companies,
        applicants,
    )


# ============================================================
# HELPERS
# ============================================================


def open_review_page(
    request=None,
    company_id=COMPANY_ID,
):
    return asyncio.run(
        review_module.write_company_review(
            request=(request or FakeRequest()),
            company_id=company_id,
        )
    )


def submit_review(
    request=None,
    company_id=COMPANY_ID,
    overall_rating=5,
    job_title="Software Engineer",
    department="IT",
    employment_type="Full-time",
    location="Kuala Lumpur",
    start_date="2024-01-01",
    end_date="",
    still_working="on",
    recommend="Yes",
    pros="Good working environment",
    cons="Busy during deadlines",
    review_title="Good company to grow",
    additional_comments="Supportive team",
    work_environment=5,
    management=4,
    career_growth=5,
    work_life_balance=4,
    benefits=4,
    company_culture=5,
    learning_opportunities=5,
):
    return asyncio.run(
        review_module.submit_company_review(
            request=(request or FakeRequest()),
            company_id=company_id,
            overall_rating=overall_rating,
            job_title=job_title,
            department=department,
            employment_type=employment_type,
            location=location,
            start_date=start_date,
            end_date=end_date,
            still_working=still_working,
            recommend=recommend,
            pros=pros,
            cons=cons,
            review_title=review_title,
            additional_comments=additional_comments,
            work_environment=work_environment,
            management=management,
            career_growth=career_growth,
            work_life_balance=work_life_balance,
            benefits=benefits,
            company_culture=company_culture,
            learning_opportunities=learning_opportunities,
        )
    )


def latest_review(
    context,
):
    return context.db.collection("company_review").added[-1]


def disable_pytest_login_bypass(
    monkeypatch,
):
    original_getenv = review_module.os.getenv

    def fake_getenv(
        key,
        default=None,
    ):
        if key == "PYTEST_CURRENT_TEST":
            return None

        return original_getenv(
            key,
            default,
        )

    monkeypatch.setattr(
        review_module.os,
        "getenv",
        fake_getenv,
    )


# ============================================================
# DIRECT PYTEST TESTS
# ============================================================


def test_write_review_page(
    setup_db,
):
    response = open_review_page()

    assert response["template"] == "writeCompanyReview.html"

    assert response["context"]["company"]["id"] == COMPANY_ID

    assert response["context"]["applicant_id"] == APPLICANT_ID


def test_submit_complete_review(
    setup_db,
):
    response = submit_review()

    added = setup_db.collection("company_review").added

    assert len(added) == 1

    review = added[0]

    assert review["company_id"] == COMPANY_ID

    assert review["applicant_id"] == APPLICANT_ID

    assert review["status"] == "Active"
    assert review["overall_rating"] == 5
    assert review["still_working"] is True

    assert response.status_code == 303

    assert response.headers["location"] == f"/company/{COMPANY_ID}/reviews"


def test_former_employee(
    setup_db,
):
    submit_review(
        still_working=None,
        end_date="2025-12-31",
    )

    review = setup_db.collection("company_review").added[0]

    assert review["still_working"] is False

    assert review["end_date"] == "2025-12-31"


def test_optional_fields_empty(
    setup_db,
):
    submit_review(
        end_date="",
        pros="",
        cons="",
        additional_comments="",
    )

    review = setup_db.collection("company_review").added[0]

    assert review["end_date"] == ""
    assert review["pros"] == ""
    assert review["cons"] == ""
    assert review["additional_comments"] == ""


def test_company_not_found_on_open(
    monkeypatch,
    applicants,
):
    install_fake_db(
        monkeypatch,
        {},
        applicants,
    )

    with pytest.raises(HTTPException) as exc:
        open_review_page()

    assert exc.value.status_code == 404
    assert exc.value.detail == "Company not found"


def test_company_not_found_on_submit(
    monkeypatch,
    applicants,
):
    install_fake_db(
        monkeypatch,
        {},
        applicants,
    )

    with pytest.raises(HTTPException) as exc:
        submit_review()

    assert exc.value.status_code == 404


def test_non_job_seeker_access_denied(
    monkeypatch,
    setup_db,
):
    disable_pytest_login_bypass(monkeypatch)

    request = FakeRequest(
        user_type="employer",
        applicant_id=None,
    )

    with pytest.raises(HTTPException) as exc:
        open_review_page(request=request)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Access denied"


def test_missing_applicant_id_requires_login(
    monkeypatch,
    setup_db,
):
    disable_pytest_login_bypass(monkeypatch)

    request = FakeRequest(
        user_type="job_seeker",
        applicant_id=None,
    )

    with pytest.raises(HTTPException) as exc:
        open_review_page(request=request)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Please login."


# ============================================================
# BDD GIVEN
# ============================================================


@given("a job seeker is logged in")
def job_seeker_logged_in(
    context,
):

    context.request = FakeRequest()


@given("the company exists")
def company_exists(
    monkeypatch,
    companies,
    applicants,
    context,
):

    if context.db is None:

        context.db = install_fake_db(
            monkeypatch,
            companies,
            applicants,
        )


@given("the applicant profile exists")
def applicant_exists(
    monkeypatch,
    companies,
    applicants,
    context,
):

    if context.db is None:

        context.db = install_fake_db(
            monkeypatch,
            companies,
            applicants,
        )


@given("the applicant profile does not exist")
def applicant_missing(
    monkeypatch,
    companies,
    context,
):

    context.db = install_fake_db(
        monkeypatch,
        companies,
        {},
    )


@given("the requested company does not exist")
def company_missing(
    monkeypatch,
    applicants,
    context,
):

    context.db = install_fake_db(
        monkeypatch,
        {},
        applicants,
    )


@given("the user is not a job seeker")
def non_job_seeker(
    monkeypatch,
    setup_db,
    context,
):
    disable_pytest_login_bypass(monkeypatch)

    if context.db is None:
        context.db = setup_db

    context.request = FakeRequest(
        user_type="employer",
        applicant_id=None,
    )


@given("the user session is job seeker without applicant ID")
def job_seeker_without_id(
    monkeypatch,
    setup_db,
    context,
):
    disable_pytest_login_bypass(monkeypatch)

    if context.db is None:
        context.db = setup_db

    context.request = FakeRequest(
        user_type="job_seeker",
        applicant_id=None,
    )


# ============================================================
# BDD WHEN
# ============================================================


@when("the job seeker opens the write company review page")
def open_page(
    context,
):
    context.response = open_review_page(request=context.request)


@when("the job seeker opens the write company review page expecting an error")
def open_page_error(
    context,
):
    try:
        context.response = open_review_page(request=context.request)

    except HTTPException as exc:
        context.error = exc


@when("the user tries to open the write company review page")
def unauthorized_open(
    context,
):
    try:
        context.response = open_review_page(request=context.request)

    except HTTPException as exc:
        context.error = exc


@when("the job seeker submits a complete company review")
def submit_complete(
    context,
):
    context.response = submit_review(request=context.request)


@when("the job seeker submits a review as a current employee")
def submit_current_employee(
    context,
):
    context.response = submit_review(
        request=context.request,
        still_working="on",
        end_date="",
    )


@when("the job seeker submits a review as a former employee")
def submit_former_employee(
    context,
):
    context.response = submit_review(
        request=context.request,
        still_working=None,
        end_date="2025-12-31",
    )


@when("the job seeker submits a review with empty optional fields")
def submit_optional_empty(
    context,
):
    context.response = submit_review(
        request=context.request,
        end_date="",
        pros="",
        cons="",
        additional_comments="",
    )


@when("the job seeker submits a company review expecting an error")
def submit_company_error(
    context,
):
    try:
        context.response = submit_review(request=context.request)

    except HTTPException as exc:
        context.error = exc


# ============================================================
# BDD THEN
# ============================================================


@then("the write company review page should be displayed")
def review_page_displayed(
    context,
):
    assert context.response["template"] == "writeCompanyReview.html"


@then("the company information should be available")
def company_info_available(
    context,
):
    company = context.response["context"]["company"]

    assert company["id"] == COMPANY_ID

    assert company["companyName"] == "ABC Technology Sdn Bhd"


@then("the applicant information should be available")
def applicant_info_available(
    context,
):
    user = context.response["context"]["user"]

    assert user is not None

    assert user["company_name"] == "ABC Technology Sdn. Bhd."


@then("the review page should still be displayed safely")
def missing_user_safe(
    context,
):
    assert context.response["template"] == "writeCompanyReview.html"

    assert context.response["context"]["user"] is None


@then("the company review should be saved")
def review_saved(
    context,
):
    assert len(context.db.collection("company_review").added) == 1


@then("the saved review should contain the correct company and applicant IDs")
def correct_ids(
    context,
):
    review = latest_review(context)

    assert review["company_id"] == COMPANY_ID

    assert review["applicant_id"] == APPLICANT_ID


@then("the review status should be active")
def active_status(
    context,
):
    assert latest_review(context)["status"] == "Active"


@then("the job seeker should be redirected to the company reviews page")
def redirected_to_reviews(
    context,
):
    assert context.response.status_code == 303

    assert context.response.headers["location"] == f"/company/{COMPANY_ID}/reviews"


@then("the overall rating should be saved correctly")
def overall_rating_saved(
    context,
):
    assert latest_review(context)["overall_rating"] == 5


@then("the employment information should be saved correctly")
def employment_saved(
    context,
):
    review = latest_review(context)

    assert review["job_title"] == "Software Engineer"

    assert review["department"] == "IT"

    assert review["employment_type"] == "Full-time"

    assert review["location"] == "Kuala Lumpur"

    assert review["start_date"] == "2024-01-01"


@then("the review title recommendation pros cons and comments should be saved correctly")
def review_content_saved(
    context,
):
    review = latest_review(context)

    assert review["recommend"] == "Yes"

    assert review["pros"] == "Good working environment"

    assert review["cons"] == "Busy during deadlines"

    assert review["review_title"] == "Good company to grow"

    assert review["additional_comments"] == "Supportive team"


@then("all category ratings should be saved correctly")
def category_ratings_saved(
    context,
):
    review = latest_review(context)

    assert review["work_environment"] == 5
    assert review["management"] == 4
    assert review["career_growth"] == 5
    assert review["work_life_balance"] == 4
    assert review["benefits"] == 4
    assert review["company_culture"] == 5

    assert review["learning_opportunities"] == 5


@then("still working should be true")
def still_working_true(
    context,
):
    assert latest_review(context)["still_working"] is True


@then("still working should be false")
def still_working_false(
    context,
):
    review = latest_review(context)

    assert review["still_working"] is False

    assert review["end_date"] == "2025-12-31"


@then("the optional review fields should be saved as empty values")
def optional_fields_empty(
    context,
):
    review = latest_review(context)

    assert review["end_date"] == ""
    assert review["pros"] == ""
    assert review["cons"] == ""

    assert review["additional_comments"] == ""


@then("the review creation time should be recorded")
def creation_time_recorded(
    context,
):
    review = latest_review(context)

    assert isinstance(
        review["created_at"],
        datetime,
    )


@then("company not found should be returned")
def company_not_found(
    context,
):
    assert context.error is not None

    assert context.error.status_code == 404

    assert context.error.detail == "Company not found"


@then("access denied should be returned")
def access_denied(
    context,
):
    assert context.error is not None

    assert context.error.status_code == 403

    assert context.error.detail == "Access denied"


@then("login required should be returned")
def login_required(
    context,
):
    assert context.error is not None

    assert context.error.status_code == 401

    assert context.error.detail == "Please login."
