import asyncio
import pytest

from unittest.mock import patch
from pytest_bdd import given, scenarios, then, when


# ============================================================
# IMPORT ROUTE WITHOUT CONNECTING TO REAL FIREBASE
# ============================================================

with patch(
    "firebase_admin.firestore.client",
    return_value=None
):

    from job_portal_web.backend.routes import (
        companyBrowse as company_module
    )


# ============================================================
# CONSTANTS
# ============================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ============================================================
# LOAD FEATURE
# ============================================================

scenarios(
    "features/browseCompanies.feature"
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
                exists=False
            )

        return FakeDocumentSnapshot(
            self.document_id,
            data,
            exists=True
        )


class FakeQuery:

    def __init__(
        self,
        documents
    ):

        self.documents = documents
        self.filters = []

    def where(
        self,
        field,
        operator,
        value
    ):

        self.filters.append(
            (
                field,
                operator,
                value
            )
        )

        return self

    def stream(self):

        results = []

        for document_id, data in (
            self.documents.items()
        ):

            matched = True

            for (
                field,
                operator,
                expected
            ) in self.filters:

                if operator != "==":

                    continue

                if (
                    data.get(field)
                    != expected
                ):

                    matched = False

                    break

            if matched:

                results.append(
                    FakeDocumentSnapshot(
                        document_id,
                        data,
                        exists=True
                    )
                )

        return results


class FakeCollection:

    def __init__(
        self,
        documents=None
    ):

        self.documents = (
            documents or {}
        )

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

        query = FakeQuery(
            self.documents
        )

        return query.where(
            field,
            operator,
            value
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
# FAKE REQUEST
# ============================================================

class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "job_seeker",
            "applicant_id": APPLICANT_ID
        }


# ============================================================
# BDD CONTEXT
# ============================================================

class Context:

    def __init__(self):

        self.response = None
        self.expected = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# APPLICANT DATA
# ============================================================

@pytest.fixture
def applicants():

    return {

        APPLICANT_ID: {

            "uid": APPLICANT_ID,

            "full_name": "Test User",

            "position":
                "Software Engineer",

            "profileImage":
                "/images/user.png"
        }
    }


# ============================================================
# COMPANY DATA
# ============================================================

@pytest.fixture
def companies():

    return {

        "COMPANY001": {

            "companyName":
                "ABC Technology Sdn Bhd",

            "status":
                "Active",

            "city":
                "Kuala Lumpur",

            "state":
                "Kuala Lumpur",

            "industry_id":
                "Information Technology",

            "logo":
                "/images/abc.png"
        },


        "COMPANY002": {

            "companyName":
                "XYZ Solutions",

            "status":
                "Active",

            "city":
                "Petaling Jaya",

            "state":
                "Selangor",

            "industry_id":
                "Software Development",

            "logo":
                "/images/xyz.png"
        },


        "COMPANY003": {

            "companyName":
                "Inactive Company",

            "status":
                "Inactive",

            "city":
                "Johor Bahru",

            "state":
                "Johor",

            "industry_id":
                "Finance",

            "logo":
                ""
        }
    }


# ============================================================
# JOB DATA
# ============================================================

@pytest.fixture
def jobs():

    return {

        "JOB001": {

            "company_id":
                "COMPANY001",

            "status":
                "Active",

            "job_title":
                "Software Engineer"
        },


        "JOB002": {

            "company_id":
                "COMPANY001",

            "status":
                "Active",

            "job_title":
                "Backend Developer"
        },


        "JOB003": {

            "company_id":
                "COMPANY001",

            "status":
                "Closed",

            "job_title":
                "Old Developer Job"
        },


        "JOB004": {

            "company_id":
                "COMPANY002",

            "status":
                "Active",

            "job_title":
                "System Analyst"
        }
    }


# ============================================================
# REVIEW DATA
# ============================================================

@pytest.fixture
def reviews():

    return {

        "REVIEW001": {

            "company_id":
                "COMPANY001",

            "overall_rating":
                4.0
        },


        "REVIEW002": {

            "company_id":
                "COMPANY001",

            "overall_rating":
                5.0
        },


        "REVIEW003": {

            "company_id":
                "COMPANY002",

            "overall_rating":
                3.5
        }
    }


# ============================================================
# INSTALL DATABASE
# ============================================================

def install_fake_db(
    monkeypatch,
    applicants,
    companies,
    jobs,
    reviews
):

    fake_db = FakeDB(
        applicants=applicants,
        companies=companies,
        jobs=jobs,
        reviews=reviews
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

def browse(
        keyword="",
    page=1
):

    request = FakeRequest()

    return asyncio.run(
        company_module.browse_companies(
            request=request,
            keyword=keyword,
            page=page
        )
    )


# ============================================================
# COMPANY GENERATOR
# ============================================================

def create_companies(
    count
):

    result = {}

    for number in range(
        1,
        count + 1
    ):

        result[
            f"C{number:03d}"
        ] = {

            "companyName":
                f"Company {number}",

            "status":
                "Active",

            "city":
                "Kuala Lumpur",

            "state":
                "Kuala Lumpur",

            "industry_id":
                "Technology",

            "logo":
                ""
        }

    return result


# ============================================================
# NORMAL PYTEST TESTS
# ============================================================


def test_browse_companies_page(
    setup_db
):

    response = browse()

    assert (
        response["template"]
        == "companyBrowse.html"
    )

    print(
        "✅ SUCCESS: Browse companies page displayed"
    )


def test_only_active_companies_displayed(
    setup_db
):

    response = browse()

    result = (
        response["context"]
        ["companies"]
    )

    assert len(result) == 2

    names = [
        company["company_name"]
        for company in result
    ]

    assert (
        "Inactive Company"
        not in names
    )

    print(
        "✅ SUCCESS: Only active companies displayed"
    )


def test_company_information(
    setup_db
):

    response = browse()

    company = (
        response["context"]
        ["companies"][0]
    )

    required = [
        "id",
        "company_name",
        "logo",
        "industry",
        "location",
        "rating",
        "review_count",
        "job_count"
    ]

    for field in required:

        assert field in company

    print(
        "✅ SUCCESS: Company information available"
    )


def test_company_active_job_count(
    setup_db
):

    response = browse(
        keyword="ABC Technology"
    )

    company = (
        response["context"]
        ["companies"][0]
    )

    assert (
        company["job_count"]
        == 2
    )

    print(
        "✅ SUCCESS: Only active jobs counted"
    )


def test_company_average_rating(
    setup_db
):

    response = browse(
        keyword="ABC Technology"
    )

    company = (
        response["context"]
        ["companies"][0]
    )

    assert (
        company["rating"]
        == 4.5
    )

    assert (
        company["review_count"]
        == 2
    )

    print(
        "✅ SUCCESS: Average rating correct"
    )


def test_company_no_reviews(
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

    response = browse(
        keyword="ABC"
    )

    company = (
        response["context"]
        ["companies"][0]
    )

    assert (
        company["rating"]
        == 0
    )

    assert (
        company["review_count"]
        == 0
    )

    print(
        "✅ SUCCESS: No-review company handled"
    )


def test_search_company_name(
    setup_db
):

    response = browse(
        keyword="ABC Technology"
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )


def test_search_partial_company_name(
    setup_db
):

    response = browse(
        keyword="ABC"
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )


def test_search_case_insensitive(
    setup_db
):

    lower = browse(
        keyword="abc technology"
    )

    upper = browse(
        keyword="ABC TECHNOLOGY"
    )

    assert (
        lower["context"]
        ["total_company"]
        ==
        upper["context"]
        ["total_company"]
    )


def test_search_extra_spaces(
    setup_db
):

    response = browse(
        keyword="   ABC Technology   "
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )


def test_search_by_city(
    setup_db
):

    response = browse(
        keyword="Petaling Jaya"
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )

    assert (
        response["context"]
        ["companies"][0]
        ["company_name"]
        == "XYZ Solutions"
    )


def test_search_by_state(
    setup_db
):

    response = browse(
        keyword="Selangor"
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )


def test_search_by_industry(
    setup_db
):

    response = browse(
        keyword="Software Development"
    )

    assert (
        response["context"]
        ["total_company"]
        == 1
    )


def test_non_existing_company_search(
    setup_db
):

    response = browse(
        keyword="DOES NOT EXIST"
    )

    assert (
        response["context"]
        ["total_company"]
        == 0
    )

    assert (
        response["context"]
        ["companies"]
        == []
    )


def test_empty_search_returns_active_companies(
    setup_db
):

    response = browse(
        keyword=""
    )

    assert (
        response["context"]
        ["total_company"]
        == 2
    )


def test_highest_rating_first(
    setup_db
):

    response = browse()

    companies = (
        response["context"]
        ["companies"]
    )

    assert (
        companies[0]
        ["company_name"]
        == "ABC Technology Sdn Bhd"
    )

    assert (
        companies[0]["rating"]
        == 4.5
    )


def test_company_no_active_jobs(
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

    response = browse(
        keyword="ABC"
    )

    company = (
        response["context"]
        ["companies"][0]
    )

    assert (
        company["job_count"]
        == 0
    )


# ============================================================
# PAGINATION
# ============================================================

def test_less_than_12_companies_one_page(
    monkeypatch,
    applicants
):

    companies = create_companies(
        10
    )

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        {}
    )

    response = browse()

    assert (
        response["context"]
        ["total_pages"]
        == 1
    )

    assert (
        len(
            response["context"]
            ["companies"]
        )
        == 10
    )


def test_exactly_12_companies_one_page(
    monkeypatch,
    applicants
):

    companies = create_companies(
        12
    )

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        {}
    )

    response = browse()

    assert (
        response["context"]
        ["total_pages"]
        == 1
    )

    assert (
        len(
            response["context"]
            ["companies"]
        )
        == 12
    )


def test_13_companies_two_pages(
    monkeypatch,
    applicants
):

    companies = create_companies(
        13
    )

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        {}
    )

    response = browse()

    assert (
        response["context"]
        ["total_pages"]
        == 2
    )


def test_second_company_page(
    monkeypatch,
    applicants
):

    companies = create_companies(
        15
    )

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        {}
    )

    response = browse(
        page=2
    )

    assert (
        len(
            response["context"]
            ["companies"]
        )
        == 3
    )

    assert (
        response["context"]
        ["page"]
        == 2
    )


# ============================================================
# EMPTY COMPANY LIST
# ============================================================

def test_no_active_companies(
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

    response = browse()

    assert (
        response["context"]
        ["total_company"]
        == 0
    )

    assert (
        response["context"]
        ["companies"]
        == []
    )

    assert (
        response["context"]
        ["total_pages"]
        == 1
    )


# ============================================================
# MISSING APPLICANT
# ============================================================

def test_missing_applicant_profile(
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

    response = browse()

    assert (
        response["context"]
        ["user"]
        is None
    )

    assert (
        response["template"]
        == "companyBrowse.html"
    )


# ============================================================
# ============================================================
# BDD STEPS
# ============================================================
# ============================================================


@given(
    "the job seeker is logged into the system"
)
def job_seeker_logged_in(
    setup_db
):

    print(
        "✅ Job seeker login assumed"
    )


@given(
    "the job seeker is viewing the browse companies page"
)
def viewing_company_page(
    setup_db,
    context
):

    context.response = None


@when("the job seeker opens the browse companies page")
def open_company_page(context):

    context.response = browse()


@then(
    "the system should display the browse companies page"
)
def verify_company_page(
    context
):

    assert (
        context.response["template"]
        == "companyBrowse.html"
    )


@when(
    "the company records are loaded"
)
def company_records_loaded(
    context
):

    if (
        context.response
        is None
    ):

        context.response = browse()


@then(
    "only active companies should be displayed"
)
def verify_active_companies(
    context
):

    companies = (
        context.response["context"]
        ["companies"]
    )

    assert (
        len(companies)
        == 2
    )

    names = [
        item["company_name"]
        for item in companies
    ]

    assert (
        "Inactive Company"
        not in names
    )


@given(
    "active and inactive companies exist"
)
def active_inactive_companies(
    setup_db
):

    pass


@when(
    "the job seeker views the browse companies page"
)
def view_company_page(
    context
):

    context.response = browse()


@then(
    "inactive companies should not be displayed"
)
def verify_inactive_hidden(
    context
):

    names = [

        item["company_name"]

        for item in

        context.response["context"]
        ["companies"]
    ]

    assert (
        "Inactive Company"
        not in names
    )


@then(
    "the company name industry location rating review count and job count should be available"
)
def verify_company_information(
    context
):

    company = (
        context.response["context"]
        ["companies"][0]
    )

    required = [
        "company_name",
        "industry",
        "location",
        "rating",
        "review_count",
        "job_count"
    ]

    for field in required:

        assert (
            field in company
        )


@given(
    "a company contains a logo"
)
def company_has_logo(
    setup_db
):

    pass


@then(
    "the company logo should be included"
)
def verify_company_logo(
    context
):

    assert (
        context.response["context"]
        ["companies"][0]
        ["logo"]
        != ""
    )


@given(
    "a company does not contain a logo"
)
def company_without_logo(
    monkeypatch,
    applicants,
    jobs,
    reviews
):

    companies = {

        "COMPANY001": {

            "companyName":
                "ABC Technology Sdn Bhd",

            "status":
                "Active",

            "city":
                "Kuala Lumpur",

            "state":
                "Kuala Lumpur",

            "industry_id":
                "Information Technology"
        }
    }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        jobs,
        reviews
    )


@then(
    "the system should handle the missing company logo safely"
)
def verify_missing_logo(
    context
):

    company = (
        context.response["context"]
        ["companies"][0]
    )

    assert (
        company["logo"]
        == ""
    )


@when(
    "the job seeker searches using a company name"
)
def search_company_name_bdd(
    context
):

    context.response = browse(
        keyword="ABC Technology"
    )


@then(
    "matching companies should be displayed"
)
def matching_company_displayed(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches using a partial company name"
)
def partial_company_search(
    context
):

    context.response = browse(
        keyword="ABC"
    )


@then(
    "companies containing the partial company name should be displayed"
)
def verify_partial_company(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches using lowercase company name"
)
def lowercase_company_search(
    context
):

    context.response = browse(
        keyword="abc technology"
    )


@then(
    "the company search should be case insensitive"
)
def verify_case_insensitive_company(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches with extra spaces"
)
def company_search_spaces(
    context
):

    context.response = browse(
        keyword="   ABC Technology   "
    )


@then(
    "the extra spaces should be ignored"
)
def verify_spaces_ignored(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches using a city"
)
def search_city(
    context
):

    context.response = browse(
        keyword="Petaling Jaya"
    )


@then(
    "companies from the matching city should be displayed"
)
def verify_city(
    context
):

    assert (
        context.response["context"]
        ["companies"][0]
        ["company_name"]
        == "XYZ Solutions"
    )


@when(
    "the job seeker searches using a state"
)
def search_state(
    context
):

    context.response = browse(
        keyword="Selangor"
    )


@then(
    "companies from the matching state should be displayed"
)
def verify_state(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches using an industry"
)
def search_industry(
    context
):

    context.response = browse(
        keyword="Software Development"
    )


@then(
    "companies from the matching industry should be displayed"
)
def verify_industry(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 1
    )


@when(
    "the job seeker searches for a company that does not exist"
)
def search_missing_company(
    context
):

    context.response = browse(
        keyword="NOT EXIST"
    )


@then(
    "the system should return an empty company result without crashing"
)
def verify_missing_company_result(
    context
):

    assert (
        context.response["context"]
        ["companies"]
        == []
    )


@when(
    "the job seeker searches without entering a keyword"
)
def empty_company_search(
    context
):

    context.response = browse(
        keyword=""
    )


@then(
    "all active companies should remain available"
)
def verify_all_active_companies(
    context
):

    assert (
        context.response["context"]
        ["total_company"]
        == 2
    )


@given(
    "a company has active and inactive job postings"
)
def company_active_inactive_jobs(
    setup_db
):

    pass


@then(
    "only active jobs should contribute to the company job count"
)
def verify_job_count(
    context
):

    company = next(

        item

        for item in

        context.response["context"]
        ["companies"]

        if (
            item["company_name"]
            == "ABC Technology Sdn Bhd"
        )
    )

    assert (
        company["job_count"]
        == 2
    )


@given(
    "a company has no active job postings"
)
def company_no_active_jobs(
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


@then(
    "the company job count should be zero"
)
def verify_zero_jobs(
    context
):

    for company in (
        context.response["context"]
        ["companies"]
    ):

        assert (
            company["job_count"]
            == 0
        )


@given(
    "a company has multiple reviews"
)
def company_multiple_reviews(
    setup_db
):

    pass


@when(
    "the company rating is calculated"
)
def calculate_rating(
    context
):

    context.response = browse(
        keyword="ABC"
    )


@then(
    "the average company rating should be correct"
)
def verify_average_rating(
    context
):

    assert (
        context.response["context"]
        ["companies"][0]
        ["rating"]
        == 4.5
    )


@given(
    "a company has reviews producing a decimal average"
)
def decimal_average_reviews(
    setup_db
):

    pass


@then(
    "the company rating should be rounded to one decimal place"
)
def verify_rating_rounding(
    context
):

    rating = (
        context.response["context"]
        ["companies"][0]
        ["rating"]
    )

    assert (
        rating
        == round(
            rating,
            1
        )
    )


@given(
    "a company has no reviews"
)
def no_reviews(
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


@then(
    "the company rating and review count should be zero"
)
def verify_no_reviews(
    context
):

    company = (
        context.response["context"]
        ["companies"][0]
    )

    assert (
        company["rating"]
        == 0
    )

    assert (
        company["review_count"]
        == 0
    )


@given(
    "companies have different ratings"
)
def different_ratings(
    setup_db
):

    pass


@then(
    "the company with the highest rating should be displayed first"
)
def verify_highest_first(
    context
):

    companies = (
        context.response["context"]
        ["companies"]
    )

    assert (
        companies[0]["rating"]
        >=
        companies[-1]["rating"]
    )



# ============================================================
# SAME RATING - DIFFERENT REVIEW COUNT
# ============================================================

@given(
    "companies have the same rating but different review counts"
)
def same_rating_different_review_counts(
    monkeypatch,
    applicants
):

    companies = {
        "COMPANY001": {
            "companyName": "ABC Technology Sdn Bhd",
            "status": "Active",
            "city": "Kuala Lumpur",
            "state": "Kuala Lumpur",
            "industry_id": "Information Technology",
            "logo": "/images/abc.png"
        },
        "COMPANY002": {
            "companyName": "XYZ Solutions",
            "status": "Active",
            "city": "Petaling Jaya",
            "state": "Selangor",
            "industry_id": "Software Development",
            "logo": "/images/xyz.png"
        }
    }

    reviews = {
        # COMPANY001 average = 4.5, review_count = 2
        "REVIEW001": {
            "company_id": "COMPANY001",
            "overall_rating": 4.0
        },
        "REVIEW002": {
            "company_id": "COMPANY001",
            "overall_rating": 5.0
        },

        # COMPANY002 average = 4.5, review_count = 1
        "REVIEW003": {
            "company_id": "COMPANY002",
            "overall_rating": 4.5
        }
    }

    install_fake_db(
        monkeypatch,
        applicants,
        companies,
        {},
        reviews
    )


@then(
    "the company with more reviews should be displayed first"
)
def verify_more_reviews_first(
    context
):

    companies = (
        context.response["context"]
        ["companies"]
    )

    assert len(companies) == 2

    assert (
        companies[0]["rating"]
        == companies[1]["rating"]
        == 4.5
    )

    assert (
        companies[0]["review_count"]
        >
        companies[1]["review_count"]
    )

    assert (
        companies[0]["company_name"]
        == "ABC Technology Sdn Bhd"
    )


@given(
    "fewer than twelve active companies exist"
)
def fewer_twelve(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        create_companies(10),
        {},
        {}
    )


@when(
    "the job seeker views the first company page"
)
def first_company_page(
    context
):

    context.response = browse(
        page=1
    )


@then(
    "only one company page should be required"
)
def verify_one_company_page(
    context
):

    assert (
        context.response["context"]
        ["total_pages"]
        == 1
    )


@given(
    "exactly twelve active companies exist"
)
def exactly_twelve(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        create_companies(12),
        {},
        {}
    )


@when(
    "the job seeker views the company list"
)
def company_list(
    context
):

    context.response = browse()


@given(
    "thirteen active companies exist"
)
def thirteen_companies(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        create_companies(13),
        {},
        {}
    )


@then(
    "two company pages should be required"
)
def verify_two_company_pages(
    context
):

    assert (
        context.response["context"]
        ["total_pages"]
        == 2
    )


@given(
    "more than twelve active companies exist"
)
def more_twelve(
    monkeypatch,
    applicants
):

    install_fake_db(
        monkeypatch,
        applicants,
        create_companies(15),
        {},
        {}
    )


@when(
    "the job seeker opens company page two"
)
def company_page_two(
    context
):

    context.response = browse(
        page=2
    )


@then(
    "the remaining companies should be displayed"
)
def verify_remaining_companies(
    context
):

    assert (
        len(
            context.response["context"]
            ["companies"]
        )
        == 3
    )


@given(
    "no active companies exist"
)
def no_active_companies_bdd(
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


@then(
    "the system should handle the empty company list successfully"
)
def verify_empty_company_list(
    context
):

    assert (
        context.response["context"]
        ["companies"]
        == []
    )

    assert (
        context.response["context"]
        ["total_company"]
        == 0
    )


@given(
    "the logged in applicant profile does not exist"
)
def missing_applicant_bdd(
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


@then(
    "the company page should still be displayed safely"
)
def verify_missing_applicant_safe(
    context
):

    assert (
        context.response["template"]
        == "companyBrowse.html"
    )

    assert (
        context.response["context"]
        ["user"]
        is None
    )