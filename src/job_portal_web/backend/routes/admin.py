from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from ..database import db
from ..email_service import (
    send_company_verification_email,
)

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")


# ==================================
# Email Helper
# ==================================


async def send_company_status_email(
    company: dict,
    status: str,
):
    company_email = (
        company.get("email") or company.get("company_email") or company.get("companyEmail")
    )

    company_name = company.get("companyName") or company.get("company_name") or "Company"

    # Some old, invalid or test records may not
    # contain an email address.
    if not company_email:
        return

    await send_company_verification_email(
        email=company_email,
        company_name=company_name,
        status=status,
    )


# ==================================
# Company Registration Requests
# ==================================


@router.get("/admin/company-requests")
def company_requests(
    request: Request,
    status: str = "Pending",
):
    companies = []

    company_docs = db.collection("company").stream()

    for doc in company_docs:
        company = doc.to_dict() or {}

        company["company_id"] = doc.id

        if status != "All":
            if company.get("status") != status:
                continue

        companies.append(company)

    return templates.TemplateResponse(
        request=request,
        name="companyRequests.html",
        context={
            "companies": companies,
            "active_page": "company-verification",
            "current_status": status,
        },
    )


# ==================================
# Review Company Details
# ==================================


@router.get("/admin/company/{company_id}")
def review_company(
    request: Request,
    company_id: str,
):
    company_doc = db.collection("company").document(company_id).get()

    company: dict[str, Any] = {}
    if company_doc.exists:
        company = company_doc.to_dict() or {}
        company["company_id"] = company_id

    return templates.TemplateResponse(
        request=request,
        name="reviewCompanyRequest.html",
        context={
            "company": company,
            "active_page": "company-verification",
        },
    )


# ==================================
# Approve Company
# ==================================


@router.post("/admin/company/{company_id}/approve")
async def approve_company(company_id: str):
    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    if not company_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company = company_doc.to_dict() or {}

    company_ref.update(
        {
            "status": "Active",
        }
    )

    await send_company_status_email(
        company=company,
        status="Approved",
    )

    return RedirectResponse(
        url="/admin/company-requests",
        status_code=303,
    )


# ==================================
# Reject Company
# ==================================


@router.post("/admin/company/{company_id}/reject")
async def reject_company(company_id: str):
    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    if not company_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company = company_doc.to_dict() or {}

    company_ref.update(
        {
            "status": "Rejected",
        }
    )

    await send_company_status_email(
        company=company,
        status="Rejected",
    )

    return RedirectResponse(
        url="/admin/company-requests",
        status_code=303,
    )


# ==================================
# Deactivate Company
# ==================================


@router.post("/admin/company/{company_id}/deactivate")
def deactivate_company(company_id: str):
    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    if not company_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company_ref.update(
        {
            "status": "Deactivated",
        }
    )

    return RedirectResponse(
        url=("/admin/company-requests?status=Active"),
        status_code=303,
    )
