from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

scenarios("features/search_messages.feature")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "src" / "job_portal_web" / "backend"

BACKEND_DIR = PROJECT_ROOT / "src" / "job_portal_web" / "backend"
MESSAGES_TEMPLATE = PROJECT_ROOT / "src" / "job_portal_web" / "ui" / "messages.html"

MAIN_FILE = BACKEND_DIR / "main.py"


def read_file(path: Path) -> str:
    assert path.exists(), f"Required file not found: {path}"
    return path.read_text(encoding="utf-8", errors="ignore")


@pytest.fixture
def context():
    return {}


@given("the user is logged into the system")
def user_logged_in(context):
    main_source = read_file(MAIN_FILE)

    assert 'request.session.get("user_type")' in main_source
    assert 'RedirectResponse("/login"' in main_source

    context["logged_in"] = True


@given("the user is viewing the Messages page")
def viewing_messages_page(context):
    main_source = read_file(MAIN_FILE)
    template = read_file(MESSAGES_TEMPLATE)

    assert '@app.get("/messages")' in main_source
    assert 'id="conversationList"' in template

    context["template"] = template


@given("the user has entered a value in the conversation search field")
def search_value_entered(context):
    template = read_file(MESSAGES_TEMPLATE)

    assert 'id="conversationSearch"' in template

    context["template"] = template


@when("the user enters a name in the conversation search field")
def search_conversation_by_name(context):
    template = context["template"]

    context["searches_name"] = "name.includes(searchText)" in template


@when("the user enters a keyword from the latest message in the search field")
def search_by_latest_message(context):
    template = context["template"]

    context["searches_message"] = "message.includes(searchText)" in template


@when("the user enters a search value that does not match any conversation")
def search_nonexistent_conversation(context):
    template = context["template"]

    context["has_no_results"] = "No conversations found" in template


@when("the user clears the search field")
def clear_conversation_search(context):
    template = context["template"]

    context["clears_search"] = 'searchInput.value = ""' in template

    context["renders_all"] = "renderConversations(allConversations)" in template


@then("the system should display conversations that match the entered name")
def display_matching_names(context):
    assert context["searches_name"]


@then("the system should display conversations containing the entered keyword")
def display_matching_messages(context):
    assert context["searches_message"]


@then("the system should display a message indicating that no conversations were found")
def display_no_conversation_results(context):
    assert context["has_no_results"]


@then("the system should display all conversations")
def display_all_conversations(context):
    assert context["clears_search"]
    assert context["renders_all"]
