import asyncio

from unittest.mock import patch

import pytest

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)


# ============================================================
# IMPORT WITHOUT REAL FIREBASE CONNECTION
# ============================================================

with patch(
    "firebase_admin.firestore.client",
    return_value=None
):
    from job_portal_web.backend.routes import (
        companyDetails as company_module
    )


# ============================================================
# CONSTANTS
# ============================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"

COMPANY_ID = "COMPANY001"


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios(
    "features/viewCompanyDetails.feature"
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
        self._data = data or {}
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

        data = self.collection.documents.get(
            self.document_id
        )

        if data is None:

            return FakeDocumentSnapshot(
                self.document_id,
                {},
                False
            )

        return FakeDocumentSnapshot(
            self.document_id,
            data,
            True
        )


class FakeQuery:

    def __init__(
        self,
        documents,
        filters=None
    ):

        self.documents = documents
        self.filters = filters or []

    def where(
        self,
        field,
        operator,
        value
    ):

        return FakeQuery(
            self.documents,
            self.filters + [
                (
                    field,
                    operator,
                    value
                )
            ]
        )

    def stream(self):

        results = []

        for document_id, data in self.documents.items():

            matched = True

            for field, operator, expected in self.filters:

                if operator == "==":

                    if data.get(field) != expected:

                        matched = False
                        break

            if matched:

                results.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        True
                    )
                )

        return results


class FakeCollection:

    def __init__(
        self,
        documents=None
    ):

        self.documents = documents or {}

    def document(
        self,
        document_id
    ):

        return FakeDocumentReference(
            self,
            document_id
        )

    def where(
        self,
        field,
        operator,
        value
    ):

        return FakeQuery(
            self.documents
        ).where(
            field,
            operator,
            value
        )


class FakeDB:

    def __init__(
        self,
        applicants=None,
        companies=None,
        jobs=None,
        reviews=None
    ):

        self.collections = {

            "job_seeker":
                FakeCollection(
                    applicants or {}
                ),

            "company":
                FakeCollection(
                    companies or {}
                ),

            "job_list":
                FakeCollection(
                    jobs or {}
                ),

            "company_review":
                FakeCollection(
                    reviews or {}
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
# REQUEST
# ============================================================

class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "job_seeker",
            "applicant_id": APPLICANT_ID
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
# DEFAULT DATA
# ============================================================

@pytest.fixture
def applicants():

    return {

        APPLICANT_ID: {
            "uid": APPLICANT_ID,
            "full_name": "Test User"
        }
    }


@pytest.fixture
def companies():

    return {

        COMPANY_ID: {

            "companyName":
                "ABC Technology Sdn Bhd",

            "status":
                "Active",

            "city":
                "Kuala Lumpur",

            "state":
                "Kuala Lumpur",

            "country":
                "Malaysia",

            "industry_id":
                "Information Technology",

            "companyDescription":
                "Technology company",

            "logo":
                "/images/company.png"
        }
    }


@pytest.fixture
def jobs():

    return {

        "JOB001": {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Software Engineer",
            "salaryType": "fixed",
            "salary": 5000
        },

        "JOB002": {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Backend Developer",
            "salaryType": "range",
            "minSalary": 4000,
            "maxSalary": 6000
        },

        "JOB003": {
            "company_id": COMPANY_ID,
            "status": "Closed",
            "job_title": "Old Job"
        }
    }


@pytest.fixture
def reviews():

    return {

        "REVIEW001": {

            "company_id": COMPANY_ID,
            "status": "Active",

            "overall_rating": 4,

            "work_environment": 4,
            "management": 4,
            "career_growth": 4,
            "work_life_balance": 4,
            "benefits": 4,
            "company_culture": 4,
            "learning_opportunities": 4
        },

        "REVIEW002": {

            "company_id": COMPANY_ID,
            "status": "Active",

            "overall_rating": 5,

            "work_environment": 5,
            "management": 5,
            "career_growth": 5,
            "work_life_balance": 5,
            "benefits": 5,
            "company_culture": 5,
            "learning_opportunities": 5
        }
    }


# ============================================================
# INSTALL DB
# ============================================================

def install_fake_db(
    monkeypatch,
    applicants,
    companies,
    jobs,
    reviews
):

    fake_db = FakeDB(
        applicants,
        companies,
        jobs,
        reviews
    )

    monkeypatch.setattr(
        company_module,
        "db",
        fake_db
    )

    monkeypatch.setattr(
        company_module,
        "templates",
        FakeTemplates()
    )

    return fake_db


@pytest.fixture
def setup_db(
    monkeypatch,
    applicants,
    companies,
    jobs,
    reviews
):

    return install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        reviews
    )


# ============================================================
# HELPER
# ============================================================

def open_details(
    company_id=COMPANY_ID
):

    return asyncio.run(
        company_module.company_details(
            request=FakeRequest(),
            company_id=company_id
        )
    )


# ============================================================
# NORMAL PYTEST
# ============================================================

def test_company_details_page(
    setup_db
):

    response = open_details()

    assert (
        response["template"]
        == "companyDetails.html"
    )


def test_company_information(
    setup_db
):

    response = open_details()

    company = (
        response["context"]["company"]
    )

    assert (
        company["companyName"]
        == "ABC Technology Sdn Bhd"
    )

    assert (
        company["id"]
        == COMPANY_ID
    )


def test_company_location(
    setup_db
):

    response = open_details()

    assert (
        response["context"]
        ["company"]
        ["location"]
        ==
        "Kuala Lumpur, Kuala Lumpur, Malaysia"
    )


def test_only_active_jobs_counted(
    setup_db
):

    response = open_details()

    assert (
        response["context"]
        ["company"]
        ["job_count"]
        == 2
    )


def test_only_five_jobs_displayed(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    many_jobs = {}

    for number in range(1, 8):

        many_jobs[
            f"JOB{number}"
        ] = {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "job_title":
                f"Job {number}",

            "salaryType":
                "fixed",

            "salary":
                5000
        }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        many_jobs,
        reviews
    )

    response = open_details()

    assert (
        response["context"]
        ["total_jobs"]
        == 7
    )

    assert (
        len(
            response["context"]["jobs"]
        )
        == 5
    )


def test_no_jobs(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        reviews
    )

    response = open_details()

    assert (
        response["context"]
        ["company"]
        ["job_count"]
        == 0
    )

    assert (
        response["context"]["jobs"]
        == []
    )


def test_review_average(
    setup_db
):

    response = open_details()

    company = (
        response["context"]["company"]
    )

    assert company["rating"] == 4.5
    assert company["review_count"] == 2


def test_missing_company(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        {},
        {},
        {}
    )

    response = open_details(
        "INVALID"
    )

    assert (
        response["template"]
        == "404.html"
    )


# ============================================================
# BDD
# ============================================================

@given(
    "an active company exists for company details"
)
def active_company_details(
    setup_db
):

    pass


@given(
    "a company has active jobs for company details"
)
def active_jobs_details(
    setup_db
):

    pass


@given(
    "a company has more than five active jobs"
)
def more_than_five_jobs(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    jobs = {}

    for number in range(1, 8):

        jobs[f"JOB{number}"] = {

            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": f"Job {number}",
            "salaryType": "fixed",
            "salary": 5000
        }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        reviews
    )


@given(
    "a company has no active jobs for company details"
)
def no_jobs_details(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        reviews
    )


@given(
    "a company has active and inactive jobs for company details"
)
def mixed_jobs_details(
    setup_db
):

    pass


@given(
    "a company has reviews for company details"
)
def reviews_details(
    setup_db
):

    pass


@given(
    "a company has no reviews for company details"
)
def no_reviews_details(
    monkeypatch,
    applicants,
    companies,
    jobs
):

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        {}
    )


@given(
    "a company has active and inactive reviews for company details"
)
def mixed_reviews_details(
    monkeypatch,
    applicants,
    companies,
    jobs,
    reviews
):

    custom_reviews = dict(reviews)

    custom_reviews["INACTIVE"] = {

        "company_id":
            COMPANY_ID,

        "status":
            "Inactive",

        "overall_rating":
            1
    }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        custom_reviews
    )


@given(
    "the requested company does not exist for company details"
)
def missing_company_details(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        {},
        {},
        {}
    )


@given(
    "the applicant profile does not exist for company details"
)
def missing_applicant_details(
    monkeypatch,
    companies,
    jobs,
    reviews
):

    install_fake_db(
        monkeypatch,
        {},
        companies,
        jobs,
        reviews
    )


@when(
    "the job seeker opens the company details page"
)
def open_company_details_step(
    context
):

    context.response = open_details()


@then(
    "the company details page should be displayed"
)
def verify_details_page(
    context
):

    assert (
        context.response["template"]
        == "companyDetails.html"
    )


@then(
    "the company information should be available"
)
def verify_information(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    assert company["id"] == COMPANY_ID
    assert company["companyName"]


@then(
    "the company location should contain city state and country"
)
def verify_location(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["location"]
        ==
        "Kuala Lumpur, Kuala Lumpur, Malaysia"
    )


@then(
    "the active job count should be correct"
)
def verify_job_count(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["job_count"]
        == 2
    )


@then(
    "only five latest jobs should be included on the company details page"
)
def verify_five_jobs(
    context
):

    assert (
        len(
            context.response["context"]
            ["jobs"]
        )
        == 5
    )

    assert (
        context.response["context"]
        ["total_jobs"]
        == 7
    )


@then(
    "the company job count should be zero"
)
def verify_zero_jobs(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["job_count"]
        == 0
    )


@then(
    "inactive jobs should not contribute to the company job count"
)
def verify_inactive_job_excluded(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["job_count"]
        == 2
    )


@then(
    "the company rating and review count should be calculated"
)
def verify_review_summary(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    assert company["rating"] == 4.5
    assert company["review_count"] == 2


@then(
    "the company rating and review count should be zero"
)
def verify_zero_reviews(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    assert company["rating"] == 0
    assert company["review_count"] == 0


@then(
    "only active reviews should contribute to the company rating"
)
def verify_inactive_review_excluded(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    assert company["rating"] == 4.5
    assert company["review_count"] == 2


@then(
    "the company not found page should be displayed"
)
def verify_not_found(
    context
):

    assert (
        context.response["template"]
        == "404.html"
    )


@then(
    "the company details page should still be displayed safely"
)
def verify_missing_applicant(
    context
):

    assert (
        context.response["template"]
        == "companyDetails.html"
    )

    assert (
        context.response["context"]
        ["user"]
        is None
    )