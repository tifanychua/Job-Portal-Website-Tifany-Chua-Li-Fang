from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from ..database import db

router = APIRouter()


templates = Jinja2Templates(directory="src/job_portal_web/ui")


# ==================================
# Company Registration Requests
# ==================================


@router.get("/admin/company-requests")
def company_requests(request: Request):

    companies = []

    # Get all company documents
    company_docs = db.collection("company").stream()

    for doc in company_docs:

        company = doc.to_dict()

        # Add document ID
        company["company_id"] = doc.id

        # Only display Pending companies

        if company.get("status") == "Pending":

            companies.append(company)

    return templates.TemplateResponse(
        request=request,
        name="companyRequests.html",
        context={"companies": companies, "active_page": "company-verification"},
    )


# ==================================
# Review Company Details
# ==================================


@router.get("/admin/company/{company_id}")
def review_company(request: Request, company_id: str):

    company_doc = db.collection("company").document(company_id).get()

    company = {}

    if company_doc.exists:

        company = company_doc.to_dict()

        company["company_id"] = company_id

    return templates.TemplateResponse(
        request=request,
        name="reviewCompanyRequest.html",
        context={"company": company, "active_page": "company-verification"},
    )


# ==================================
# Approve Company
# ==================================


@router.post("/admin/company/{company_id}/approve")
def approve_company(company_id: str):

    company_ref = db.collection("company").document(company_id)

    company_ref.update({"status": "Approved"})

    return RedirectResponse(url="/admin/company-requests", status_code=303)


# ==================================
# Reject Company
# ==================================


@router.post("/admin/company/{company_id}/reject")
def reject_company(company_id: str):

    company_ref = db.collection("company").document(company_id)

    company_ref.update({"status": "Rejected"})

    return RedirectResponse(url="/admin/company-requests", status_code=303)
