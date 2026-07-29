from fastapi.testclient import TestClient
import pytest
from job_portal_web.backend.main import app
from job_portal_web.backend.jobs import apply_search

client = TestClient(app)


# ==========================
# Test Data
# ==========================


@pytest.fixture
def sample_jobs():
    return [
        {
            "job_title": "Software Engineer",
            "company_name": "Microsoft",
            "location": "Kuala Lumpur",
            "position": "Senior Executive",
            "category": "Information Technology",
            "benefits": ["Socso", "Transport Allowance"],
        },
        {
            "job_title": "Software Developer",
            "company_name": "Google",
            "location": "Selangor",
            "position": "Internship",
            "category": "Information Technology",
            "benefits": ["Socso"],
        },
        {
            "job_title": "Accountant",
            "company_name": "Deloitte",
            "location": "Penang",
            "position": "Senior Engineer",
            "category": "Finance",
            "benefits": ["EPF"],
        },
    ]


# ==================================================
# Integration Tests
# ==================================================


def test_view_all_jobs():
    response = client.get("/jobs")

    assert response.status_code == 200
    assert "Find Your Dream Job" in response.text


def test_search_job_title():
    response = client.get("/jobs", params={"q": "Software Engineer"})

    assert response.status_code == 200


def test_search_company():
    response = client.get("/jobs", params={"q": "Microsoft"})

    assert response.status_code == 200


def test_filter_location():
    response = client.get("/jobs", params={"location": "Kuala Lumpur"})

    assert response.status_code == 200


def test_filter_by_position():

    response = client.get("/jobs", params={"position": "Senior Engineer"})

    assert response.status_code == 200

    assert "Senior Engineer" in response.text


def test_filter_by_benefits():

    response = client.get("/jobs", params={"benefits": "Socso"})

    assert response.status_code == 200

    assert "Socso" in response.text


def test_search_and_filter():
    response = client.get("/jobs", params={"q": "Engineer", "location": "Kuala Lumpur"})

    assert response.status_code == 200


# ==================================================
# Unit Tests
# ==================================================


def test_search_exact_job_title(sample_jobs):

    result = apply_search(sample_jobs, "Software Engineer", "")

    assert len(result) == 1
    assert result[0]["job_title"] == "Software Engineer"


def test_search_case_insensitive(sample_jobs):

    result = apply_search(sample_jobs, "software engineer", "")

    assert len(result) == 1
    assert result[0]["job_title"] == "Software Engineer"


def test_search_category(sample_jobs):

    result = apply_search(sample_jobs, "", "Information Technology")

    assert len(result) == 2

    for job in result:
        assert job["category"] == "Information Technology"


def test_search_keyword_and_category(sample_jobs):

    result = apply_search(sample_jobs, "Software", "Information Technology")

    assert len(result) == 2


def test_search_no_result(sample_jobs):

    result = apply_search(sample_jobs, "Astronaut", "")

    assert result == []


def test_empty_search_returns_all_jobs(sample_jobs):

    result = apply_search(sample_jobs, "", "")

    assert len(result) == 3
