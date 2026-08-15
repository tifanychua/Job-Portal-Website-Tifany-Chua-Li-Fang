import logging
from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..database import db

router = APIRouter(tags=["Admin dashboard analytics"])

CURRENT_YEAR = datetime.now(UTC).year
MONTH_LABELS = [
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

logger = logging.getLogger(__name__)


def _is_admin(request: Request) -> bool:
    """Support the common admin session fields used across the project."""
    session = request.session
    role = (
        str(session.get("user_type") or session.get("role") or session.get("account_type") or "")
        .strip()
        .lower()
    )

    return (
        role in {"admin", "administrator"}
        or bool(session.get("admin_id"))
        or session.get("is_admin") is True
    )


def _safe_stream(collection_name: str) -> list[dict[str, Any]]:
    """Read a collection without breaking the whole dashboard if it is empty."""
    records: list[dict[str, Any]] = []

    try:
        for document in db.collection(collection_name).stream():
            data = document.to_dict() or {}
            data["_document_id"] = document.id
            records.append(data)
    except Exception:
        # A dashboard should still render if one optional collection is unavailable.
        return []

    return records


def _first_collection_with_data(names: Iterable[str]) -> list[dict[str, Any]]:
    """Handle old and new Firestore collection names used by the project."""
    for name in names:
        records = _safe_stream(name)
        if records:
            return records
    return []


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    if hasattr(value, "to_datetime"):
        try:
            converted = value.to_datetime()
            if converted.tzinfo is None:
                converted = converted.replace(tzinfo=UTC)
            return converted
        except (TypeError, ValueError, AttributeError):
            pass

    if isinstance(value, str):
        cleaned = value.strip().replace("Z", "+00:00")
        if not cleaned:
            return None

        for parser in (
            lambda text: datetime.fromisoformat(text),
            lambda text: datetime.strptime(text, "%Y-%m-%d"),
            lambda text: datetime.strptime(text, "%d/%m/%Y"),
        ):
            try:
                converted = parser(cleaned)
                if converted.tzinfo is None:
                    converted = converted.replace(tzinfo=UTC)
                return converted
            except ValueError:
                continue

    return None


def _record_date(record: dict[str, Any], *keys: str) -> datetime | None:
    for key in keys:
        converted = _as_datetime(record.get(key))
        if converted:
            return converted
    return None


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _normalise_status(value: Any, default: str) -> str:
    status = str(value or default).strip().replace("_", " ")
    return status.title() if status else default


def _company_name(company_id: str, cache: dict[str, str]) -> str:
    if not company_id:
        return "Unknown company"

    if company_id in cache:
        return cache[company_id]

    name = "Unknown company"
    try:
        document = db.collection("company").document(company_id).get()
        if document.exists:
            company = document.to_dict() or {}
            name = (
                company.get("companyName")
                or company.get("company_name")
                or company.get("name")
                or name
            )
    except Exception as exc:
        logger.warning(
            "Unable to retrieve company name for %s: %s",
            company_id,
            exc,
        )

    cache[company_id] = name
    return name


@router.get("/admin/dashboard/analytics-data")
def admin_dashboard_analytics_data(request: Request):
    """Return the live data used by admin_dashboard.html."""
    if not _is_admin(request):
        raise HTTPException(status_code=401, detail="Admin login required")

    job_seekers = _safe_stream("job_seeker")
    companies = _safe_stream("company")
    jobs = _first_collection_with_data(("job_list", "jobs"))
    applications = _first_collection_with_data(("application", "applications"))
    payments = _safe_stream("payment")

    active_jobs = sum(
        1
        for job in jobs
        if str(job.get("status", "")).strip().lower() in {"active", "open", "published"}
    )

    application_statuses = Counter(
        _normalise_status(
            application.get("status") or application.get("applicationStatus"),
            "Submitted",
        )
        for application in applications
    )

    payment_statuses: Counter[str] = Counter()
    monthly_revenue = [0.0] * 12
    current_year_revenue = 0.0
    completed_transactions = 0

    for payment in payments:
        status = str(payment.get("status", "")).strip().upper() or "UNKNOWN"
        payment_statuses[status] += 1

        if status != "COMPLETED":
            continue

        completed_transactions += 1
        payment_date = _record_date(payment, "completed_at", "created_at")
        amount = _number(payment.get("amount"))

        if payment_date and payment_date.year == CURRENT_YEAR:
            current_year_revenue += amount
            monthly_revenue[payment_date.month - 1] += amount

    recent_payment_records: list[tuple[datetime, dict[str, Any]]] = []
    oldest_date = datetime.min.replace(tzinfo=UTC)

    for payment in payments:
        payment_date = _record_date(payment, "completed_at", "created_at")
        recent_payment_records.append((payment_date or oldest_date, payment))

    recent_payment_records.sort(key=lambda item: item[0], reverse=True)
    company_cache: dict[str, str] = {}
    recent_transactions = []

    for payment_date, payment in recent_payment_records[:6]:
        transaction_id = str(payment.get("_document_id", ""))
        company_id = str(payment.get("company_id", "") or "")
        status = str(payment.get("status", "UNKNOWN")).strip().upper()

        recent_transactions.append(
            {
                "transaction_id": transaction_id,
                "company_name": _company_name(company_id, company_cache),
                "package": payment.get("package_name") or payment.get("package") or "—",
                "amount": round(_number(payment.get("amount")), 2),
                "status": status,
                "date": (
                    payment_date.strftime("%d %b %Y, %I:%M %p")
                    if payment_date != oldest_date
                    else "Date unavailable"
                ),
            }
        )

    application_items = application_statuses.most_common(7)

    return {
        "generated_at": datetime.now(UTC).strftime("%d %b %Y, %I:%M %p UTC"),
        "current_year": CURRENT_YEAR,
        "metrics": {
            "total_users": len(job_seekers) + len(companies),
            "job_seekers": len(job_seekers),
            "employers": len(companies),
            "active_jobs": active_jobs,
            "applications": len(applications),
            "completed_transactions": completed_transactions,
            "current_year_revenue": round(current_year_revenue, 2),
        },
        "transaction_statuses": {
            "completed": payment_statuses.get("COMPLETED", 0),
            "pending": payment_statuses.get("PENDING", 0),
            "failed": payment_statuses.get("FAILED", 0),
        },
        "charts": {
            "monthly_revenue": {
                "labels": MONTH_LABELS,
                "values": [round(value, 2) for value in monthly_revenue],
            },
            "application_statuses": {
                "labels": [label for label, _ in application_items],
                "values": [value for _, value in application_items],
            },
            "user_mix": {
                "labels": ["Job seekers", "Employers"],
                "values": [len(job_seekers), len(companies)],
            },
        },
        "recent_transactions": recent_transactions,
    }
