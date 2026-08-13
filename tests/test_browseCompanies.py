import asyncio
from unittest.mock import patch

import pytest
from pytest_bdd import given, scenarios, then, when

# ============================================================
# IMPORT ROUTE WITHOUT CONNECTING TO REAL FIREBASE
# ============================================================

with patch("firebase_admin.firestore.client", return_value=None):
    from job_portal_web.backend.routes import companyBrowse as company_module


# ============================================================
# CONSTANTS
# ============================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios("features/browseCompanies.feature")


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


class FakeQuery:
    def __init__(self, documents):
        self.documents = documents
        self.filters = []

    def where(self, field, operator, value):
        self.filters.append((field, operator, value))

        return self

    def stream(self):

        results = []

        for document_id, data in self.documents.items():
            matched = True

            for field, operator, expected in self.filters:
                if operator != "==":
                    continue

                if data.get(field) != expected:
                    matched = False
                    break

            if matched:
                results.append(FakeDocumentSnapshot(document_id, data, exists=True))

        return results


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or {}

    def document(self, document_id):
        return FakeDocumentReference(self, document_id)

    def where(self, field, operator, value):
        query = FakeQuery(self.documents)

        return query.where(field, operator, value)

    def stream(self):

        return [
            FakeDocumentSnapshot(document_id, data, exists=True)
            for document_id, data in self.documents.items()
        ]


class FakeDB:
    def __init__(self, applicants=None, companies=None, jobs=None, reviews=None):

        self.collections = {
            "job_seeker": FakeCollection(applicants or {}),
            "company": FakeCollection(companies or {}),
            "job_list": FakeCollection(jobs or {}),
            "company_review": FakeCollection(reviews or {}),
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

        self.session = {"user_type": "job_seeker", "applicant_id": APPLICANT_ID}


# ============================================================
# TEST CONTEXT
# ============================================================


class Context:
    def __init__(self):
        self.response = None


@pytest.fixture
def context():
    return Context()


# ============================================================
# APPLICANT
# ============================================================


@pytest.fixture
def applicants():

    return {
        APPLICANT_ID: {
            "uid": APPLICANT_ID,
            "full_name": "Test User",
            "position": "Software Engineer",
            "profileImage": "/images/user.png",
        }
    }


# ============================================================
# COMPANIES
# ============================================================


@pytest.fixture
def companies():

    return {
        "COMPANY001": {
            "companyName": "ABC Technology Sdn Bhd",
            "status": "Active",
            "city": "Kuala Lumpur",
            "state": "Kuala Lumpur",
            "industry_id": "Information Technology",
            "logo": "/images/abc.png",
        },
        "COMPANY002": {
            "companyName": "XYZ Solutions",
            "status": "Active",
            "city": "Petaling Jaya",
            "state": "Selangor",
            "industry_id": "Software Development",
            "logo": "/images/xyz.png",
        },
        "COMPANY003": {
            "companyName": "Inactive Company",
            "status": "Inactive",
            "city": "Johor Bahru",
            "state": "Johor",
            "industry_id": "Finance",
            "logo": "",
        },
    }


# ============================================================
# JOBS
# ============================================================


@pytest.fixture
def jobs():

    return {
        "JOB001": {
            "company_id": "COMPANY001",
            "status": "Active",
            "job_title": "Software Engineer",
        },
        "JOB002": {
            "company_id": "COMPANY001",
            "status": "Active",
            "job_title": "Backend Developer",
        },
        "JOB003": {
            "company_id": "COMPANY001",
            "status": "Closed",
            "job_title": "Old Developer Job",
        },
        "JOB004": {"company_id": "COMPANY002", "status": "Active", "job_title": "System Analyst"},
    }


# ============================================================
# REVIEWS
# ============================================================


@pytest.fixture
def reviews():

    return {
        "REVIEW001": {"company_id": "COMPANY001", "overall_rating": 4.0},
        "REVIEW002": {"company_id": "COMPANY001", "overall_rating": 5.0},
        "REVIEW003": {"company_id": "COMPANY002", "overall_rating": 3.5},
    }


# ============================================================
# INSTALL FAKE DATABASE
# ============================================================


def install_fake_db(monkeypatch, applicants, companies, jobs, reviews):

    fake_db = FakeDB(applicants=applicants, companies=companies, jobs=jobs, reviews=reviews)

    monkeypatch.setattr(company_module, "db", fake_db)

    monkeypatch.setattr(company_module, "templates", FakeTemplates())

    return fake_db


@pytest.fixture
def setup_db(monkeypatch, applicants, companies, jobs, reviews):

    return install_fake_db(monkeypatch, applicants, companies, jobs, reviews)


# ============================================================
# HELPER
# ============================================================


def browse():

    request = FakeRequest()

    return asyncio.run(company_module.browse_companies(request=request, keyword="", page=1))


# ============================================================
# GIVEN
# ============================================================


@given("the job seeker is logged into the system")
def job_seeker_logged_in(setup_db):
    pass


@given("active companies exist")
def active_companies_exist(setup_db):
    pass


@given("active and inactive companies exist")
def active_and_inactive_exist(setup_db):
    pass


@given("an active company contains a logo")
def active_company_has_logo(setup_db):
    pass


@given("an active company does not contain a logo")
def active_company_no_logo(monkeypatch, applicants, jobs, reviews):

    companies = {
        "COMPANY001": {
            "companyName": "ABC Technology Sdn Bhd",
            "status": "Active",
            "city": "Kuala Lumpur",
            "state": "Kuala Lumpur",
            "industry_id": "Information Technology",
            "logo": "",
        }
    }

    install_fake_db(monkeypatch, applicants, companies, jobs, reviews)


@given("an active company has available jobs")
def active_company_has_jobs(setup_db):
    pass


@given("an active company has no available jobs")
def active_company_no_jobs(monkeypatch, applicants, companies, reviews):

    install_fake_db(monkeypatch, applicants, companies, {}, reviews)


@given("an active company has company reviews")
def active_company_has_reviews(setup_db):
    pass


@given("an active company has no company reviews")
def active_company_no_reviews(monkeypatch, applicants, companies, jobs):

    install_fake_db(monkeypatch, applicants, companies, jobs, {})


@given("no active companies exist")
def no_active_companies(monkeypatch, applicants):

    install_fake_db(monkeypatch, applicants, {}, {}, {})


# ============================================================
# WHEN
# ============================================================


@when("the job seeker opens the browse companies page")
def open_browse_companies(context):

    context.response = browse()


# ============================================================
# THEN
# ============================================================


@then("the system should display the browse companies page")
def display_browse_page(context):

    assert context.response["template"] == "companyBrowse.html"


@then("the active companies should be displayed")
def active_companies_displayed(context):

    companies = context.response["context"]["companies"]

    names = [company["company_name"] for company in companies]

    assert "ABC Technology Sdn Bhd" in names

    assert "XYZ Solutions" in names


@then("inactive companies should not be displayed")
def inactive_companies_hidden(context):

    companies = context.response["context"]["companies"]

    names = [company["company_name"] for company in companies]

    assert "Inactive Company" not in names


@then(
    "each company should display its company name industry location rating review count and job count"
)
def company_information_displayed(context):

    companies = context.response["context"]["companies"]

    assert len(companies) > 0

    for company in companies:
        assert "company_name" in company

        assert "industry" in company

        assert "location" in company

        assert "rating" in company

        assert "review_count" in company

        assert "job_count" in company


@then("the company logo should be available")
def company_logo_available(context):

    companies = context.response["context"]["companies"]

    assert companies[0]["logo"] != ""


@then("the missing company logo should be handled safely")
def missing_logo_safe(context):

    companies = context.response["context"]["companies"]

    assert len(companies) == 1

    assert companies[0]["logo"] == ""


@then("the number of available jobs should be displayed")
def available_job_count_displayed(context):

    companies = context.response["context"]["companies"]

    abc_company = next(
        company for company in companies if company["company_name"] == "ABC Technology Sdn Bhd"
    )

    assert abc_company["job_count"] == 2


@then("the company job count should display zero")
def zero_job_count_displayed(context):

    companies = context.response["context"]["companies"]

    for company in companies:
        assert company["job_count"] == 0


@then("the company rating and review count should be displayed")
def rating_displayed(context):

    companies = context.response["context"]["companies"]

    abc_company = next(
        company for company in companies if company["company_name"] == "ABC Technology Sdn Bhd"
    )

    assert abc_company["rating"] == 4.5

    assert abc_company["review_count"] == 2


@then("the company rating and review count should display zero")
def no_review_display(context):

    companies = context.response["context"]["companies"]

    for company in companies:
        assert company["rating"] == 0

        assert company["review_count"] == 0


@then("the system should display an empty company list without crashing")
def empty_company_list(context):

    assert context.response["context"]["companies"] == []

    assert context.response["context"]["total_company"] == 0

    assert context.response["template"] == "companyBrowse.html"
