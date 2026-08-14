from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("features/search_saved_posts.feature")


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAVED_POSTS_TEMPLATE = PROJECT_ROOT / "src" / "job_portal_web" / "ui" / "savedCareerAdvice.html"


def read_template() -> str:
    assert SAVED_POSTS_TEMPLATE.exists(), f"Template not found: {SAVED_POSTS_TEMPLATE}"

    return SAVED_POSTS_TEMPLATE.read_text(
        encoding="utf-8",
        errors="ignore",
    )


@pytest.fixture
def context():
    return {}


@given("the job seeker is viewing the saved posts page")
def viewing_saved_posts_page(context):
    template = read_template()

    assert 'id="savedPostSearch"' in template
    assert 'id="savedPostGrid"' in template

    context["template"] = template


@given("the job seeker has entered a keyword in the saved post search field")
def keyword_entered(context):
    template = read_template()

    assert 'id="savedPostSearch"' in template
    assert "filterSavedPosts()" in template

    context["template"] = template


@when("the job seeker enters a post title in the search field")
def search_by_title(context):
    template = context["template"]

    context["searches_title"] = "card.dataset.title" in template

    context["uses_includes"] = "includes(keyword)" in template


@when("the job seeker enters a summary keyword in the search field")
def search_by_summary(context):
    template = context["template"]

    context["searches_summary"] = "card.dataset.summary" in template

    context["uses_includes"] = "includes(keyword)" in template


@when("the job seeker enters a keyword that does not match any saved post")
def search_no_matching_post(context):
    template = context["template"]

    context["has_no_results"] = (
        'id="savedPostNoResults"' in template and "No matching posts" in template
    )


@when("the job seeker clears the search field")
def clear_search(context):
    template = context["template"]

    context["has_clear_function"] = "function clearSavedPostFilters()" in template

    context["clears_search"] = 'getElementById("savedPostSearch").value = ""' in template


@then("the system should display saved posts that match the entered title")
def display_matching_titles(context):
    assert context["searches_title"]
    assert context["uses_includes"]


@then("the system should display saved posts containing the entered keyword")
def display_matching_summaries(context):
    assert context["searches_summary"]
    assert context["uses_includes"]


@then("the system should display a message indicating that no matching posts were found")
def display_no_matching_posts(context):
    assert context["has_no_results"]


@then("the system should display all saved Career Advice posts")
def display_all_saved_posts(context):
    assert context["has_clear_function"]
    assert context["clears_search"]
