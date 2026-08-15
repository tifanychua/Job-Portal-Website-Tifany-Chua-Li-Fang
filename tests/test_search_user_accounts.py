import json
import os
import socket
import threading
import time
from base64 import b64encode
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import uvicorn
from itsdangerous import TimestampSigner
from pytest_bdd import given, scenarios, then, when
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/search_user_accounts.feature")


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
def browser(live_server_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1200")

    driver = webdriver.Chrome(options=options)
    driver.get(live_server_url)

    secret_key = os.getenv("SECRET_KEY", "jobconnect-secret-key")
    session = {
        "user_type": "admin",
        "admin_id": "TEST_ADMIN",
        "user_id": "TEST_ADMIN",
    }
    encoded = b64encode(json.dumps(session).encode("utf-8"))
    signed = TimestampSigner(str(secret_key)).sign(encoded)

    driver.add_cookie(
        {
            "name": "session",
            "value": signed.decode("utf-8"),
            "path": "/",
        }
    )

    yield driver
    driver.quit()


@pytest.fixture
def context():
    marker = uuid4().hex[:10]
    return {
        "marker": marker,
        "job_seeker_id": f"TEST_SEARCH_SEEKER_{marker}",
        "employer_id": f"TEST_SEARCH_EMPLOYER_{marker}",
        "job_seeker_name": f"Alicia {marker}",
        "employer_name": f"Bright Company {marker}",
        "job_seeker_email": f"alicia.{marker}@example.com",
        "employer_email": f"company.{marker}@example.com",
    }


@pytest.fixture
def test_accounts(context):
    current_time = datetime.now(UTC)

    db.collection("job_seeker").document(context["job_seeker_id"]).set(
        {
            "fullName": context["job_seeker_name"],
            "email": context["job_seeker_email"],
            "accountStatus": "Active",
            "createdAt": current_time,
            "test": True,
        }
    )

    db.collection("company").document(context["employer_id"]).set(
        {
            "companyName": context["employer_name"],
            "companyEmail": context["employer_email"],
            "accountStatus": "Active",
            "createdAt": current_time,
            "test": True,
        }
    )

    yield

    db.collection("job_seeker").document(context["job_seeker_id"]).delete()
    db.collection("company").document(context["employer_id"]).delete()


def account_row(browser, account_id):
    return browser.find_element(
        By.CSS_SELECTOR,
        f".user-account-row[data-id='{account_id}']",
    )


def open_user_management(
    browser,
    live_server_url,
    context,
):
    browser.get(f"{live_server_url}/admin/users")
    WebDriverWait(browser, 5).until(
        lambda driver: account_row(
            driver,
            context["job_seeker_id"],
        ).is_displayed()
    )


def enter_search(browser, value):
    search = browser.find_element(By.ID, "userSearch")
    search.send_keys(value)


# =====================================
# COMMON GIVEN
# =====================================


@given("the admin is viewing the user management section")
def viewing_user_management(
    browser,
    live_server_url,
    context,
    test_accounts,
):
    open_user_management(browser, live_server_url, context)


# =====================================
# SCENARIO 1
# =====================================


@when("the admin enters a user's name in the search field")
def search_by_name(browser, context):
    enter_search(browser, context["job_seeker_name"])


@then("the system should display user accounts that match the entered name")
def verify_name_results(browser, context):
    assert account_row(
        browser,
        context["job_seeker_id"],
    ).is_displayed()
    assert not account_row(
        browser,
        context["employer_id"],
    ).is_displayed()


# =====================================
# SCENARIO 2
# =====================================


@when("the admin enters a user's email address in the search field")
def search_by_email(browser, context):
    enter_search(browser, context["employer_email"])


@then("the system should display the user account associated with the entered email address")
def verify_email_results(browser, context):
    assert account_row(
        browser,
        context["employer_id"],
    ).is_displayed()
    assert not account_row(
        browser,
        context["job_seeker_id"],
    ).is_displayed()


# =====================================
# SCENARIO 3
# =====================================


@when("the entered search criteria do not match any registered users")
def search_no_match(browser):
    enter_search(browser, f"NO_MATCH_{uuid4().hex}")


@then("the system should display a message indicating that no user accounts were found")
def verify_no_accounts_message(browser):
    no_results = WebDriverWait(browser, 5).until(
        lambda driver: driver.find_element(By.ID, "noFilteredUsers")
    )
    assert no_results.is_displayed()
    assert "No matching accounts" in no_results.text


# =====================================
# SCENARIO 4
# =====================================


@given("the admin has entered search criteria and is viewing filtered results")
def viewing_filtered_results(
    browser,
    live_server_url,
    context,
    test_accounts,
):
    open_user_management(browser, live_server_url, context)
    enter_search(browser, context["job_seeker_name"])
    assert account_row(
        browser,
        context["job_seeker_id"],
    ).is_displayed()
    assert not account_row(
        browser,
        context["employer_id"],
    ).is_displayed()


@when("the admin clears the search field")
def clear_search(browser):
    search = browser.find_element(By.ID, "userSearch")
    search.send_keys(Keys.CONTROL, "a")
    search.send_keys(Keys.BACKSPACE)


@then("the system should display the complete list of registered user accounts")
def verify_complete_account_list(browser, context):
    WebDriverWait(browser, 5).until(
        lambda driver: (
            account_row(
                driver,
                context["job_seeker_id"],
            ).is_displayed()
            and account_row(
                driver,
                context["employer_id"],
            ).is_displayed()
        )
    )
    assert account_row(
        browser,
        context["job_seeker_id"],
    ).is_displayed()
    assert account_row(
        browser,
        context["employer_id"],
    ).is_displayed()
