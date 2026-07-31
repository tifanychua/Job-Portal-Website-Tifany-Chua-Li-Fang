import time
from pytest_bdd import scenarios, given, when, then

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

scenarios("features/jobSeeker_register.feature")


def fill_registration_form(
    driver, email=None, password="Password@123", confirm_password="Password@123"
):

    if email is None:
        email = f"selenium_{int(time.time())}@gmail.com"

    driver.find_element(By.ID, "name").send_keys("John Doe")

    driver.find_element(By.ID, "email").send_keys(email)

    driver.find_element(By.ID, "phone").send_keys("0123456789")

    driver.find_element(By.ID, "password").send_keys(password)

    driver.find_element(By.ID, "confirm_password").send_keys(confirm_password)

    driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']").click()

    return email


@given("the job seeker is on the registration page")
def register_page(driver, base_url):

    driver.get(f"{base_url}/register")


@given("the email address is already registered")
def existing_email(driver, base_url):

    driver.get(f"{base_url}/register")


@given("the job seeker has successfully registered an account")
def registered(driver, base_url):

    driver.get(f"{base_url}/register")


@when("the job seeker enters valid registration information")
def valid_information(driver):

    fill_registration_form(driver)

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@when("the job seeker submits the registration form using that email address")
def submit_existing_email(driver):

    fill_registration_form(driver, email="existing@gmail.com")

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@when("the job seeker submits the registration form with missing or invalid information")
def invalid_information(driver):

    driver.find_element(By.ID, "name").send_keys("John Doe")

    driver.find_element(By.ID, "password").send_keys("Password@123")

    driver.find_element(By.ID, "confirm_password").send_keys("Password@123")

    driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']").click()

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@when("the job seeker enters different values for the password and confirm password fields")
def password_not_match(driver):

    fill_registration_form(driver, password="Password@123", confirm_password="Password@456")

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@when("the registration process is completed")
def completed(driver):

    fill_registration_form(driver)

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@then("the system should create a new job seeker account successfully")
def success(driver):

    WebDriverWait(driver, 10).until(lambda d: "login" in d.current_url.lower())

    assert "login" in driver.current_url.lower()


@then('the system should display an "Email address already exists" message')
def duplicate_email(driver):

    alert = WebDriverWait(driver, 10).until(EC.alert_is_present())

    assert "already" in alert.text.lower() or "email" in alert.text.lower()

    alert.accept()


@then("the system should display appropriate validation messages")
def validation(driver):

    email = driver.find_element(By.ID, "email")

    assert email.get_attribute("validationMessage") != ""


@then('the system should display a "Passwords do not match" message')
def password_error(driver):

    alert = WebDriverWait(driver, 10).until(EC.alert_is_present())

    assert "passwords do not match" in alert.text.lower()

    alert.accept()


@then("the account should not be created")
def account_not_created(driver):

    assert "register" in driver.current_url.lower()


@then("the system should allow the job seeker to proceed to login")
def redirect(driver):

    WebDriverWait(driver, 10).until(lambda d: "login" in d.current_url.lower())

    assert "login" in driver.current_url.lower()

    assert "registered=success" in driver.current_url.lower()
