from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("features/filter_saved_posts.feature")


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

    assert 'id="savedPostCategory"' in template

    context["template"] = template


@given("the job seeker has filtered the saved posts by category")
def category_filter_applied(context):
    template = read_template()

    assert 'id="savedPostCategory"' in template
    assert "filterSavedPosts()" in template

    context["template"] = template


@when("the job seeker selects a Career Advice category")
def select_category(context):
    template = context["template"]

    context["has_category_filter"] = 'id="savedPostCategory"' in template

    context["checks_category"] = "card.dataset.category === category" in template


@when("the job seeker selects a category that has no matching saved posts")
def select_category_without_posts(context):
    template = context["template"]

    context["checks_visible_count"] = "visibleCount === 0" in template

    context["has_no_results"] = (
        'id="savedPostNoResults"' in template and "No matching posts" in template
    )


@when("the job seeker selects all categories")
def select_all_categories(context):
    template = context["template"]

    context["has_all_option"] = '<option value="all">All categories</option>' in template

    context["supports_all_categories"] = 'category === "all"' in template


@then("the system should display only saved posts that belong to the selected category")
def display_selected_category_posts(context):
    assert context["has_category_filter"]
    assert context["checks_category"]


@then("the system should display a message indicating that no matching posts were found")
def display_no_matching_posts(context):
    assert context["checks_visible_count"]
    assert context["has_no_results"]


@then("the system should display saved posts from every category")
def display_posts_from_all_categories(context):
    assert context["has_all_option"]
    assert context["supports_all_categories"]
