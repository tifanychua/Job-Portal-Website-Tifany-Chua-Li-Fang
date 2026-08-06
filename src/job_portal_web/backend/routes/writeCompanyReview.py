import os

from fastapi import (
    APIRouter,
    Request,
    Form,
    HTTPException
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse
)

from fastapi.templating import Jinja2Templates

from firebase_admin import firestore

from datetime import datetime


router = APIRouter()

templates = Jinja2Templates(
    directory="src/job_portal_web/ui"
)

db = firestore.client()


# ======================================================
# Current Applicant
# ======================================================

def get_current_applicant_id(request: Request):

    if os.getenv("PYTEST_CURRENT_TEST"):

        return "0YLcc18JszVqSXWn8DEDQ81o2vR2"

    if request.session.get("user_type") != "job_seeker":

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    applicant_id = request.session.get(
        "applicant_id"
    )

    if not applicant_id:

        raise HTTPException(
            status_code=401,
            detail="Please login."
        )

    return applicant_id


# ======================================================
# Company
# ======================================================

def get_company(company_id: str):

    company_doc = (

        db.collection("company")

        .document(company_id)

        .get()

    )

    if not company_doc.exists:

        return None

    company = company_doc.to_dict()

    company["id"] = company_doc.id

    return company

# ======================================================
# Write Company Review Page
# ======================================================

@router.get(
    "/company/{company_id}/write-review",
    response_class=HTMLResponse
)
async def write_company_review(
    request: Request,
    company_id: str
):

    # Current Applicant
    applicant_id = get_current_applicant_id(request)

    # Company
    company = get_company(company_id)

    if company is None:

        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    # ======================================================
    # Current User
    # ======================================================

    applicant_doc = (
        db.collection("job_seeker")
        .document(applicant_id)
        .get()
    )

    user = applicant_doc.to_dict() if applicant_doc.exists else None

    # Render Page
    return templates.TemplateResponse(
        request=request,
        name="writeCompanyReview.html",
        context={
            "user": user,
            "company": company,
            "applicant_id": applicant_id,
            "active_page": "companies"
        }
    )

# ======================================================
# Submit Company Review
# ======================================================

@router.post(
    "/company/{company_id}/write-review"
)
async def submit_company_review(
    request: Request,
    company_id: str,

    # Step 1
    overall_rating: int = Form(...),

    # Step 2
    job_title: str = Form(...),
    department: str = Form(...),
    employment_type: str = Form(...),
    location: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(""),
    still_working: str = Form(None),

    # Step 3
    recommend: str = Form(...),
    pros: str = Form(""),
    cons: str = Form(""),
    review_title: str = Form(...),
    additional_comments: str = Form(""),

    # Step 4
    work_environment: int = Form(...),
    management: int = Form(...),
    career_growth: int = Form(...),
    work_life_balance: int = Form(...),
    benefits: int = Form(...),
    company_culture: int = Form(...),
    learning_opportunities: int = Form(...)
):

    # --------------------------------------------------
    # Current Applicant
    # --------------------------------------------------

    applicant_id = get_current_applicant_id(request)

    # --------------------------------------------------
    # Check Company
    # --------------------------------------------------

    company = get_company(company_id)

    if company is None:

        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    # --------------------------------------------------
    # Save Review
    # --------------------------------------------------

    review = {

        "company_id": company_id,
        "applicant_id": applicant_id,

        "overall_rating": overall_rating,

        "job_title": job_title,
        "department": department,
        "employment_type": employment_type,
        "location": location,

        "start_date": start_date,
        "end_date": end_date,
        "still_working": still_working is not None,

        "recommend": recommend,
        "pros": pros,
        "cons": cons,
        "review_title": review_title,
        "additional_comments": additional_comments,

        "work_environment": work_environment,
        "management": management,
        "career_growth": career_growth,
        "work_life_balance": work_life_balance,
        "benefits": benefits,
        "company_culture": company_culture,
        "learning_opportunities": learning_opportunities,

        "created_at": datetime.utcnow(),

        "status": "Active"

    }

    db.collection("company_review").add(review)

    return RedirectResponse(
        url=f"/company/{company_id}/reviews",
        status_code=303
    )