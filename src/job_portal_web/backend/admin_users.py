from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from job_portal_web.backend.database import db


router = APIRouter()

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
TEMPLATE_DIRECTORY = PROJECT_DIRECTORY / "ui"
templates = Jinja2Templates(directory=str(TEMPLATE_DIRECTORY))

ACCOUNT_COLLECTIONS = {
    "job_seeker": "job_seeker",
    "employer": "company",
}

ACCOUNT_STATUS_LABELS = {
    "active": "Active",
    "suspended": "Suspended",
    "deactivated": "Deactivated",
}


class AccountStatusPayload(BaseModel):
    status: Literal["Active", "Suspended", "Deactivated"]
    reason: str = Field(default="", max_length=300)


def is_admin(request: Request) -> bool:
    role = request.session.get("user_type") or request.session.get("userType")
    return str(role or "").strip().lower() == "admin"


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Administrator access is required.")


def current_admin_id(request: Request) -> str:
    value = (
        request.session.get("admin_id")
        or request.session.get("user_id")
        or request.session.get("userId")
        or "unknown"
    )
    return str(value)


def first_value(record: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def account_status(record: dict) -> str:
    raw_status = first_value(
        record,
        "accountStatus",
        "account_status",
        default="Active",
    )
    normalized = raw_status.strip().lower()
    return ACCOUNT_STATUS_LABELS.get(normalized, "Active")


def timestamp_number(value) -> float:
    try:
        return value.timestamp()
    except (AttributeError, TypeError, ValueError):
        return 0.0


def display_date(value) -> str:
    if not value:
        return "Not available"

    try:
        return value.strftime("%d %b %Y")
    except (AttributeError, TypeError, ValueError):
        return str(value)


def normalize_job_seeker(document) -> dict:
    record = document.to_dict() or {}

    first_name = first_value(record, "firstName", "first_name")
    last_name = first_value(record, "lastName", "last_name")
    combined_name = " ".join(part for part in (first_name, last_name) if part)

    name = first_value(
        record,
        "fullName",
        "full_name",
        "name",
        "username",
        default=combined_name or "Unnamed job seeker",
    )

    created_at = (
        record.get("createdAt")
        or record.get("created_at")
        or record.get("registeredAt")
        or record.get("registered_at")
    )

    return {
        "id": document.id,
        "account_type": "job_seeker",
        "account_type_label": "Job Seeker",
        "name": name,
        "email": first_value(record, "email", "emailAddress", default="No email"),
        "phone": first_value(record, "phone", "phoneNumber", default="Not provided"),
        "image_url": first_value(
            record,
            "profileImage",
            "profile_image",
            "profilePicture",
            "photoURL",
        ),
        "status": account_status(record),
        "created_at": created_at,
        "created_display": display_date(created_at),
    }


def normalize_employer(document) -> dict:
    record = document.to_dict() or {}
    created_at = (
        record.get("createdAt")
        or record.get("created_at")
        or record.get("registeredAt")
        or record.get("registered_at")
    )

    return {
        "id": document.id,
        "account_type": "employer",
        "account_type_label": "Employer",
        "name": first_value(
            record,
            "companyName",
            "company_name",
            "name",
            default="Unnamed employer",
        ),
        "email": first_value(
            record,
            "companyEmail",
            "email",
            "emailAddress",
            default="No email",
        ),
        "phone": first_value(
            record,
            "companyPhone",
            "phone",
            "phoneNumber",
            default="Not provided",
        ),
        "image_url": first_value(record, "logo", "companyLogo", "logoUrl"),
        "status": account_status(record),
        "created_at": created_at,
        "created_display": display_date(created_at),
    }


def get_registered_accounts() -> list[dict]:
    accounts = []

    for document in db.collection("job_seeker").stream():
        accounts.append(normalize_job_seeker(document))

    for document in db.collection("company").stream():
        accounts.append(normalize_employer(document))

    accounts.sort(
        key=lambda account: (
            timestamp_number(account.get("created_at")),
            account.get("name", "").lower(),
        ),
        reverse=True,
    )

    return accounts


def get_account_counts(accounts: list[dict]) -> dict:
    return {
        "total": len(accounts),
        "active": sum(account["status"] == "Active" for account in accounts),
        "suspended": sum(
            account["status"] == "Suspended" for account in accounts
        ),
        "deactivated": sum(
            account["status"] == "Deactivated" for account in accounts
        ),
    }


@router.get("/admin/users", response_class=HTMLResponse)
def admin_user_management_page(request: Request):
    if not is_admin(request):
        return RedirectResponse("/login/admin", status_code=303)

    accounts = get_registered_accounts()

    return templates.TemplateResponse(
        request=request,
        name="adminUserManagement.html",
        context={
            "accounts": accounts,
            "counts": get_account_counts(accounts),
            "active_page": "users",
        },
    )


@router.patch("/api/admin/users/{account_type}/{user_id}/status")
def update_account_status(
    account_type: str,
    user_id: str,
    payload: AccountStatusPayload,
    request: Request,
):
    require_admin(request)

    collection_name = ACCOUNT_COLLECTIONS.get(account_type)
    if not collection_name:
        raise HTTPException(status_code=404, detail="Account type was not found.")

    reason = payload.reason.strip()
    if payload.status != "Active" and not reason:
        raise HTTPException(
            status_code=422,
            detail="Please provide a reason for restricting this account.",
        )

    account_reference = db.collection(collection_name).document(user_id)
    snapshot = account_reference.get()

    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="User account was not found.")

    previous_record = snapshot.to_dict() or {}
    previous_status = account_status(previous_record)
    changed_at = datetime.now(timezone.utc)
    changed_by = current_admin_id(request)

    account_reference.update(
        {
            "accountStatus": payload.status,
            "accountStatusReason": reason if payload.status != "Active" else "",
            "accountStatusUpdatedAt": changed_at,
            "accountStatusUpdatedBy": changed_by,
        }
    )

    db.collection("account_status_audit").add(
        {
            "accountId": user_id,
            "accountType": account_type,
            "previousStatus": previous_status,
            "newStatus": payload.status,
            "reason": reason,
            "changedAt": changed_at,
            "changedBy": changed_by,
        }
    )

    action_message = {
        "Active": "Account reactivated successfully.",
        "Suspended": "Account suspended successfully.",
        "Deactivated": "Account deactivated successfully.",
    }[payload.status]

    return JSONResponse(
        content={
            "success": True,
            "status": payload.status,
            "message": action_message,
        }
    )


def ensure_account_can_log_in(account_record: dict) -> None:
    """Call this from login after credentials are valid."""
    status = account_status(account_record)

    if status == "Suspended":
        raise HTTPException(
            status_code=403,
            detail="This account is currently suspended. Please contact support.",
        )

    if status == "Deactivated":
        raise HTTPException(
            status_code=403,
            detail="This account has been deactivated. Please contact support.",
        )
