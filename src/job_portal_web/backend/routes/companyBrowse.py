from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")

db = firestore.client()


# ======================================================
# Get Optional Logged-In User
# ======================================================


def get_optional_user(request: Request):
    """
    Return job-seeker information when logged in.

    Visitors who are not logged in can still access
    the company browsing page.
    """

    if request.session.get("user_type") != "job_seeker":
        return None

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        return None

    applicant_document = db.collection("job_seeker").document(applicant_id).get()

    if not applicant_document.exists:
        return None

    user = applicant_document.to_dict()
    user["id"] = applicant_document.id

    return user


# ======================================================
# Browse Companies
# ======================================================


@router.get(
    "/companies",
    response_class=HTMLResponse,
)
async def browse_companies(
    request: Request,
    keyword: str = "",
    page: int = 1,
):
    # Logged-in user information is optional.
    user = get_optional_user(request)

    per_page = 12
    companies = []

    keyword = keyword.strip().lower()

    # Prevent invalid page numbers.
    if page < 1:
        page = 1

    # ==================================================
    # Retrieve Active Companies
    # ==================================================

    company_documents = db.collection("company").where("status", "==", "Active").stream()

    for document in company_documents:
        company = document.to_dict()

        if company.get("status") != "Active":
            continue

        company_id = document.id

        company_name = (
            company.get("companyName")
            or company.get("company_name")
            or company.get("name")
            or "Unknown Company"
        )

        city = company.get("city", "")
        state = company.get("state", "")

        location_parts = [part for part in (city, state) if part]

        location = ", ".join(location_parts)

        industry = company.get("industry_id") or company.get("industry") or ""

        # ==============================================
        # Search
        # ==============================================

        if keyword:
            searchable_text = (f"{company_name} " f"{location} " f"{industry}").lower()

            if keyword not in searchable_text:
                continue

        # ==============================================
        # Count Active Jobs
        # ==============================================

        job_documents = (
            db.collection("job_list")
            .where("company_id", "==", company_id)
            .where("status", "==", "Active")
            .stream()
        )

        job_count = sum(1 for _ in job_documents)

        # ==============================================
        # Calculate Company Rating
        # ==============================================

        review_documents = (
            db.collection("company_review").where("company_id", "==", company_id).stream()
        )

        total_rating = 0
        review_count = 0

        for review_document in review_documents:
            review_data = review_document.to_dict()

            total_rating += review_data.get(
                "overall_rating",
                0,
            )

            review_count += 1

        if review_count > 0:
            average_rating = round(
                total_rating / review_count,
                1,
            )
        else:
            average_rating = 0

        # ==============================================
        # Add Company
        # ==============================================

        companies.append(
            {
                "id": company_id,
                "company_name": company_name,
                "logo": company.get("logo", ""),
                "industry": industry,
                "location": location,
                "rating": average_rating,
                "review_count": review_count,
                "job_count": job_count,
            }
        )

    # ==================================================
    # Sort by Highest Rating
    # ==================================================

    companies.sort(
        key=lambda item: (
            item["rating"],
            item["review_count"],
        ),
        reverse=True,
    )

    # ==================================================
    # Pagination
    # ==================================================

    total_company = len(companies)

    total_pages = max(
        1,
        (total_company + per_page - 1) // per_page,
    )

    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page

    displayed_companies = companies[start:end]

    # ==================================================
    # Render Page
    # ==================================================

    return templates.TemplateResponse(
        request=request,
        name="companyBrowse.html",
        context={
            "user": user,
            "companies": displayed_companies,
            "keyword": keyword,
            "page": page,
            "total_pages": total_pages,
            "total_company": total_company,
            "active_page": "companies",
        },
    )
