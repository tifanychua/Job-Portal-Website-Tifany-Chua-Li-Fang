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
    "features/viewCompanyReviews.feature"
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

            valid = True

            for field, operator, value in self.filters:

                if operator == "==":

                    if data.get(field) != value:

                        valid = False
                        break

            if valid:

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
            "company_id": COMPANY_ID,
            "status": "Active",
            "job_title": "Software Engineer"
        },

        "JOB002": {
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

            "work_environment": 3,
            "management": 4,
            "career_growth": 3,
            "work_life_balance": 4,
            "benefits": 3,
            "company_culture": 4,
            "learning_opportunities": 3
        },

        "REVIEW002": {

            "company_id": COMPANY_ID,
            "status": "Active",

            "overall_rating": 5,

            "work_environment": 5,
            "management": 4,
            "career_growth": 5,
            "work_life_balance": 4,
            "benefits": 5,
            "company_culture": 4,
            "learning_opportunities": 5
        },

        "INACTIVE": {

            "company_id": COMPANY_ID,
            "status": "Inactive",

            "overall_rating": 1,

            "work_environment": 1,
            "management": 1,
            "career_growth": 1,
            "work_life_balance": 1,
            "benefits": 1,
            "company_culture": 1,
            "learning_opportunities": 1
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


def open_reviews(
    company_id=COMPANY_ID
):

    return asyncio.run(
        company_module.company_reviews(
            request=FakeRequest(),
            company_id=company_id
        )
    )


# ============================================================
# NORMAL TESTS
# ============================================================

def test_company_reviews_page(
    setup_db
):

    response = open_reviews()

    assert (
        response["template"]
        == "companyReviews.html"
    )


def test_only_active_reviews(
    setup_db
):

    response = open_reviews()

    reviews = (
        response["context"]["reviews"]
    )

    assert len(reviews) == 2

    assert all(
        review["status"] == "Active"
        for review in reviews
    )


def test_overall_rating(
    setup_db
):

    response = open_reviews()

    assert (
        response["context"]
        ["company"]
        ["rating"]
        == 4.5
    )


def test_review_count(
    setup_db
):

    response = open_reviews()

    assert (
        response["context"]
        ["company"]
        ["review_count"]
        == 2
    )


def test_review_averages(
    setup_db
):

    company = (
        open_reviews()
        ["context"]
        ["company"]
    )

    assert (
        company["work_environment_avg"]
        == 4.0
    )

    assert (
        company["management_avg"]
        == 4.0
    )

    assert (
        company["career_growth_avg"]
        == 4.0
    )

    assert (
        company["work_life_balance_avg"]
        == 4.0
    )

    assert (
        company["benefits_avg"]
        == 4.0
    )

    assert (
        company["company_culture_avg"]
        == 4.0
    )

    assert (
        company[
            "learning_opportunities_avg"
        ]
        == 4.0
    )


def test_no_reviews(
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

    company = (
        open_reviews()
        ["context"]
        ["company"]
    )

    assert company["rating"] == 0
    assert company["review_count"] == 0
    assert company["five_star"] == 0
    assert company["four_star"] == 0
    assert company["three_star"] == 0
    assert company["two_star"] == 0
    assert company["one_star"] == 0


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

    response = open_reviews(
        "INVALID"
    )

    assert (
        response["template"]
        == "404.html"
    )


# ============================================================
# BDD GIVEN
# ============================================================

@given(
    "an active company exists for company reviews"
)
def active_company_reviews(
    setup_db
):

    pass


@given(
    "the company has active and inactive reviews"
)
def mixed_reviews(
    setup_db
):

    pass


@given(
    "the company has multiple active reviews"
)
def multiple_reviews(
    setup_db
):

    pass


@given(
    "reviews with all star ratings exist"
)
def all_star_ratings(
    monkeypatch,
    applicants,
    companies,
    jobs
):

    custom_reviews = {}

    for rating in range(1, 6):

        custom_reviews[
            f"R{rating}"
        ] = {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "overall_rating":
                rating,

            "work_environment":
                rating,

            "management":
                rating,

            "career_growth":
                rating,

            "work_life_balance":
                rating,

            "benefits":
                rating,

            "company_culture":
                rating,

            "learning_opportunities":
                rating
        }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        custom_reviews
    )


@given(
    "the company has no active reviews"
)
def no_active_reviews(
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
    "an active review contains missing category ratings"
)
def missing_category_values(
    monkeypatch,
    applicants,
    companies,
    jobs
):

    reviews = {

        "REVIEW001": {

            "company_id":
                COMPANY_ID,

            "status":
                "Active",

            "overall_rating":
                4
        }
    }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        reviews
    )


@given(
    "the company has active jobs for company reviews"
)
def review_page_jobs(
    setup_db
):

    pass


@given(
    "the requested company does not exist for company reviews"
)
def missing_company_reviews(
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
    "the job seeker opens the company reviews page"
)
def open_reviews_step(
    context
):

    context.response = open_reviews()


# ============================================================
# THEN
# ============================================================

@then(
    "the company reviews page should be displayed"
)
def verify_reviews_page(
    context
):

    assert (
        context.response["template"]
        == "companyReviews.html"
    )


@then(
    "only active company reviews should be returned"
)
def verify_active_reviews(
    context
):

    reviews = (
        context.response["context"]
        ["reviews"]
    )

    assert len(reviews) == 2

    assert all(
        review["status"] == "Active"
        for review in reviews
    )


@then(
    "the overall company rating should be correct"
)
def verify_rating(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["rating"]
        == 4.5
    )


@then(
    "the company review count should be correct"
)
def verify_review_count(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["review_count"]
        == 2
    )


@then(
    "the work environment average should be correct"
)
def verify_work_environment(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["work_environment_avg"]
        == 4.0
    )


@then(
    "the management average should be correct"
)
def verify_management(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["management_avg"]
        == 4.0
    )


@then(
    "the career growth average should be correct"
)
def verify_career_growth(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["career_growth_avg"]
        == 4.0
    )


@then(
    "the work life balance average should be correct"
)
def verify_work_life(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["work_life_balance_avg"]
        == 4.0
    )


@then(
    "the benefits average should be correct"
)
def verify_benefits(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["benefits_avg"]
        == 4.0
    )


@then(
    "the company culture average should be correct"
)
def verify_culture(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["company_culture_avg"]
        == 4.0
    )


@then(
    "the learning opportunities average should be correct"
)
def verify_learning(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["learning_opportunities_avg"]
        == 4.0
    )


@then(
    "the five star review count should be correct"
)
def verify_five_star(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["five_star"]
        == 1
    )


@then(
    "the four star review count should be correct"
)
def verify_four_star(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["four_star"]
        == 1
    )


@then(
    "the three star review count should be correct"
)
def verify_three_star(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["three_star"]
        == 1
    )


@then(
    "the two star review count should be correct"
)
def verify_two_star(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["two_star"]
        == 1
    )


@then(
    "the one star review count should be correct"
)
def verify_one_star(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["one_star"]
        == 1
    )


@then(
    "all company review summary values should be zero"
)
def verify_zero_summary(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    fields = [
        "rating",
        "review_count",
        "work_environment_avg",
        "management_avg",
        "career_growth_avg",
        "work_life_balance_avg",
        "benefits_avg",
        "company_culture_avg",
        "learning_opportunities_avg",
        "five_star",
        "four_star",
        "three_star",
        "two_star",
        "one_star"
    ]

    for field in fields:

        assert company[field] == 0


@then(
    "missing category ratings should be treated safely"
)
def verify_missing_categories(
    context
):

    company = (
        context.response["context"]
        ["company"]
    )

    assert company["rating"] == 4

    assert (
        company["work_environment_avg"]
        == 0
    )

    assert (
        company["management_avg"]
        == 0
    )

    assert (
        company["career_growth_avg"]
        == 0
    )

    assert (
        company["work_life_balance_avg"]
        == 0
    )

    assert (
        company["benefits_avg"]
        == 0
    )

    assert (
        company["company_culture_avg"]
        == 0
    )

    assert (
        company[
            "learning_opportunities_avg"
        ]
        == 0
    )


@then(
    "the company job count should be available on the reviews page"
)
def verify_review_page_job_count(
    context
):

    assert (
        context.response["context"]
        ["company"]
        ["job_count"]
        == 1
    )


@then(
    "the company reviews not found page should be displayed"
)
def verify_reviews_not_found(
    context
):

    assert (
        context.response["template"]
        == "404.html"
    )