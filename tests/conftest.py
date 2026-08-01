import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Import the email service for mocking
from job_portal_web.backend import email_service

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def driver():
    options = Options()
    options.binary_location = "/snap/bin/chromium"

    # Headless mode
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(driver_version="150.0.7871.128").install()),
        options=options,
    )

    driver.implicitly_wait(10)

    yield driver

    driver.quit()


# =============================================
# Email Mock Fixture
# =============================================
@pytest.fixture
def email_mock():
    """
    Mock email service for testing.
    This fixture resets the email mock before each test.
    """
    # Reset the mock
    email_service.email_mock = {
        "sent": False,
        "email": None,
        "candidate": None,
        "company": None,
        "interview": None
    }
    
    # Ensure test environment is set
    os.environ["PYTEST_CURRENT_TEST"] = "true"
    
    # Return the mock for use in tests
    return email_service.email_mock


# =============================================
# Test Client Fixture (if you need it)
# =============================================
@pytest.fixture
def client():
    """Create a test client for FastAPI app."""
    from fastapi.testclient import TestClient
    from job_portal_web.backend.main import app
    return TestClient(app)


# =============================================
# Cleanup Fixture (if needed)
# =============================================
@pytest.fixture(autouse=True)
def cleanup():
    """Clean up after each test."""
    yield
    # Reset email mock after test
    email_service.email_mock = {
        "sent": False,
        "email": None,
        "candidate": None,
        "company": None,
        "interview": None
    }