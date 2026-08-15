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
from selenium.webdriver.support.ui import Select, WebDriverWait

from job_portal_web.backend.database import db
from job_portal_web.backend.main import app

scenarios("features/view_registered_user_accounts.feature")


@pytest.fixture(scope="session")
def live_server_url():
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        port = server_socket.getsockname()[1]

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
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
        "active_seeker_id": f"TEST_ACTIVE_SEEKER_{marker}",
        "suspended_seeker_id": f"TEST_SUSPENDED_SEEKER_{marker}",
        "employer_id": f"TEST_EMPLOYER_{marker}",
        "active_seeker_name": f"Active Seeker {marker}",
        "suspended_seeker_name": f"Suspended Seeker {marker}",
        "employer_name": f"Employer Company {marker}",
        "active_seeker_email": f"active.{marker}@example.com",
        "suspended_seeker_email": f"suspended.{marker}@example.com",
        "employer_email": f"employer.{marker}@example.com",
    }


@pytest.fixture
def test_accounts(context):
    current_time = datetime.now(UTC)

    db.collection("job_seeker").document(context["active_seeker_id"]).set(
        {
            "fullName": context["active_seeker_name"],
            "email": context["active_seeker_email"],
            "phone": "0123456789",
            "accountStatus": "Active",
            "createdAt": current_time,
            "test": True,
        }
    )
    db.collection("job_seeker").document(context["suspended_seeker_id"]).set(
        {
            "fullName": context["suspended_seeker_name"],
            "email": context["suspended_seeker_email"],
            "phone": "0198765432",
            "accountStatus": "Suspended",
            "createdAt": current_time,
            "test": True,
        }
    )
    db.collection("company").document(context["employer_id"]).set(
        {
            "companyName": context["employer_name"],
            "companyEmail": context["employer_email"],
            "companyPhone": "041234567",
            "accountStatus": "Active",
            "createdAt": current_time,
            "test": True,
        }
    )

    yield

    for user_id in (
        context["active_seeker_id"],
        context["suspended_seeker_id"],
    ):
        db.collection("job_seeker").document(user_id).delete()
    db.collection("company").document(context["employer_id"]).delete()


def row(browser, account_id):
    return browser.find_element(
        By.CSS_SELECTOR,
        f".user-account-row[data-id='{account_id}']",
    )


def open_management(browser, live_server_url, context):
    browser.get(f"{live_server_url}/admin/users")
    WebDriverWait(browser, 5).until(
        lambda driver: row(
            driver,
            context["active_seeker_id"],
        ).is_displayed()
    )


# =====================================
# SCENARIO 1
# =====================================


@given("the admin is logged into the admin dashboard")
def admin_logged_in(browser):
    assert browser.get_cookie("session") is not None


@when("the admin accesses the user management section")
def access_management(
    browser,
    live_server_url,
    context,
    test_accounts,
):
    open_management(browser, live_server_url, context)


@then("the system should display a list of all registered user accounts")
def verify_account_list(browser, context):
    assert row(browser, context["active_seeker_id"]).is_displayed()
    assert row(browser, context["suspended_seeker_id"]).is_displayed()
    assert row(browser, context["employer_id"]).is_displayed()


# =====================================
# COMMON LIST GIVEN
# =====================================


@given("the admin is viewing the registered user accounts list")
def viewing_account_list(
    browser,
    live_server_url,
    context,
    test_accounts,
):
    open_management(browser, live_server_url, context)


@given("the admin is viewing the user management section")
def viewing_management(
    browser,
    live_server_url,
    context,
    test_accounts,
):
    open_management(browser, live_server_url, context)


# =====================================
# SCENARIO 2
# =====================================


@when("the registered user accounts are displayed")
def accounts_displayed(browser, context):
    assert row(browser, context["active_seeker_id"]).is_displayed()


@then("the system should display each user's account details")
def verify_each_account_details(browser, context):
    assert (
        context["active_seeker_name"]
        in row(
            browser,
            context["active_seeker_id"],
        ).text
    )
    assert (
        context["employer_name"]
        in row(
            browser,
            context["employer_id"],
        ).text
    )


@then("the details should include the user's personal information and account status")
def verify_personal_information_and_status(browser, context):
    seeker_row = row(browser, context["active_seeker_id"])
    assert context["active_seeker_email"] in seeker_row.text
    assert "0123456789" in seeker_row.text
    assert "Active" in seeker_row.text

    employer_row = row(browser, context["employer_id"])
    assert context["employer_email"] in employer_row.text
    assert "041234567" in employer_row.text
    assert "Active" in employer_row.text


# =====================================
# SCENARIO 3
# =====================================


@when("the admin filters the accounts by user type or account status")
def filter_by_user_type(browser):
    Select(browser.find_element(By.ID, "accountTypeFilter")).select_by_value("job_seeker")


@then("the system should display only the user accounts that match the selected criteria")
def verify_filtered_accounts(browser, context):
    assert row(browser, context["active_seeker_id"]).is_displayed()
    assert row(browser, context["suspended_seeker_id"]).is_displayed()
    assert not row(browser, context["employer_id"]).is_displayed()


# =====================================
# SCENARIO 4
# =====================================


@when("the admin enters a user's name or email address in the search field")
def search_account(browser, context):
    browser.find_element(By.ID, "userSearch").send_keys(context["employer_email"])


@then("the system should display the user accounts that match the search criteria")
def verify_search_results(browser, context):
    assert row(browser, context["employer_id"]).is_displayed()
    assert not row(browser, context["active_seeker_id"]).is_displayed()
    assert not row(browser, context["suspended_seeker_id"]).is_displayed()
