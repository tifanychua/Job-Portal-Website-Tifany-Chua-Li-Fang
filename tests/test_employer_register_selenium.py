from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uuid
import time

# ==========================================
# Generate valid test data
# ==========================================


def generate_test_email():
    return f"company{uuid.uuid4().hex[:8]}@gmail.com"


def generate_registration_number():
    # 12 digits, start with non-zero
    return "20" + uuid.uuid4().int.__str__()[:10]


# ==========================================
# Handle javascript alert
# ==========================================


def handle_alert(driver, timeout=3):

    try:
        alert = WebDriverWait(driver, timeout).until(EC.alert_is_present())

        message = alert.text
        alert.accept()

        return message

    except Exception:
        return None


# ==========================================
# Fill registration wizard
# ==========================================


def fill_employer_registration_form(driver, base_url, email=None):

    if email is None:
        email = generate_test_email()

    driver.get(f"{base_url}/register?role=employer")

    wait = WebDriverWait(driver, 10)

    # ==========================
    # STEP 1
    # ==========================

    wait.until(EC.visibility_of_element_located((By.ID, "companyName")))

    driver.find_element(By.ID, "companyName").send_keys("ABC Technology Sdn Bhd")

    driver.find_element(By.ID, "businessEmail").send_keys(email)

    driver.find_element(By.ID, "registrationNumber").send_keys(generate_registration_number())

    driver.find_element(By.ID, "phone").send_keys("0123456789")

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
    # STEP 2
    # ==========================

    wait.until(EC.visibility_of_element_located((By.ID, "contactFullName")))

    driver.find_element(By.ID, "contactFullName").send_keys("John Tan")

    driver.find_element(By.ID, "contactEmail").send_keys(email)

    driver.find_element(By.ID, "contactJobTitle").send_keys("HR Manager")

    driver.find_element(By.ID, "contactDepartment").send_keys("Human Resource")

    driver.find_element(By.ID, "contactPhone").send_keys("0123456789")

    driver.find_element(By.ID, "correspondenceAddress").send_keys("Jalan Bukit Bintang")

    driver.find_element(By.ID, "nextBtn").click()

    # ==========================
    # STEP 3
    # ==========================

    wait.until(EC.visibility_of_element_located((By.ID, "accountEmail")))

    driver.find_element(By.ID, "accountEmail").send_keys(email)

    driver.find_element(By.ID, "wizardPassword").send_keys("Password123!")

    driver.find_element(By.ID, "wizardConfirmPassword").send_keys("Password123!")

    driver.find_element(By.ID, "nextBtn").click()

    return email


# ==========================================
# Password mismatch
# ==========================================


def test_password_not_match(driver, base_url):

    driver.get(f"{base_url}/register?role=employer")

    driver.execute_script("currentStep=3;goToStep(3);")

    driver.find_element(By.ID, "accountEmail").send_keys(generate_test_email())

    driver.find_element(By.ID, "wizardPassword").send_keys("Password123!")

    driver.find_element(By.ID, "wizardConfirmPassword").send_keys("Password321!")

    driver.find_element(By.ID, "nextBtn").click()

    alert = WebDriverWait(driver, 5).until(EC.alert_is_present())

    assert "Passwords do not match" in alert.text

    alert.accept()


# ==========================================
# Successful registration
# ==========================================


def test_successful_registration(driver, base_url):

    fill_employer_registration_form(driver, base_url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "submitBtn")))

    driver.find_element(By.ID, "submitBtn").click()

    alert = handle_alert(driver)

    if alert:
        assert False, alert

    WebDriverWait(driver, 15).until(lambda d: "login" in d.current_url.lower())

    assert "login" in driver.current_url.lower()


# ==========================================
# Required field
# ==========================================


def test_company_name_required(driver, base_url):

    driver.get(f"{base_url}/register?role=employer")

    driver.find_element(By.ID, "nextBtn").click()

    field = driver.find_element(By.ID, "companyName")

    assert field.get_attribute("validationMessage") != ""


# ==========================================
# Existing email
# ==========================================


def test_existing_email(driver, base_url):

    email = generate_test_email()

    # First register
    fill_employer_registration_form(driver, base_url, email)

    driver.find_element(By.ID, "submitBtn").click()

    time.sleep(3)

    handle_alert(driver)

    # Second register same email

    fill_employer_registration_form(driver, base_url, email)

    driver.find_element(By.ID, "submitBtn").click()

    alert = WebDriverWait(driver, 10).until(EC.alert_is_present())

    message = alert.text.lower()

    assert "already" in message or "email" in message or "in use" in message

    alert.accept()
