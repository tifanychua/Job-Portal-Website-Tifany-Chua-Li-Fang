import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Import the email service for mocking
from job_portal_web.backend import email_service

BASE_URL = "http://127.0.0.1:8000"


# =============================================
# Base URL Fixture
# =============================================


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


# =============================================
# Base URL Fixture
# =============================================


@pytest.fixture
def driver():

    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument("--window-size=1920,1080")

    # WSL stability
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=VizDisplayCompositor")


    driver = webdriver.Chrome(options=options)

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
    Reset email mock before each test.
    """

    email_service.email_mock = {
        "sent": False,
        "email": None,
        "candidate": None,
        "company": None,
        "interview": None,
    }

    os.environ["PYTEST_CURRENT_TEST"] = "true"

    return email_service.email_mock


# =============================================
# FastAPI Test Client Fixture
# =============================================


@pytest.fixture
def client():

    from fastapi.testclient import TestClient

    from job_portal_web.backend.main import app

    return TestClient(app)


# =============================================
# Cleanup Fixture
# =============================================


@pytest.fixture(autouse=True)
def cleanup():

    yield

    email_service.email_mock = {
        "sent": False,
        "email": None,
        "candidate": None,
        "company": None,
        "interview": None,
    }
