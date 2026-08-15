from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("features/view_saved_posts.feature")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "src" / "job_portal_web" / "backend"

CAREER_ADVICE_FILE = BACKEND_DIR / "career_advice.py"
UI_DIRECTORY = PROJECT_ROOT / "src" / "job_portal_web" / "ui"

SAVED_POSTS_TEMPLATE = UI_DIRECTORY / "savedCareerAdvice.html"


def read_file(path: Path) -> str:
    assert path.exists(), f"Required file not found: {path}"
    return path.read_text(encoding="utf-8", errors="ignore")


@pytest.fixture
def context():
    return {}


@given("the job seeker is logged into the system")
def job_seeker_logged_in(context):
    source = read_file(CAREER_ADVICE_FILE)

    assert "job_seeker_id(request)" in source
    assert 'RedirectResponse("/login"' in source

    context["logged_in"] = True


@given("the job seeker has saved Career Advice posts")
def job_seeker_has_saved_posts(context):
    source = read_file(CAREER_ADVICE_FILE)

    assert "SAVED_COLLECTION_NAME" in source
    assert '"saved_career_advice"' in source

    context["has_posts"] = True


@given("the job seeker is viewing the saved posts page")
def viewing_saved_posts_page(context):
    template = read_file(SAVED_POSTS_TEMPLATE)

    assert 'id="savedPostGrid"' in template

    context["template"] = template


@given("the job seeker has not saved any Career Advice posts")
def job_seeker_has_no_saved_posts(context):
    template = read_file(SAVED_POSTS_TEMPLATE)

    assert 'id="savedPostEmpty"' in template

    context["template"] = template


@when("the job seeker accesses the saved posts page")
def access_saved_posts_page(context):
    source = read_file(CAREER_ADVICE_FILE)
    template = read_file(SAVED_POSTS_TEMPLATE)

    context["route_exists"] = '@router.get("/saved-posts"' in source

    context["template"] = template


@when("the saved Career Advice posts are displayed")
def saved_posts_displayed(context):
    context["template"] = read_file(SAVED_POSTS_TEMPLATE)


@when("the job seeker selects a saved Career Advice post")
def select_saved_post(context):
    template = read_file(SAVED_POSTS_TEMPLATE)

    context["has_article_link"] = "/job-seeker/career-advice/{{ post.id }}" in template


@then("the system should display all Career Advice posts saved by the job seeker")
def display_all_saved_posts(context):
    template = context["template"]

    assert context["route_exists"]
    assert "{% for post in posts %}" in template
    assert 'class="saved-post-card"' in template


@then(
    "the system should display the title, summary, category, "
    "publication date, and saved date of each post"
)
def display_saved_post_information(context):
    template = context["template"]

    assert "{{ post.title }}" in template
    assert "{{ post.summary }}" in template
    assert "{{ post.category }}" in template
    assert "{{ post.publication_date_display }}" in template
    assert "{{ post.saved_at_display }}" in template


@then("the system should display the selected Career Advice article")
def display_selected_article(context):
    assert context["has_article_link"]


@then("the system should display a message indicating that no posts have been saved")
def display_empty_saved_posts_message(context):
    template = context["template"]

    assert 'id="savedPostEmpty"' in template
    assert "No saved posts yet" in template
