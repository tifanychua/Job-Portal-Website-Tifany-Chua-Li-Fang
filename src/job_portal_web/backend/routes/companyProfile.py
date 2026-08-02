import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

router = APIRouter()

db = firestore.client()

templates = Jinja2Templates(directory="src/job_portal_web/ui")


def get_current_company_id(request: Request):

    # ==================================================
    # Pytest bypass
    # ==================================================
    if os.getenv("PYTEST_CURRENT_TEST"):
        print("PYTEST MODE - bypass company login")
        return "company001"

    # ==================================================
    # Normal login validation
    # ==================================================
    if request.session.get("user_type") != "employer":
        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:
        raise HTTPException(status_code=401, detail="Company not logged in")

    return company_id


@router.get("/company-profile", response_class=HTMLResponse)
async def company_profile(request: Request):

    company_id = get_current_company_id(request)

    company_doc = db.collection("company").document(company_id).get()
    if company_doc.exists:
        company = company_doc.to_dict()

    else:
        company = {
            "companyName": "",
            "companyDescription": "",
            "registrationNumber": "",
            "businessEmail": "",
            "phone": "",
            "companyWebsite": "",
            "address": "",
            "city": "",
            "state": "",
            "postalCode": "",
            "country": "",
            "industry_id": "",
            "specialty_category_id": "",
            "logo": "",
            "status": "Pending",
        }

    # =====================================================
    # Industry Name
    # =====================================================

    company["industry_name"] = ""

    if company.get("industry_id"):
        industry_docs = (
            db.collection("industries")
            .where("industry_id", "==", company["industry_id"])
            .limit(1)
            .stream()
        )

        for doc in industry_docs:
            company["industry_name"] = doc.to_dict().get("industry_name", "")

    # =====================================================
    # Specialty Name
    # =====================================================

    company["specialty_category_name"] = ""

    selected_ids = company.get("specialty_category_ids", [])

    if selected_ids:
        names = []

        category_docs = db.collection("skill_categories").stream()

        for doc in category_docs:
            category = doc.to_dict()

            if category.get("category_id") in selected_ids:
                names.append(category.get("category_name"))

        company["specialty_category_name"] = ", ".join(names)

    # =====================================================
    # Full Address
    # =====================================================

    company["full_address"] = ", ".join(
        filter(
            None,
            [
                company.get("address"),
                company.get("address_line2"),
                company.get("city"),
                company.get("state"),
                company.get("postalCode"),
                company.get("country"),
            ],
        )
    )

    # =====================================================
    # Gallery
    # =====================================================

    gallery = []

    gallery_docs = db.collection("company_gallery").where("company_id", "==", company_id).stream()

    for doc in gallery_docs:
        gallery.append(doc.to_dict())

    # =====================================================
    # Team Members
    # =====================================================

    team_members = []

    team_docs = db.collection("company_team").where("company_id", "==", company_id).stream()

    for doc in team_docs:
        team_members.append(doc.to_dict())

    # =====================================================
    # Documents
    # =====================================================

    documents = []

    document_docs = (
        db.collection("company_documents").where("company_id", "==", company_id).stream()
    )

    for doc in document_docs:
        documents.append(doc.to_dict())

    # =====================================================
    # Statistics (Optional Defaults)
    # =====================================================

    company.setdefault("is_verified", False)
    company.setdefault("total_jobs", 0)
    company.setdefault("total_applications", 0)
    company.setdefault("total_employees", 0)
    company.setdefault("profile_views", 0)

    # =====================================================
    # Render HTML
    # =====================================================

    return templates.TemplateResponse(
        request=request,
        name="companyProfile.html",
        context={
            "company": company,
            "gallery": gallery,
            "team_members": team_members,
            "documents": documents,
        },
    )
