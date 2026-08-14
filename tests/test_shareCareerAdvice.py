from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("features/share_career_advice.feature")


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DETAILS_TEMPLATE = (
    PROJECT_ROOT / "src" / "job_portal_web" / "ui" / "jobSeekerCareerAdviceDetails.html"
)


def read_template() -> str:
    assert DETAILS_TEMPLATE.exists(), f"Template not found: {DETAILS_TEMPLATE}"

    return DETAILS_TEMPLATE.read_text(
        encoding="utf-8",
        errors="ignore",
    )


@pytest.fixture
def context():
    return {}


@given("the job seeker is viewing a Career Advice article")
def viewing_career_advice_article(context):
    template = read_template()

    assert 'id="shareArticle"' in template

    context["template"] = template


@given("the browser supports the device sharing function")
def browser_supports_sharing(context):
    template = context["template"]

    context["supports_sharing"] = "navigator.share" in template


@given("the browser does not support the device sharing function")
def browser_does_not_support_sharing(context):
    template = context["template"]

    context["has_fallback"] = "navigator.clipboard.writeText" in template


@given("the device sharing options are displayed")
def sharing_options_displayed(context):
    template = read_template()

    assert "navigator.share" in template

    context["template"] = template


@when("the job seeker clicks the Share button")
def click_share_button(context):
    template = context["template"]

    context["has_click_listener"] = (
        'getElementById("shareArticle")' in template and 'addEventListener("click"' in template
    )


@when("the job seeker cancels the sharing operation")
def cancel_sharing(context):
    template = context["template"]

    context["handles_abort"] = 'error.name !== "AbortError"' in template


@when("the article cannot be shared or copied")
def sharing_fails(context):
    template = context["template"]

    context["has_error_message"] = "Unable to share this article." in template


@then("the system should open the device sharing options")
def open_device_sharing_options(context):
    assert context["supports_sharing"]
    assert context["has_click_listener"]


@then("the article title and link should be prepared for sharing")
def prepare_article_information(context):
    template = context["template"]

    assert "title: document.title" in template
    assert "url: window.location.href" in template


@then("the system should copy the article link to the clipboard")
def copy_article_link(context):
    template = context["template"]

    assert context["has_fallback"]
    assert "window.location.href" in template


@then("the system should display a message indicating that the article link was copied")
def display_link_copied_message(context):
    template = context["template"]

    assert "Article link copied." in template


@then("the system should close the device sharing options")
def close_sharing_options(context):
    assert context["handles_abort"]


@then("the job seeker should remain on the Career Advice article page")
def remain_on_article_page(context):
    template = context["template"]

    assert "window.location.href =" not in template


@then("the system should display a message indicating that the article cannot be shared")
def display_share_error(context):
    assert context["has_error_message"]
