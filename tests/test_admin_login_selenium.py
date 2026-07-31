from pytest_bdd import scenarios, given, when, then

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

scenarios("features/admin_login.feature")


def admin_login(driver, email, password):

    driver.find_element(By.ID, "email").clear()

    driver.find_element(By.ID, "email").send_keys(email)

    driver.find_element(By.ID, "password").clear()

    driver.find_element(By.ID, "password").send_keys(password)

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@given("the admin is on the login page")
def admin_login_page(driver, base_url):

    driver.get(f"{base_url}/login/admin")


@given("the admin has a registered administrator account")
def registered_admin(driver, base_url):

    driver.get(f"{base_url}/login/admin")


@given("the admin has entered incorrect login credentials")
def invalid_admin(driver, base_url):

    driver.get(f"{base_url}/login/admin")


@given("the admin has logged in successfully")
def logged_in_admin(driver, base_url):

    driver.get(f"{base_url}/login/admin")

    admin_login(driver, "teohyongyun90@gmail.com", "Yy050613.")

    WebDriverWait(driver, 20).until(lambda d: "/admin/company-requests" in d.current_url)


@when("the admin enters a valid email address and password")
def valid_login(driver):

    admin_login(driver, "teohyongyun90@gmail.com", "Yy050613.")


@when("the admin attempts to log in")
def invalid_login(driver):

    admin_login(driver, "wrong@gmail.com", "wrongpassword")


@when("the admin leaves the email address or password field empty")
def empty_fields(driver):

    driver.find_element(By.ID, "email").clear()

    driver.find_element(By.ID, "password").clear()


@when("attempts to log in")
def submit_empty(driver):

    driver.find_element(By.CSS_SELECTOR, ".btn-auth-submit").click()


@when("the admin accesses the system")
def access_dashboard():

    pass


@then("the system should authenticate the admin successfully")
def login_success(driver):

    WebDriverWait(driver, 20).until(lambda d: "/admin/company-requests" in d.current_url)


@then("redirect the admin to the administration dashboard")
def redirect_dashboard(driver):

    assert "/admin/company-requests" in driver.current_url



@then("the system should display an error message")
def login_error(driver):

    WebDriverWait(driver, 10).until(EC.alert_is_present())

    alert = driver.switch_to.alert

    assert alert.text != ""

    alert.accept()


@then("prevent access to administrative features")
def no_dashboard(driver):

    assert "/admin/company-requests" not in driver.current_url


@then("the system should display validation messages")
def validation(driver):

    email = driver.find_element(By.ID, "email")

    assert email.get_attribute("validationMessage") != ""


@then("request the admin to complete the required fields")
def request_complete(driver):

    assert "/login/admin" in driver.current_url


@then("the system should allow access to platform management features")
def access_features(driver):

    assert "/admin/company-requests" in driver.current_url