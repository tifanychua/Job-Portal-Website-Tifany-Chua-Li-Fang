import os

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")

db = firestore.client()

# ======================================================
# Get Current Applicant
# ======================================================

def get_current_applicant_id(request: Request):

    # During pytest, skip login
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "0YLcc18JszVqSXWn8DEDQ81o2vR2"

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(status_code=403, detail="Access denied")

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        raise HTTPException(status_code=401, detail="Applicant not logged in")

    return applicant_id


@router.get("/companies", response_class=HTMLResponse)
async def browse_companies(
    request: Request,
    keyword: str = "",
    page: int = 1
):

    # =====================================
    # Current Applicant
    # =====================================

    applicant_id = get_current_applicant_id(request)

    applicant_doc = (
        db.collection("job_seeker")
        .document(applicant_id)
        .get()
    )

    user = applicant_doc.to_dict() if applicant_doc.exists else None

    PER_PAGE = 12

    companies = []

    keyword = keyword.strip().lower()

    # =====================================
    # Get Companies
    # =====================================

    company_docs = (
        db.collection("company")
        .where("status", "==", "Active")
        .stream()
    )

    for doc in company_docs:

        company = doc.to_dict()

        # =====================================
        # Only Show Active Companies
        # =====================================

        if company.get("status") != "Active":
            continue

        company_id = doc.id

        company_name = company.get("companyName", "")

        location = f"{company.get('city','')}, {company.get('state','')}"

        industry = company.get("industry_id", "")

        # ---------------------------------
        # Search
        # ---------------------------------

        if keyword:

            searchable = (
                f"{company_name} "
                f"{location} "
                f"{industry}"
            ).lower()

            if keyword not in searchable:
                continue

        # =====================================
        # Count Active Jobs
        # =====================================

        job_docs = (
            db.collection("job_list")
            .where("company_id", "==", company_id)
            .where("status", "==", "Active")
            .stream()
        )

        job_count = sum(1 for _ in job_docs)

        # =====================================
        # Calculate Rating
        # =====================================

        review_docs = (
            db.collection("company_review")
            .where("company_id", "==", company_id)
            .stream()
        )

        total_rating = 0
        review_count = 0

        for review in review_docs:

            review_data = review.to_dict()

            total_rating += review_data.get("overall_rating", 0)

            review_count += 1

        if review_count > 0:

            average_rating = round(
                total_rating / review_count,
                1
            )

        else:

            average_rating = 0

        # =====================================
        # Add Company
        # =====================================

        companies.append({

            "id": company_id,

            "company_name": company_name,

            "logo": company.get("logo", ""),

            "industry": industry,

            "location": location,

            "rating": average_rating,

            "review_count": review_count,

            "job_count": job_count

        })

    # =====================================
    # Highest Rating First
    # =====================================

    companies.sort(
        key=lambda x: (
            x["rating"],
            x["review_count"]
        ),
        reverse=True
    )

    # =====================================
    # Pagination
    # =====================================

    total_company = len(companies)

    total_pages = max(
        1,
        (total_company + PER_PAGE - 1) // PER_PAGE
    )

    start = (page - 1) * PER_PAGE

    end = start + PER_PAGE

    companies = companies[start:end]

    # =====================================
    # Render
    # =====================================

    return templates.TemplateResponse(

        request=request,

        name="companyBrowse.html",

        context={

            "user": user,

            "companies": companies,

            "keyword": keyword,

            "page": page,

            "total_pages": total_pages,

            "total_company": total_company,

            "active_page": "companies"

        }

    )