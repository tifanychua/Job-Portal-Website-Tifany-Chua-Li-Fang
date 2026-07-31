from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def fill_employer_registration_form(driver, base_url):

    driver.get(f"{base_url}/register?role=employer")

    # ==========================
    # Step 1
    # ==========================

    driver.find_element(By.ID, "companyName").send_keys("ABC Technology")

    driver.find_element(By.ID, "businessEmail").send_keys("company@gmail.com")

    driver.find_element(By.ID, "registrationNumber").send_keys("202401234567")

    driver.find_element(By.ID, "phone").send_keys("123456789")

    Select(driver.find_element(By.ID, "industry")).select_by_visible_text("Information Technology")

    driver.find_element(By.ID, "companyAddress").send_keys("Jalan Bukit Bintang")

    Select(driver.find_element(By.ID, "companySize")).select_by_visible_text("11 - 50 employees")

    driver.find_element(By.ID, "city").send_keys("Kuala Lumpur")

    driver.find_element(By.ID, "companyWebsite").send_keys("https://abc.com")

    Select(driver.find_element(By.ID, "state")).select_by_visible_text("Kuala Lumpur")

    driver.find_element(By.ID, "postalCode").send_keys("55100")

    driver.find_element(By.ID, "companyDescription").send_keys("Software Company")

    driver.find_element(By.ID, "nextBtn").click()

    # ==========================
    # Step 2
    # ==========================

    driver.find_element(By.ID, "contactFullName").send_keys("John Tan")

    driver.find_element(By.ID, "contactEmail").send_keys("john@gmail.com")

    driver.find_element(By.ID, "contactJobTitle").send_keys("HR Manager")

    driver.find_element(By.ID, "contactDepartment").send_keys("Human Resource")

    driver.find_element(By.ID, "contactPhone").send_keys("111111111")

    driver.find_element(By.ID, "correspondenceAddress").send_keys("Jalan Bukit Bintang")

    driver.find_element(By.ID, "nextBtn").click()

    # ==========================
    # Step 3
    # ==========================

    driver.find_element(By.ID, "accountEmail").send_keys("company@gmail.com")

    driver.find_element(By.ID, "wizardPassword").send_keys("Password123!")

    driver.find_element(By.ID, "wizardConfirmPassword").send_keys("Password123!")

    driver.find_element(By.ID, "nextBtn").click()


def test_password_not_match(driver, base_url):

    driver.get(f"{base_url}/register?role=employer")

    driver.execute_script("currentStep=3;goToStep(3);")

    driver.find_element(By.ID, "accountEmail").send_keys("company@gmail.com")

    driver.find_element(By.ID, "wizardPassword").send_keys("Password123!")

    driver.find_element(By.ID, "wizardConfirmPassword").send_keys("Password321!")

    driver.find_element(By.ID, "nextBtn").click()

    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())

    assert alert.text == "Passwords do not match."

    alert.accept()


def test_successful_registration(driver, base_url):

    fill_employer_registration_form(driver, base_url)

    driver.find_element(By.ID, "submitBtn").click()

    WebDriverWait(driver, 10).until(lambda d: "login" in d.current_url.lower())

    assert "login" in driver.current_url.lower()


def test_company_name_required(driver, base_url):

    driver.get(f"{base_url}/register?role=employer")

    driver.find_element(By.ID, "nextBtn").click()

    field = driver.find_element(By.ID, "companyName")

    assert field.get_attribute("validationMessage") != ""


def test_existing_email(driver, base_url):

    fill_employer_registration_form(driver, base_url)

    driver.find_element(By.ID, "submitBtn").click()

    alert = WebDriverWait(driver, 10).until(EC.alert_is_present())

    message = alert.text.lower()

    print(message)

    assert "already" in message or "email" in message or "in use" in message

    alert.accept()
