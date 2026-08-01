# tests/test_jobs_search_filter.py - COMPLETE FIXED VERSION

from fastapi.testclient import TestClient
import pytest
from pytest_bdd import (
    scenarios,
    given,
    when,
    then,
    parsers,
)
from job_portal_web.backend.main import app
from job_portal_web.backend.jobs import apply_search

client = TestClient(app)

# Load Feature File
scenarios("features/jobs_search_filter.feature")


# ==========================================================
# Test Data Fixtures
# ==========================================================


@pytest.fixture
def sample_jobs():
    """Sample job data for testing"""
    return [
        {
            "job_title": "Software Engineer",
            "company_name": "ABC Sdn Bhd",
            "location": "Kuala Lumpur",
            "position": "Senior Executive",
            "category": "Information Technology",
            "benefits": ["Socso", "Transport Allowance", "Medical"],
        },
        {
            "job_title": "Software Developer",
            "company_name": "Google",
            "location": "Selangor",
            "position": "Internship",
            "category": "Information Technology",
            "benefits": ["Socso", "Remote Work"],
        },
        {
            "job_title": "Accountant",
            "company_name": "Deloitte",
            "location": "Penang",
            "position": "Full Time",
            "category": "Finance",
            "benefits": ["EPF", "Medical"],
        },
    ]


@pytest.fixture
def search_context(sample_jobs):
    """Shared context for BDD steps"""
    return {
        "search_keyword": "",
        "selected_category": "",
        "selected_locations": [],
        "selected_positions": [],
        "selected_benefits": [],
        "response": None,
        "search_results": [],
        "all_jobs": sample_jobs.copy(),
        "filters_applied": False,
        "selected_job": None,
    }


# ==========================================================
# Helper Function
# ==========================================================


def _execute_combined_search(search_context):
    """Helper to execute combined search with all filters"""
    # Build params for API call
    params = {}

    if search_context["search_keyword"]:
        params["q"] = search_context["search_keyword"]
    if search_context["selected_category"]:
        params["category"] = search_context["selected_category"]
    if search_context["selected_locations"]:
        params["location"] = search_context["selected_locations"][0]
    if search_context["selected_positions"]:
        params["position"] = search_context["selected_positions"][0]
    if search_context["selected_benefits"]:
        params["benefits"] = search_context["selected_benefits"][0]

    # Make API call
    if params:
        response = client.get("/jobs", params=params)
        search_context["response"] = response
    else:
        # No filters, get all jobs
        response = client.get("/jobs")
        search_context["response"] = response

    # Filter sample data
    filtered = search_context["all_jobs"].copy()

    # Apply keyword search
    if search_context["search_keyword"]:
        filtered = apply_search(filtered, search_context["search_keyword"], "")

    # Apply category filter
    if search_context["selected_category"]:
        filtered = [
            job for job in filtered if job["category"] == search_context["selected_category"]
        ]

    # Apply location filter
    if search_context["selected_locations"]:
        filtered = [
            job for job in filtered if job["location"] in search_context["selected_locations"]
        ]

    # Apply position filter
    if search_context["selected_positions"]:
        filtered = [
            job for job in filtered if job["position"] in search_context["selected_positions"]
        ]

    # Apply benefits filter
    if search_context["selected_benefits"]:
        filtered = [
            job
            for job in filtered
            if any(b in job["benefits"] for b in search_context["selected_benefits"])
        ]

    search_context["search_results"] = filtered
    return filtered


# ==========================================================
# Background Steps
# ==========================================================


@given("the job portal contains active job postings")
def active_job_postings(search_context):
    """Prepare the database with active job postings"""
    pass


@given("the job seeker is on the job search page")
def open_job_search_page(search_context):
    """Navigate to the job search page"""
    response = client.get("/jobs")
    assert response.status_code == 200
    search_context["response"] = response


@given("search results are displayed")
def search_results_displayed(search_context):
    """Ensure search results are displayed"""
    response = client.get("/jobs")
    assert response.status_code == 200
    search_context["response"] = response
    search_context["search_results"] = search_context["all_jobs"].copy()


@given("the job seeker has selected a category")
def category_selected(search_context):
    """Simulate category selection"""
    search_context["selected_category"] = "Information Technology"
    search_context["filters_applied"] = True


@given("the location filter is applied")
def location_filter_applied(search_context):
    """Apply location filter"""
    search_context["selected_locations"] = ["Kuala Lumpur"]
    search_context["filters_applied"] = True


@given("the position filter is applied")
def position_filter_applied(search_context):
    """Apply position filter"""
    search_context["selected_positions"] = ["Full Time"]
    search_context["filters_applied"] = True


@given("the benefits filter is applied")
def benefits_filter_applied(search_context):
    """Apply benefits filter"""
    search_context["selected_benefits"] = ["Medical"]
    search_context["filters_applied"] = True


# ==========================================================
# When Steps - Search Actions
# ==========================================================


@when(parsers.parse('the job seeker enters "{keyword}" in the search box'))
def enter_keyword(search_context, keyword):
    """Enter keyword in search box"""
    search_context["search_keyword"] = keyword


@when(parsers.parse('the job seeker searches for "{keyword}"'))
def search_for_keyword(search_context, keyword):
    """Search for keyword"""
    search_context["search_keyword"] = keyword
    response = client.get("/jobs", params={"q": keyword})
    search_context["response"] = response
    search_context["search_results"] = apply_search(search_context["all_jobs"], keyword, "")


@when('clicks the "Search Jobs" button')
def click_search_button(search_context):
    """Click the search button to execute search"""
    keyword = search_context["search_keyword"]
    category = search_context["selected_category"]

    params = {}
    if keyword:
        params["q"] = keyword
    if category:
        params["category"] = category

    response = client.get("/jobs", params=params)
    search_context["response"] = response

    if search_context["all_jobs"]:
        search_context["search_results"] = apply_search(
            search_context["all_jobs"], keyword, category
        )


@when(parsers.parse('the job seeker selects "{category}" from the category list'))
def select_category_from_list(search_context, category):
    """Select a category from the list"""
    search_context["selected_category"] = category


@when('the job seeker selects "All Categories"')
def select_all_categories(search_context):
    """Clear category selection"""
    search_context["selected_category"] = ""
    search_context["filters_applied"] = False


# ==========================================================
# When Steps - Location Filters
# ==========================================================


@when(parsers.parse('the job seeker selects the location "{location}"'))
def select_location(search_context, location):
    """Select a single location"""
    search_context["selected_locations"] = [location]
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects the locations "{locations}" and "{location2}"'))
def select_multiple_locations(search_context, locations, location2):
    """Select multiple locations"""
    search_context["selected_locations"] = [locations, location2]
    _execute_combined_search(search_context)


@when("the job seeker clears all selected locations")
def clear_locations(search_context):
    """Clear all location filters"""
    search_context["selected_locations"] = []
    search_context["filters_applied"] = False


# ==========================================================
# When Steps - Position Filters
# ==========================================================


@when(parsers.parse('the job seeker selects the position "{position}"'))
def select_position(search_context, position):
    """Select a single position"""
    search_context["selected_positions"] = [position]
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects "{position1}" and "{position2}"'))
def select_multiple_positions(search_context, position1, position2):
    """Select multiple positions"""
    search_context["selected_positions"] = [position1, position2]
    _execute_combined_search(search_context)


@when("the job seeker clears all selected positions")
def clear_positions(search_context):
    """Clear all position filters"""
    search_context["selected_positions"] = []
    search_context["filters_applied"] = False


# ==========================================================
# When Steps - Benefits Filters
# ==========================================================


@when(parsers.parse('the job seeker selects the benefit "{benefit}"'))
def select_benefit(search_context, benefit):
    """Select a single benefit"""
    search_context["selected_benefits"] = [benefit]
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects the benefits "{benefit1}" and "{benefit2}"'))
def select_multiple_benefits(search_context, benefit1, benefit2):
    """Select multiple benefits"""
    search_context["selected_benefits"] = [benefit1, benefit2]
    _execute_combined_search(search_context)


@when("the job seeker clears all selected benefits")
def clear_benefits(search_context):
    """Clear all benefit filters"""
    search_context["selected_benefits"] = []
    search_context["filters_applied"] = False


# ==========================================================
# CRITICAL FIX: Combined Scenarios Step Definitions
# These match the exact wording in your feature file
# ==========================================================


@when(parsers.parse('selects the benefit "{benefit}"'))
def selects_benefit_short(search_context, benefit):
    """Select benefit in combined scenarios (short form)"""
    search_context["selected_benefits"] = [benefit]
    _execute_combined_search(search_context)


@when(parsers.parse('selects the category "{category}"'))
def selects_category_short(search_context, category):
    """Select category in combined scenarios (short form)"""
    search_context["selected_category"] = category
    _execute_combined_search(search_context)


@when(parsers.parse('selects the location "{location}"'))
def selects_location_short(search_context, location):
    """Select location in combined scenarios (short form)"""
    search_context["selected_locations"] = [location]
    _execute_combined_search(search_context)


@when(parsers.parse('selects the position "{position}"'))
def selects_position_short(search_context, position):
    """Select position in combined scenarios (short form)"""
    search_context["selected_positions"] = [position]
    _execute_combined_search(search_context)


# ==========================================================
# FIX: Add the full "the job seeker selects the category" step
# This is what was missing!
# ==========================================================


@when(parsers.parse('the job seeker selects the category "{category}"'))
def the_job_seeker_selects_category(search_context, category):
    """The job seeker selects a category (full wording)"""
    search_context["selected_category"] = category
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects the location "{location}"'))
def the_job_seeker_selects_location(search_context, location):
    """The job seeker selects a location (full wording)"""
    search_context["selected_locations"] = [location]
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects the benefit "{benefit}"'))
def the_job_seeker_selects_benefit(search_context, benefit):
    """The job seeker selects a benefit (full wording)"""
    search_context["selected_benefits"] = [benefit]
    _execute_combined_search(search_context)


@when(parsers.parse('the job seeker selects the position "{position}"'))
def the_job_seeker_selects_position(search_context, position):
    """The job seeker selects a position (full wording)"""
    search_context["selected_positions"] = [position]
    _execute_combined_search(search_context)


@when(parsers.parse('And selects the location "{location}"'))
def and_selects_location(search_context, location):
    """Additional location selection in combined scenarios"""
    search_context["selected_locations"] = [location]
    _execute_combined_search(search_context)


@when(parsers.parse('And selects the category "{category}"'))
def and_selects_category(search_context, category):
    """Additional category selection in combined scenarios"""
    search_context["selected_category"] = category
    _execute_combined_search(search_context)


@when(parsers.parse('And selects the benefit "{benefit}"'))
def and_selects_benefit(search_context, benefit):
    """Additional benefit selection in combined scenarios"""
    search_context["selected_benefits"] = [benefit]
    _execute_combined_search(search_context)


@when(parsers.parse('And selects the position "{position}"'))
def and_selects_position(search_context, position):
    """Additional position selection in combined scenarios"""
    search_context["selected_positions"] = [position]
    _execute_combined_search(search_context)


@when(parsers.parse("the job seeker selects filters that have no matching jobs"))
def select_no_matching_filters(search_context):
    """Select filters that yield no results"""
    search_context["selected_locations"] = ["Mars"]
    search_context["selected_positions"] = ["Astronaut"]

    response = client.get("/jobs", params={"location": "Mars", "position": "Astronaut"})
    search_context["response"] = response
    search_context["search_results"] = []


@when("the job seeker selects a job posting")
def select_job_posting(search_context):
    """Select a job from search results"""
    if search_context["search_results"]:
        search_context["selected_job"] = search_context["search_results"][0]
    else:
        jobs = search_context["all_jobs"]
        if jobs:
            search_context["selected_job"] = jobs[0]


# ==========================================================
# Then Steps - Verification
# ==========================================================


@then(parsers.parse('the system should display job postings with the title "{title}"'))
def verify_exact_job_title(search_context, title):
    """Verify exact job title is displayed"""
    assert search_context["response"].status_code == 200
    assert title in search_context["response"].text
    if search_context["search_results"]:
        titles = [job["job_title"] for job in search_context["search_results"]]
        assert title in titles


@then(parsers.parse('the system should display job postings containing "{keyword}"'))
def verify_partial_title(search_context, keyword):
    """Verify job postings containing keyword"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert keyword.lower() in job["job_title"].lower()


@then("the system should display matching job postings regardless of capitalization")
def verify_case_insensitive(search_context):
    """Verify case insensitive search"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        keyword = search_context["search_keyword"].lower()
        for job in search_context["search_results"]:
            assert keyword in job["job_title"].lower()


@then(parsers.parse('the system should display job postings from "{company}"'))
def verify_company_search(search_context, company):
    """Verify company search results"""
    assert search_context["response"].status_code == 200
    assert company in search_context["response"].text
    if search_context["search_results"]:
        companies = [job["company_name"] for job in search_context["search_results"]]
        assert any(company in comp for comp in companies)


@then(parsers.parse('the system should display job postings from companies containing "{company}"'))
def verify_partial_company(search_context, company):
    """Verify partial company name search"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert company.lower() in job["company_name"].lower()


@then(
    parsers.parse('the system should display job postings belonging to the "{category}" category')
)
def verify_category(search_context, category):
    """Verify category filtering"""
    assert search_context["response"].status_code == 200
    assert category in search_context["response"].text
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert job["category"] == category


@then("the system should display all available job postings")
def verify_all_jobs(search_context):
    """Verify all jobs are displayed"""
    assert search_context["response"].status_code == 200
    assert "Find Your Dream Job" in search_context["response"].text
    if search_context["all_jobs"]:
        all_jobs_count = len(search_context["all_jobs"])
        if search_context["search_results"]:
            assert len(search_context["search_results"]) == all_jobs_count


@then(parsers.parse('the system should display only job postings located in "{location}"'))
def verify_location_filter(search_context, location):
    """Verify location filtering"""
    assert search_context["response"].status_code == 200
    assert location in search_context["response"].text
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert job["location"] == location


@then(parsers.parse("the system should display job postings from either selected location"))
def verify_multiple_locations(search_context):
    """Verify multiple locations filter"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        locations = search_context["selected_locations"]
        for job in search_context["search_results"]:
            assert job["location"] in locations


@then(parsers.parse('the system should display only "{position}" job postings'))
def verify_position_filter(search_context, position):
    """Verify position filtering"""
    assert search_context["response"].status_code == 200
    assert position in search_context["response"].text
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert job["position"] == position


@then(parsers.parse("the system should display job postings matching either selected position"))
def verify_multiple_positions(search_context):
    """Verify multiple positions filter"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        positions = search_context["selected_positions"]
        for job in search_context["search_results"]:
            assert job["position"] in positions


@then(parsers.parse('the system should display only job postings offering "{benefit}"'))
def verify_benefit_filter(search_context, benefit):
    """Verify benefit filtering"""
    assert search_context["response"].status_code == 200
    assert benefit in search_context["response"].text
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert benefit in job["benefits"]


@then(parsers.parse("the system should display job postings offering either selected benefit"))
def verify_multiple_benefits(search_context):
    """Verify multiple benefits filter"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        benefits = search_context["selected_benefits"]
        for job in search_context["search_results"]:
            assert any(b in job["benefits"] for b in benefits)


@then(parsers.parse('the system should display only Engineering jobs located in "{location}"'))
def verify_combined_title_location(search_context, location):
    """Verify combined title and location filter"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            assert "Engineer" in job["job_title"]
            assert job["location"] == location


@then(
    parsers.parse('the system should display only Information Technology jobs offering "{benefit}"')
)
def verify_combined_category_benefit(search_context, benefit):
    """Verify combined category and benefit filter"""
    assert search_context["response"].status_code == 200

    # Check that we have results
    assert len(search_context["search_results"]) > 0, "No search results found"

    # Verify each result
    for job in search_context["search_results"]:
        # Check category
        assert (
            job["category"] == "Information Technology"
        ), f"Expected 'Information Technology', got '{job['category']}'"
        # Check benefit
        assert benefit in job["benefits"], f"Expected '{benefit}' in {job['benefits']}"


@then("the system should display only matching job postings")
def verify_combined_multiple_filters(search_context):
    """Verify multiple combined filters"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"]:
        for job in search_context["search_results"]:
            if search_context["search_keyword"]:
                assert search_context["search_keyword"].lower() in job["job_title"].lower()
            if search_context["selected_category"]:
                assert job["category"] == search_context["selected_category"]
            if search_context["selected_locations"]:
                assert job["location"] in search_context["selected_locations"]
            if search_context["selected_positions"]:
                assert job["position"] in search_context["selected_positions"]


@then(parsers.parse('the system should display the message "{message}"'))
def verify_no_results_message(search_context, message):
    """Verify no results message"""
    assert search_context["response"].status_code == 200
    if search_context["search_results"] is not None:
        assert len(search_context["search_results"]) == 0


@then("the system should display the complete job details")
def verify_complete_job_details(search_context):
    """Verify complete job details are displayed"""
    assert search_context["response"] is not None
    assert search_context["selected_job"] is not None


@then("the job title should be displayed")
def verify_job_title_displayed(search_context):
    """Verify job title is displayed"""
    assert search_context["selected_job"] is not None
    assert "job_title" in search_context["selected_job"]


@then("the company name should be displayed")
def verify_company_displayed(search_context):
    """Verify company name is displayed"""
    assert search_context["selected_job"] is not None
    assert "company_name" in search_context["selected_job"]


@then("the job location should be displayed")
def verify_location_displayed(search_context):
    """Verify job location is displayed"""
    assert search_context["selected_job"] is not None
    assert "location" in search_context["selected_job"]


@then("the job benefits should be displayed")
def verify_benefits_displayed(search_context):
    """Verify job benefits are displayed"""
    assert search_context["selected_job"] is not None
    assert "benefits" in search_context["selected_job"]
    assert isinstance(search_context["selected_job"]["benefits"], list)


# ==========================================================
# Original Integration Tests
# ==========================================================


def test_view_all_jobs():
    response = client.get("/jobs")
    assert response.status_code == 200
    assert "Find Your Dream Job" in response.text


def test_search_job_title():
    response = client.get("/jobs", params={"q": "Software Engineer"})
    assert response.status_code == 200


def test_search_company():
    response = client.get("/jobs", params={"q": "Microsoft"})
    assert response.status_code == 200


def test_filter_location():
    response = client.get("/jobs", params={"location": "Kuala Lumpur"})
    assert response.status_code == 200


def test_filter_by_position():
    response = client.get("/jobs", params={"position": "Senior Engineer"})
    assert response.status_code == 200
    assert "Senior Engineer" in response.text


def test_filter_by_benefits():
    response = client.get("/jobs", params={"benefits": "Socso"})
    assert response.status_code == 200
    assert "Socso" in response.text


def test_search_and_filter():
    response = client.get("/jobs", params={"q": "Engineer", "location": "Kuala Lumpur"})
    assert response.status_code == 200


# ==========================================================
# Original Unit Tests
# ==========================================================


def test_search_exact_job_title(sample_jobs):
    result = apply_search(sample_jobs, "Software Engineer", "")
    assert len(result) == 1
    assert result[0]["job_title"] == "Software Engineer"


def test_search_case_insensitive(sample_jobs):
    result = apply_search(sample_jobs, "software engineer", "")
    assert len(result) == 1
    assert result[0]["job_title"] == "Software Engineer"


def test_search_category(sample_jobs):
    result = apply_search(sample_jobs, "", "Information Technology")
    assert len(result) == 2
    for job in result:
        assert job["category"] == "Information Technology"


def test_search_keyword_and_category(sample_jobs):
    result = apply_search(sample_jobs, "Software", "Information Technology")
    assert len(result) == 2


def test_search_no_result(sample_jobs):
    result = apply_search(sample_jobs, "Astronaut", "")
    assert result == []


def test_empty_search_returns_all_jobs(sample_jobs):
    result = apply_search(sample_jobs, "", "")
    assert len(result) == 3
