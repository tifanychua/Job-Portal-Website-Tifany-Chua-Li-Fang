import asyncio
import importlib
from pathlib import Path

import pytest
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

# ============================================================
# LOAD COMPANY BROWSE MODULE SAFELY
# ============================================================


def load_company_module():

    routes_dir = Path("src/job_portal_web/backend/routes")

    for path in routes_dir.glob("*.py"):

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if "def browse_companies(" in text and '"/companies"' in text:

            import firebase_admin.firestore as firestore_module

            original_client = firestore_module.client

            # Prevent real Firebase connection during import
            firestore_module.client = lambda: None

            try:

                module_name = "job_portal_web.backend.routes." + path.stem

                return importlib.import_module(module_name)

            finally:

                firestore_module.client = original_client

    raise ImportError("Could not find browse_companies route.")


company_module = load_company_module()


scenarios("features/searchCompanies.feature")


# ============================================================
# CONSTANTS
# ============================================================

APPLICANT_ID = "0YLcc18JszVqSXWn8DEDQ81o2vR2"


# ============================================================
# FAKE REQUEST
# ============================================================


class FakeRequest:

    def __init__(self):

        self.session = {
            "user_type": "job_seeker",
            "applicant_id": APPLICANT_ID,
        }


# ============================================================
# FAKE FIRESTORE DOCUMENT
# ============================================================


class FakeDocument:

    def __init__(
        self,
        document_id,
        data,
        exists=True,
    ):

        self.id = document_id
        self._data = data
        self.exists = exists

    def to_dict(self):

        return self._data


# ============================================================
# FAKE DOCUMENT REFERENCE
# ============================================================


class FakeDocumentReference:

    def __init__(
        self,
        database,
        collection_name,
        document_id,
    ):

        self.database = database
        self.collection_name = collection_name
        self.document_id = document_id

    def get(self):

        collection = self.database.data.get(self.collection_name, {})

        data = collection.get(self.document_id)

        if data is None:

            return FakeDocument(
                self.document_id,
                None,
                exists=False,
            )

        return FakeDocument(
            self.document_id,
            data,
            exists=True,
        )


# ============================================================
# FAKE FIRESTORE QUERY
# ============================================================


class FakeQuery:

    def __init__(
        self,
        database,
        collection_name,
        filters=None,
    ):

        self.database = database
        self.collection_name = collection_name
        self.filters = filters or []

    def where(
        self,
        field=None,
        operator=None,
        value=None,
        **kwargs,
    ):

        # Support:
        # .where("status", "==", "Active")

        new_filters = list(self.filters)

        if field is not None:

            new_filters.append(
                (
                    field,
                    operator,
                    value,
                )
            )

        return FakeQuery(
            self.database,
            self.collection_name,
            new_filters,
        )

    def stream(self):

        collection = self.database.data.get(self.collection_name, {})

        results = []

        for document_id, data in collection.items():

            include = True

            for (
                field,
                operator,
                value,
            ) in self.filters:

                if operator == "==":

                    if data.get(field) != value:

                        include = False
                        break

            if include:

                results.append(
                    FakeDocument(
                        document_id,
                        data,
                    )
                )

        return results


# ============================================================
# FAKE COLLECTION
# ============================================================


class FakeCollection:

    def __init__(
        self,
        database,
        collection_name,
    ):

        self.database = database
        self.collection_name = collection_name

    def document(
        self,
        document_id,
    ):

        return FakeDocumentReference(
            self.database,
            self.collection_name,
            document_id,
        )

    def where(
        self,
        field=None,
        operator=None,
        value=None,
        **kwargs,
    ):

        query = FakeQuery(
            self.database,
            self.collection_name,
        )

        return query.where(
            field,
            operator,
            value,
            **kwargs,
        )

    def stream(self):

        return FakeQuery(
            self.database,
            self.collection_name,
        ).stream()


# ============================================================
# FAKE FIRESTORE
# ============================================================


class FakeFirestore:

    def __init__(self):

        self.data = {
            "job_seeker": {},
            "company": {},
            "job_list": {},
            "company_review": {},
        }

    def collection(
        self,
        collection_name,
    ):

        return FakeCollection(
            self,
            collection_name,
        )


# ============================================================
# CONTEXT
# ============================================================


class Context:

    def __init__(self):

        self.db = FakeFirestore()

        self.response = None

        self.selected_company = None


@pytest.fixture
def context():

    return Context()


# ============================================================
# TEMPLATE MOCK
# ============================================================


@pytest.fixture(autouse=True)
def setup_test(
    monkeypatch,
    context,
):

    # --------------------------------------------------------
    # Mock DB
    # --------------------------------------------------------

    monkeypatch.setattr(
        company_module,
        "db",
        context.db,
    )

    # --------------------------------------------------------
    # Mock authentication
    # --------------------------------------------------------

    monkeypatch.setattr(
        company_module,
        "get_current_applicant_id",
        lambda request: APPLICANT_ID,
    )

    # --------------------------------------------------------
    # Mock TemplateResponse
    # --------------------------------------------------------

    def fake_template_response(
        *args,
        **kwargs,
    ):

        return {
            "template": kwargs.get("name"),
            "context": kwargs.get("context"),
        }

    monkeypatch.setattr(
        company_module.templates,
        "TemplateResponse",
        fake_template_response,
    )

    # --------------------------------------------------------
    # Applicant
    # --------------------------------------------------------

    context.db.data["job_seeker"][APPLICANT_ID] = {
        "uid": APPLICANT_ID,
        "full_name": "Test Job Seeker",
        "email": "jobseeker@example.com",
    }

    # --------------------------------------------------------
    # Active Companies
    # --------------------------------------------------------

    context.db.data["company"]["company001"] = {
        "companyName": "ABC Technology Sdn. Bhd.",
        "companyDescription": "Software and technology company",
        "industry_id": "Technology",
        "city": "Kuala Lumpur",
        "state": "Kuala Lumpur",
        "logo": "/images/abc.png",
        "status": "Active",
    }

    context.db.data["company"]["company002"] = {
        "companyName": "Global Finance Berhad",
        "companyDescription": "Financial services company",
        "industry_id": "Finance",
        "city": "Petaling Jaya",
        "state": "Selangor",
        "logo": "/images/global.png",
        "status": "Active",
    }

    context.db.data["company"]["company003"] = {
        "companyName": "Tech Solutions Malaysia",
        "companyDescription": "Business technology solutions",
        "industry_id": "Technology",
        "city": "Cyberjaya",
        "state": "Selangor",
        "logo": "/images/tech.png",
        "status": "Active",
    }

    # --------------------------------------------------------
    # Inactive Company
    # --------------------------------------------------------

    context.db.data["company"]["company004"] = {
        "companyName": "Inactive Technology Company",
        "companyDescription": "Inactive company",
        "industry_id": "Technology",
        "city": "Kuala Lumpur",
        "state": "Kuala Lumpur",
        "status": "Inactive",
    }

    # --------------------------------------------------------
    # Jobs
    # --------------------------------------------------------

    context.db.data["job_list"]["job001"] = {
        "company_id": "company001",
        "job_title": "Software Engineer",
        "status": "Active",
    }

    context.db.data["job_list"]["job002"] = {
        "company_id": "company001",
        "job_title": "Web Developer",
        "status": "Active",
    }

    context.db.data["job_list"]["job003"] = {
        "company_id": "company002",
        "job_title": "Finance Executive",
        "status": "Active",
    }

    context.db.data["job_list"]["job004"] = {
        "company_id": "company003",
        "job_title": "System Analyst",
        "status": "Active",
    }

    # Deleted job must NOT count
    context.db.data["job_list"]["job005"] = {
        "company_id": "company001",
        "job_title": "Old Developer Position",
        "status": "Deleted",
    }

    # --------------------------------------------------------
    # Reviews
    # --------------------------------------------------------

    context.db.data["company_review"]["review001"] = {
        "company_id": "company001",
        "overall_rating": 5,
    }

    context.db.data["company_review"]["review002"] = {
        "company_id": "company001",
        "overall_rating": 4,
    }


# ============================================================
# HELPER
# ============================================================


def search(
    context,
    keyword="",
):

    context.response = asyncio.run(
        company_module.browse_companies(
            FakeRequest(),
            keyword=keyword,
            page=1,
        )
    )

    return context.response


def companies_from_response(
    context,
):

    return context.response["context"]["companies"]


# ============================================================
# GIVEN
# ============================================================


@given("the job seeker is viewing the company search section")
def viewing_company_search(
    context,
):

    search(
        context,
        "",
    )


@given("the job seeker has received company search results")
def received_search_results(
    context,
):

    search(
        context,
        "ABC",
    )

    assert len(companies_from_response(context)) > 0


@given("multiple active companies exist")
def multiple_companies_exist(
    context,
):

    assert len(context.db.data["company"]) >= 3


@given("an inactive company matches the search keyword")
def inactive_company_exists(
    context,
):

    company = context.db.data["company"]["company004"]

    assert company["status"] == "Inactive"


@given("the job seeker has entered a company name or keyword")
def search_criteria_entered(
    context,
):

    search(
        context,
        "ABC",
    )


@given("no companies match the current search")
def no_companies_match(
    context,
):

    search(
        context,
        "CompanyThatDoesNotExist12345",
    )

    assert len(companies_from_response(context)) == 0


@given("the job seeker has entered search criteria")
def entered_search_criteria(
    context,
):

    search(
        context,
        "Technology",
    )


# ============================================================
# WHEN
# ============================================================


@when('the job seeker searches for company name "ABC Technology"')
def search_company_name(
    context,
):

    search(
        context,
        "ABC Technology",
    )


@when('the job seeker searches for keyword "Technology"')
def search_industry_keyword(
    context,
):

    search(
        context,
        "Technology",
    )


@when('the job seeker searches for location "Kuala Lumpur"')
def search_location(
    context,
):

    search(
        context,
        "Kuala Lumpur",
    )


@when("the job seeker searches using lowercase company name")
def search_lowercase(
    context,
):

    search(
        context,
        "abc technology",
    )


@when("the job seeker searches using a partial company name")
def search_partial_name(
    context,
):

    search(
        context,
        "ABC Tech",
    )


@when('the job seeker searches for "Technology"')
def search_technology(
    context,
):

    search(
        context,
        "Technology",
    )


@when("the job seeker searches for that company")
def search_inactive(
    context,
):

    search(
        context,
        "Inactive Technology Company",
    )


@when("the job seeker selects a company from the search results")
def select_company(
    context,
):

    companies = companies_from_response(context)

    assert companies

    context.selected_company = companies[0]


@when("the matching company is displayed")
def matching_company_displayed(
    context,
):

    companies = companies_from_response(context)

    assert companies


@when("no companies match the search criteria")
def search_no_match(
    context,
):

    search(
        context,
        "ZZZ_NON_EXISTENT_COMPANY",
    )


@when("the company search page is rendered")
def search_page_rendered(
    context,
):

    assert context.response["template"] == "companyBrowse.html"


@when("the job seeker clears the search field")
def clear_search(
    context,
):

    search(
        context,
        "",
    )


@when("the job seeker searches with spaces around the keyword")
def search_spaces(
    context,
):

    search(
        context,
        "   Technology   ",
    )


@when("the job seeker submits an empty search")
def empty_search(
    context,
):

    search(
        context,
        "",
    )


@when("the company search result is prepared")
def result_prepared(
    context,
):

    assert companies_from_response(context)


# ============================================================
# THEN
# ============================================================


@then("the system should display companies that match the entered company name")
def company_name_matches(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) == 1

    assert companies[0]["company_name"] == "ABC Technology Sdn. Bhd."


@then("the system should display companies that match the entered keyword")
def keyword_matches(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) == 2

    for company in companies:

        assert (
            "technology" in company["industry"].lower()
            or "technology" in company["company_name"].lower()
        )


@then("the system should display companies located in Kuala Lumpur")
def location_matches(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) >= 1

    for company in companies:

        assert "kuala lumpur" in company["location"].lower()


@then("the matching company should still be displayed")
def lowercase_match(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) == 1

    assert companies[0]["company_name"] == "ABC Technology Sdn. Bhd."


@then("companies containing the partial company name should be displayed")
def partial_match(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) == 1

    assert "ABC Technology" in companies[0]["company_name"]


@then("companies unrelated to the search keyword should not be displayed")
def unrelated_not_displayed(
    context,
):

    companies = companies_from_response(context)

    names = [company["company_name"] for company in companies]

    assert "Global Finance Berhad" not in names

    assert "ABC Technology Sdn. Bhd." in names

    assert "Tech Solutions Malaysia" in names


@then("the inactive company should not be displayed")
def inactive_not_displayed(
    context,
):

    companies = companies_from_response(context)

    assert len(companies) == 0


@then("the system should provide access to the selected company's details")
def company_details_access(
    context,
):

    assert context.selected_company is not None

    assert context.selected_company["id"] == "company001"

    expected_url = f"/company/" f"{context.selected_company['id']}"

    assert expected_url == "/company/company001"


@then("the search result should contain company name industry location and available job count")
def company_information_available(
    context,
):

    company = companies_from_response(context)[0]

    assert "company_name" in company

    assert "industry" in company

    assert "location" in company

    assert "job_count" in company

    assert company["company_name"] == "ABC Technology Sdn. Bhd."

    assert company["industry"] == "Technology"

    assert "Kuala Lumpur" in company["location"]

    # Only Active jobs:
    # Software Engineer
    # Web Developer
    assert company["job_count"] == 2


@then("the system should return an empty company result")
def empty_result(
    context,
):

    companies = companies_from_response(context)

    assert companies == []

    assert context.response["context"]["total_company"] == 0


@then("the page should have no company cards available")
def no_company_cards(
    context,
):

    companies = companies_from_response(context)

    assert companies == []


@then("the system should display the default company listing")
def default_listing(
    context,
):

    response_context = context.response["context"]

    companies = response_context["companies"]

    # 3 active companies.
    # company004 is inactive.
    assert len(companies) == 3

    assert response_context["keyword"] == ""

    names = {company["company_name"] for company in companies}

    assert names == {
        "ABC Technology Sdn. Bhd.",
        "Global Finance Berhad",
        "Tech Solutions Malaysia",
    }


@then("the spaces should be ignored when searching")
def spaces_ignored(
    context,
):

    response_context = context.response["context"]

    assert response_context["keyword"] == "technology"

    companies = response_context["companies"]

    assert len(companies) == 2


@then("each company result should contain its company ID")
def result_has_company_id(
    context,
):

    companies = companies_from_response(context)

    assert companies

    for company in companies:

        assert "id" in company

        assert company["id"] is not None

        assert company["id"] != ""
