from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_bdd import given, scenarios, then, when
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.routes import (
    adminAnalytics as analytics_backend,
)

# ==================================================
# Test Application
# ==================================================

test_app = FastAPI()

test_app.add_middleware(
    SessionMiddleware,
    secret_key="analytics-test-secret",
)

test_app.include_router(analytics_backend.router)


# ==================================================
# Feature
# ==================================================

scenarios("features/adminDashboardAnalytics.feature")

ANALYTICS_URL = "/admin/dashboard/analytics-data"


# ==================================================
# Context
# ==================================================


class Context:
    def __init__(self):
        self.response = None
        self.data = None


@pytest.fixture
def context():
    return Context()


# ==================================================
# Analytics Module
# ==================================================


@pytest.fixture
def analytics_module():
    return analytics_backend


# ==================================================
# Test Client
# ==================================================


@pytest.fixture
def client():
    with TestClient(test_app) as test_client:
        yield test_client


# ==================================================
# Mock Dashboard Data
# ==================================================


def install_mock_dashboard_data(
    monkeypatch,
    analytics_module,
):
    current_year = analytics_module.CURRENT_YEAR

    collections = {
        "job_seeker": [
            {
                "_document_id": "SEEKER001",
                "name": "Test Seeker One",
            },
            {
                "_document_id": "SEEKER002",
                "name": "Test Seeker Two",
            },
        ],
        "company": [
            {
                "_document_id": "COMPANY001",
                "companyName": "Test Company One",
            },
            {
                "_document_id": "COMPANY002",
                "companyName": "Test Company Two",
            },
        ],
        "job_list": [
            {
                "_document_id": "JOB001",
                "status": "Active",
            },
            {
                "_document_id": "JOB002",
                "status": "Published",
            },
            {
                "_document_id": "JOB003",
                "status": "Draft",
            },
            {
                "_document_id": "JOB004",
                "status": "Open",
            },
        ],
        "application": [
            {
                "_document_id": "APPLICATION001",
                "status": "Submitted",
            },
            {
                "_document_id": "APPLICATION002",
                "applicationStatus": "Shortlisted",
            },
            {
                "_document_id": "APPLICATION003",
                "status": "Accepted",
            },
            {
                "_document_id": "APPLICATION004",
            },
        ],
        "payment": [
            {
                "_document_id": "PAYMENT001",
                "company_id": "COMPANY001",
                "package_name": "Basic Plan",
                "amount": 100,
                "status": "COMPLETED",
                "completed_at": datetime(
                    current_year,
                    1,
                    15,
                    10,
                    30,
                    tzinfo=UTC,
                ),
            },
            {
                "_document_id": "PAYMENT002",
                "company_id": "COMPANY002",
                "package_name": "Premium Plan",
                "amount": 200.50,
                "status": "COMPLETED",
                "completed_at": datetime(
                    current_year,
                    8,
                    1,
                    14,
                    0,
                    tzinfo=UTC,
                ),
            },
            {
                "_document_id": "PAYMENT003",
                "company_id": "COMPANY001",
                "package_name": "Basic Plan",
                "amount": 50,
                "status": "PENDING",
                "created_at": datetime(
                    current_year,
                    9,
                    1,
                    9,
                    0,
                    tzinfo=UTC,
                ),
            },
            {
                "_document_id": "PAYMENT004",
                "company_id": "COMPANY002",
                "package_name": "Premium Plan",
                "amount": 70,
                "status": "FAILED",
                "created_at": datetime(
                    current_year,
                    7,
                    10,
                    12,
                    0,
                    tzinfo=UTC,
                ),
            },
            {
                "_document_id": "PAYMENT005",
                "company_id": "COMPANY001",
                "package_name": "Old Plan",
                "amount": 999,
                "status": "COMPLETED",
                "completed_at": datetime(
                    current_year - 1,
                    12,
                    31,
                    12,
                    0,
                    tzinfo=UTC,
                ),
            },
        ],
    }

    company_names = {
        "COMPANY001": "Test Company One",
        "COMPANY002": "Test Company Two",
    }

    def fake_safe_stream(collection_name):
        records = collections.get(
            collection_name,
            [],
        )

        return [dict(record) for record in records]

    def fake_first_collection_with_data(
        names,
    ):
        for name in names:
            records = collections.get(name, [])

            if records:
                return [dict(record) for record in records]

        return []

    def fake_company_name(
        company_id,
        cache,
    ):
        name = company_names.get(
            company_id,
            "Unknown company",
        )

        cache[company_id] = name

        return name

    monkeypatch.setattr(
        analytics_module,
        "_safe_stream",
        fake_safe_stream,
    )

    monkeypatch.setattr(
        analytics_module,
        "_first_collection_with_data",
        fake_first_collection_with_data,
    )

    monkeypatch.setattr(
        analytics_module,
        "_company_name",
        fake_company_name,
    )


# ==================================================
# Acceptance Test
# Administrator Retrieves Analytics
# ==================================================


def test_admin_retrieves_dashboard_analytics(
    client,
    monkeypatch,
    analytics_module,
):
    install_mock_dashboard_data(
        monkeypatch,
        analytics_module,
    )

    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: True,
    )

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 200

    result = response.json()

    assert "generated_at" in result
    assert "current_year" in result
    assert "metrics" in result
    assert "transaction_statuses" in result
    assert "charts" in result
    assert "recent_transactions" in result


# ==================================================
# Verify Dashboard Metrics
# ==================================================


def test_dashboard_metrics_are_calculated_correctly(
    client,
    monkeypatch,
    analytics_module,
):
    install_mock_dashboard_data(
        monkeypatch,
        analytics_module,
    )

    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: True,
    )

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 200

    result = response.json()
    metrics = result["metrics"]

    assert metrics["total_users"] == 4
    assert metrics["job_seekers"] == 2
    assert metrics["employers"] == 2
    assert metrics["active_jobs"] == 3
    assert metrics["applications"] == 4

    assert metrics["completed_transactions"] == 3

    # Current-year completed payments:
    # RM100 + RM200.50
    assert metrics["current_year_revenue"] == 300.50


# ==================================================
# Verify Charts and Transaction Statuses
# ==================================================


def test_dashboard_charts_and_transaction_statuses(
    client,
    monkeypatch,
    analytics_module,
):
    install_mock_dashboard_data(
        monkeypatch,
        analytics_module,
    )

    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: True,
    )

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 200

    result = response.json()

    statuses = result["transaction_statuses"]

    assert statuses["completed"] == 3
    assert statuses["pending"] == 1
    assert statuses["failed"] == 1

    monthly_revenue = result["charts"]["monthly_revenue"]

    assert monthly_revenue["labels"] == [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    # January revenue
    assert monthly_revenue["values"][0] == 100

    # August revenue
    assert monthly_revenue["values"][7] == 200.50

    user_mix = result["charts"]["user_mix"]

    assert user_mix["labels"] == [
        "Job seekers",
        "Employers",
    ]

    assert user_mix["values"] == [2, 2]

    application_chart = result["charts"]["application_statuses"]

    application_results = dict(
        zip(
            application_chart["labels"],
            application_chart["values"],
        )
    )

    assert application_results["Submitted"] == 2

    assert application_results["Shortlisted"] == 1

    assert application_results["Accepted"] == 1


# ==================================================
# Verify Recent Transactions
# ==================================================


def test_recent_transactions_are_sorted_by_date(
    client,
    monkeypatch,
    analytics_module,
):
    install_mock_dashboard_data(
        monkeypatch,
        analytics_module,
    )

    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: True,
    )

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 200

    transactions = response.json()["recent_transactions"]

    assert len(transactions) == 5

    # September payment is the newest.
    assert transactions[0]["transaction_id"] == "PAYMENT003"

    assert transactions[0]["company_name"] == "Test Company One"

    assert transactions[0]["status"] == "PENDING"

    # August payment is second.
    assert transactions[1]["transaction_id"] == "PAYMENT002"

    assert transactions[1]["amount"] == 200.50


# ==================================================
# Negative Test
# Non-Administrator Access
# ==================================================


def test_non_admin_cannot_access_dashboard_analytics(
    client,
    monkeypatch,
    analytics_module,
):
    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: False,
    )

    response = client.get(ANALYTICS_URL)

    assert response.status_code == 401

    assert response.json()["detail"] == ("Admin login required")


# ==================================================
# BDD Given Steps
# ==================================================


@given("analytics test records are available")
def analytics_records_available(
    monkeypatch,
    analytics_module,
):
    install_mock_dashboard_data(
        monkeypatch,
        analytics_module,
    )


@given("the requester is logged in as an administrator")
def requester_is_admin(
    monkeypatch,
    analytics_module,
):
    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: True,
    )


@given("the requester is not logged in as an administrator")
def requester_is_not_admin(
    monkeypatch,
    analytics_module,
):
    monkeypatch.setattr(
        analytics_module,
        "_is_admin",
        lambda request: False,
    )


# ==================================================
# BDD When Step
# ==================================================


@when("the requester retrieves the dashboard analytics")
def retrieve_dashboard_analytics(
    client,
    context,
):
    context.response = client.get(ANALYTICS_URL)

    if context.response.status_code == 200:
        context.data = context.response.json()


# ==================================================
# BDD Then: Dashboard Analytics
# ==================================================


@then("the dashboard metrics and charts should be returned")
def verify_dashboard_response(context):
    assert context.response is not None

    assert context.response.status_code == 200

    result = context.data

    assert result["metrics"]["total_users"] == 4

    assert result["metrics"]["active_jobs"] == 3

    assert result["metrics"]["applications"] == 4

    assert "monthly_revenue" in result["charts"]

    assert "application_statuses" in result["charts"]

    assert "user_mix" in result["charts"]


# ==================================================
# BDD Then: Revenue
# ==================================================


@then("the current-year revenue should be calculated correctly")
def verify_current_year_revenue(context):
    assert context.response is not None

    assert context.response.status_code == 200

    result = context.data

    assert result["metrics"]["current_year_revenue"] == 300.50

    assert result["metrics"]["completed_transactions"] == 3


# ==================================================
# BDD Then: Access Denied
# ==================================================


@then("access to the dashboard analytics should be denied")
def verify_access_denied(context):
    assert context.response is not None

    assert context.response.status_code == 401

    assert context.response.json()["detail"] == "Admin login required"
