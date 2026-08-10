import asyncio

from unittest.mock import patch

import pytest

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)


with patch(
    "firebase_admin.firestore.client",
    return_value=None
):
    from job_portal_web.backend.routes import (
        companyDetails as company_module
    )


APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"
COMPANY_ID = "COMPANY001"


scenarios(
    "features/viewCompanyJobs.feature"
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

        result = []

        for document_id, data in self.documents.items():

            valid = True

            for field, operator, value in self.filters:

                if operator == "==":

                    if data.get(field) != value:

                        valid = False
                        break

            if valid:

                result.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        True
                    )
                )

        return result


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


class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "job_seeker",
            "applicant_id": APPLICANT_ID
        }


class Context:

    def __init__(self):

        self.response = None


@pytest.fixture
def context():

    return Context()


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
                "ABC Technology",

            "status":
                "Active",

            "city":
                "Kuala Lumpur",

            "state":
                "Kuala Lumpur",

            "country":
                "Malaysia"
        }
    }


@pytest.fixture
def jobs():

    return {

        "JOB001": {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "job_title":
                "Software Engineer",

            "salaryType":
                "fixed",

            "salary":
                5000
        },

        "JOB002": {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "job_title":
                "Backend Developer",

            "salaryType":
                "range",

            "minSalary":
                4000,

            "maxSalary":
                6000
        },

        "JOB003": {

            "company_id":
                COMPANY_ID,

            "status":
                "Closed",

            "job_title":
                "Old Job"
        }
    }


@pytest.fixture
def reviews():

    return {

        "REVIEW001": {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "overall_rating":
                5
        }
    }


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


def open_jobs(
    company_id=COMPANY_ID
):

    return asyncio.run(
        company_module.company_jobs(
            request=FakeRequest(),
            company_id=company_id
        )
    )


# ============================================================
# NORMAL TESTS
# ============================================================

def test_company_jobs_page(
    setup_db
):

    response = open_jobs()

    assert (
        response["template"]
        == "companyJobs.html"
    )


def test_only_active_jobs(
    setup_db
):

    response = open_jobs()

    jobs = (
        response["context"]["jobs"]
    )

    assert len(jobs) == 2

    assert all(
        job["status"] == "Active"
        for job in jobs
    )


def test_fixed_salary(
    setup_db
):

    response = open_jobs()

    job = next(
        job
        for job in response["context"]["jobs"]
        if job["id"] == "JOB001"
    )

    assert (
        job["salary_display"]
        == "RM 5,000"
    )


def test_range_salary(
    setup_db
):

    response = open_jobs()

    job = next(
        job
        for job in response["context"]["jobs"]
        if job["id"] == "JOB002"
    )

    assert (
        job["salary_display"]
        ==
        "RM 4,000 - RM 6,000"
    )


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

    response = open_jobs(
        "INVALID"
    )

    assert (
        response["template"]
        == "404.html"
    )


# ============================================================
# CUSTOM JOB HELPER
# ============================================================

def install_single_job(
    monkeypatch,
    applicants,
    companies,
    reviews,
    job
):

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {
            "TESTJOB": job
        },
        reviews
    )


# ============================================================
# BDD GIVEN
# ============================================================

@given(
    "an active company exists for company jobs"
)
def active_company_jobs(
    setup_db
):

    pass


@given(
    "the company has active and inactive jobs"
)
def mixed_company_jobs(
    setup_db
):

    pass


@given(
    "the company has a fixed salary job"
)
def fixed_salary_job(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "fixed",
            "salary": 5000
        }
    )


@given(
    "the company has a fixed salary stored with comma"
)
def comma_fixed_salary(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "fixed",
            "salary": "5,500"
        }
    )


@given(
    "the company has an invalid fixed salary"
)
def invalid_fixed_salary(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "fixed",
            "salary": "ABC"
        }
    )


@given(
    "the company has a salary range job"
)
def range_salary_job(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "range",
            "minSalary": 4000,
            "maxSalary": 6000
        }
    )


@given(
    "the company has an invalid salary range"
)
def invalid_range_salary(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "range",
            "minSalary": "ABC",
            "maxSalary": 6000
        }
    )


@given(
    "the company has a negotiable salary job"
)
def negotiable_job(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "negotiable"
        }
    )


@given(
    "the company has a job with unknown salary type"
)
def unknown_salary_type(
    monkeypatch,
    applicants,
    companies,
    reviews
):

    install_single_job(
        monkeypatch,
        applicants,
        companies,
        reviews,
        {
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Developer",
            "salaryType": "something"
        }
    )


@given(
    "the company has no active jobs for company jobs page"
)
def no_active_jobs(
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
    "the company has reviews for company jobs"
)
def company_jobs_reviews(
    setup_db
):

    pass


@given(
    "the requested company does not exist for company jobs"
)
def missing_company_jobs(
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


# ============================================================
# WHEN
# ============================================================

@when(
    "the job seeker opens the company jobs page"
)
def open_jobs_step(
    context
):

    context.response = open_jobs()


# ============================================================
# THEN
# ============================================================

@then(
    "the company jobs page should be displayed"
)
def verify_jobs_page(
    context
):

    assert (
        context.response["template"]
        == "companyJobs.html"
    )


@then(
    "the company information should be available on the jobs page"
)
def verify_company_information(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["companyName"]
        ==
        "ABC Technology"
    )


@then(
    "only active company jobs should be returned"
)
def verify_active_jobs(
    context
):

    jobs = (
        context.response["context"]
        ["jobs"]
    )

    assert len(jobs) == 2

    assert all(
        job["status"] == "Active"
        for job in jobs
    )


@then(
    "the company active job count should be correct"
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
    "the fixed salary should be formatted correctly"
)
def verify_fixed_salary(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "RM 5,000"
    )


@then(
    "the fixed salary with comma should be formatted correctly"
)
def verify_comma_salary(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "RM 5,500"
    )


@then(
    "the invalid fixed salary should become negotiable"
)
def verify_invalid_fixed(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "Negotiable"
    )


@then(
    "the salary range should be formatted correctly"
)
def verify_range_salary(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        ==
        "RM 4,000 - RM 6,000"
    )


@then(
    "the invalid salary range should become negotiable"
)
def verify_invalid_range(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "Negotiable"
    )


@then(
    "the salary should be negotiable"
)
def verify_negotiable(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "Negotiable"
    )


@then(
    "the unknown salary type should become negotiable"
)
def verify_unknown_salary(
    context
):

    assert (
        context.response["context"]
        ["jobs"][0]
        ["salary_display"]
        == "Negotiable"
    )


@then(
    "the company jobs list should be empty"
)
def verify_empty_jobs(
    context
):

    assert (
        context.response["context"]
        ["jobs"]
        == []
    )

    assert (
        context.response["context"]
        ["total_jobs"]
        == 0
    )


@then(
    "the company rating should be available on the jobs page"
)
def verify_jobs_rating(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["rating"]
        == 5
    )


@then(
    "the company jobs not found page should be displayed"
)
def verify_jobs_not_found(
    context
):

    assert (
        context.response["template"]
        == "404.html"
    )