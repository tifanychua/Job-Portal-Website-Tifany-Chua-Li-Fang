
import pytest
from pytest_bdd import scenarios, given, when, then

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

scenarios("features/forgot_password.feature")


def submit_forgot_password(driver, email):

    driver.find_element(By.ID, "email").clear()
    driver.find_element(By.ID, "email").send_keys(email)

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()

    WebDriverWait(driver, 10).until(
        lambda d: d.current_url != "http://127.0.0.1:8000/forgot-password"
    )


@given("the user is on the Forgot Password page")
def forgot_password_page(driver, base_url):

    driver.get(f"{base_url}/forgot-password")


@given("the user has received the password reset email")
def received_reset_email():
    pytest.skip("Handled by Firebase Authentication (out of application scope).")


@given("the password reset verification link is expired or invalid")
def invalid_reset_link():
    pytest.skip("Handled by Firebase Authentication (out of application scope).")


@when("the user enters a registered email address and submits the request")
def request_password_reset(driver):

    submit_forgot_password(driver, "teohyongyun92@gmail.com")


@when("the user enters an email address that is not registered")
def unregistered_email(driver):

    submit_forgot_password(driver, "notfound@gmail.com")


@when("the user opens the valid verification link and enters a new password")
def valid_reset_link():

    pytest.skip("Firebase hosted password reset page is outside the application scope.")


@when("the user attempts to reset the password")
def invalid_reset():

    pytest.skip("Firebase hosted password reset page is outside the application scope.")


@then("the system should send a password reset email containing a verification link")
def reset_email_sent(driver):

    WebDriverWait(driver, 10).until(lambda d: "sent=1" in d.current_url)

    assert "Check Your Email" in driver.page_source

    assert "Resend Email" in driver.page_source

    assert "Back to Log In" in driver.page_source


@then("the system should display the same confirmation message")
def same_confirmation(driver):

    WebDriverWait(driver, 10).until(lambda d: "sent=1" in d.current_url)

    assert "Check Your Email" in driver.page_source


@then("no information about whether the email exists should be revealed")
def no_information(driver):

    assert "Email address not found" not in driver.page_source

    assert "Invalid email" not in driver.page_source


@then("the system should update the user's password successfully")
def password_updated():

    pytest.skip("Password update is handled by Firebase Authentication.")


@then("redirect the user to the login page")
def redirect_login():

    pytest.skip("Redirect is handled by Firebase Authentication.")


@then('the system should display an "Invalid or expired verification link" message')
def invalid_link():

    pytest.skip("Handled by Firebase Authentication.")


@then("the password should not be updated")
def password_not_updated():

    pytest.skip("Handled by Firebase Authentication.")
