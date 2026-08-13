import socket
import threading
import time
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import uvicorn
from pytest_bdd import given, scenarios, then, when
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/search_and_filter_career_advice_posts.feature")


@pytest.fixture(scope="session")
def live_server_url():
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        port = server_socket.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("The test server did not start.")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1200")

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def context():
    return {
        "marker": uuid4().hex[:10],
        "interview_title": None,
        "resume_title": None,
        "other_title": None,
    }


@pytest.fixture
def test_posts():
    post_ids = []
    yield post_ids

    for post_id in post_ids:
        db.collection("career_advice").document(post_id).delete()


def create_post(test_posts, title, category, summary):
    post_id = f"TEST_SEARCH_ADVICE_{uuid4().hex}"
    current_time = datetime.now(UTC)
    db.collection("career_advice").document(post_id).set(
        {
            "title": title,
            "category": category,
            "summary": summary,
            "content": (
                "This is published test content for career advice "
                "searching and category filtering functionality."
            ),
            "imageUrl": "",
            "status": "Published",
            "createdAt": current_time,
            "updatedAt": current_time,
            "publicationDate": current_time,
            "test": True,
        }
    )
    test_posts.append(post_id)


def prepare_posts(context, test_posts):
    marker = context["marker"]
    context["interview_title"] = f"{marker} Target Interview Guide"
    context["resume_title"] = f"{marker} Target Resume Guide"
    context["other_title"] = f"{marker} Networking Guide"

    create_post(
        test_posts,
        context["interview_title"],
        "Interview Tips",
        f"{marker} target advice for interviews",
    )
    create_post(
        test_posts,
        context["resume_title"],
        "Resume Tips",
        f"{marker} target advice for resumes",
    )
    create_post(
        test_posts,
        context["other_title"],
        "Networking",
        f"{marker} communication advice",
    )


def card(browser, title):
    return browser.find_element(
        By.XPATH,
        f"//article[contains(@class,'career-card')][contains(., '{title}')]",
    )


def wait_for_filter(browser):
    WebDriverWait(browser, 5).until(
        lambda driver: driver.find_element(By.ID, "resultInformation").text != ""
    )


# =====================================
# COMMON GIVEN
# =====================================


@given("the job seeker is viewing the career advice section")
def viewing_career_advice(
    browser,
    live_server_url,
    context,
    test_posts,
):
    prepare_posts(context, test_posts)
    browser.get(f"{live_server_url}/career-advice")
    WebDriverWait(browser, 5).until(
        lambda driver: card(driver, context["interview_title"]).is_displayed()
    )


# =====================================
# SCENARIO 1
# =====================================


@when("the job seeker enters a keyword in the search bar")
def search_by_keyword(browser, context):
    search = browser.find_element(By.ID, "adviceSearch")
    search.send_keys(f"{context['marker']} target interview")
    wait_for_filter(browser)


@then("the system should display career advice posts that match the keyword")
def verify_keyword_results(browser, context):
    assert card(browser, context["interview_title"]).is_displayed()
    assert not card(browser, context["resume_title"]).is_displayed()
    assert not card(browser, context["other_title"]).is_displayed()


# =====================================
# SCENARIO 2
# =====================================


@when("the job seeker selects a specific category filter")
def select_category(browser):
    browser.find_element(
        By.CSS_SELECTOR,
        "#categoryFilters [data-category='interview tips']",
    ).click()
    wait_for_filter(browser)


@then("the system should display only career advice posts that belong to the selected category")
def verify_category_results(browser, context):
    assert card(browser, context["interview_title"]).is_displayed()
    assert not card(browser, context["resume_title"]).is_displayed()
    assert not card(browser, context["other_title"]).is_displayed()


# =====================================
# SCENARIO 3
# =====================================


@when("the job seeker applies multiple search and filter criteria")
def apply_multiple_criteria(browser, context):
    browser.find_element(By.ID, "adviceSearch").send_keys(f"{context['marker']} target")
    browser.find_element(
        By.CSS_SELECTOR,
        "#categoryFilters [data-category='interview tips']",
    ).click()
    wait_for_filter(browser)


@then("the system should display career advice posts that match all selected criteria")
def verify_multiple_criteria(browser, context):
    assert card(browser, context["interview_title"]).is_displayed()
    assert not card(browser, context["resume_title"]).is_displayed()
    assert not card(browser, context["other_title"]).is_displayed()


# =====================================
# SCENARIO 4
# =====================================


@given("the job seeker has entered search criteria or applied filters")
def entered_search_criteria(
    browser,
    live_server_url,
    context,
    test_posts,
):
    prepare_posts(context, test_posts)
    browser.get(f"{live_server_url}/career-advice")
    WebDriverWait(browser, 5).until(
        lambda driver: driver.find_element(By.ID, "adviceSearch").is_displayed()
    )


@when("no career advice posts match the selected criteria")
def search_with_no_matches(browser):
    browser.find_element(By.ID, "adviceSearch").send_keys(f"NO_MATCH_{uuid4().hex}")
    WebDriverWait(browser, 5).until(
        lambda driver: driver.find_element(By.ID, "noResults").is_displayed()
    )


@then(
    "the system should display a message indicating that no relevant "
    "career advice posts are available"
)
def verify_no_results_message(browser):
    message = browser.find_element(By.ID, "noResults")
    assert message.is_displayed()
    assert "No matching articles" in message.text


# =====================================
# SCENARIO 5
# =====================================


@given("the job seeker has applied search criteria or filters")
def applied_search_and_filter(
    browser,
    live_server_url,
    context,
    test_posts,
):
    prepare_posts(context, test_posts)
    browser.get(f"{live_server_url}/career-advice")
    search = WebDriverWait(browser, 5).until(
        lambda driver: driver.find_element(By.ID, "adviceSearch")
    )
    search.send_keys(context["marker"])
    browser.find_element(
        By.CSS_SELECTOR,
        "#categoryFilters [data-category='interview tips']",
    ).click()


@when("the job seeker clears all search and filter options")
def clear_search_and_filters(browser):
    browser.find_element(By.ID, "clearSearch").click()
    browser.find_element(
        By.CSS_SELECTOR,
        "#categoryFilters [data-category='']",
    ).click()
    wait_for_filter(browser)


@then("the system should display all available career advice posts")
def verify_all_posts_displayed(browser, context):
    assert card(browser, context["interview_title"]).is_displayed()
    assert card(browser, context["resume_title"]).is_displayed()
    assert card(browser, context["other_title"]).is_displayed()
