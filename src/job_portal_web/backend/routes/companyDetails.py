from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")

db = firestore.client()


# ======================================================
# Optional Current User
# ======================================================


def get_current_user(request: Request):
    """
    Return the logged-in job seeker's information.

    Visitors who are not logged in can still view
    company details, jobs, and reviews.
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
# Company Information
# ======================================================


def get_company(company_id: str):
    company_document = db.collection("company").document(company_id).get()

    if not company_document.exists:
        return None

    company = company_document.to_dict()

    company["id"] = company_document.id

    company["company_name"] = (
        company.get("companyName")
        or company.get("company_name")
        or company.get("name")
        or "Unknown Company"
    )

    company["location"] = ", ".join(
        filter(
            None,
            [
                company.get("city"),
                company.get("state"),
                company.get("country"),
            ],
        )
    )

    return company


# ======================================================
# Company Jobs
# ======================================================


def get_company_jobs(company_id: str):
    jobs = []

    job_documents = (
        db.collection("job_list")
        .where("company_id", "==", company_id)
        .where("status", "==", "Active")
        .stream()
    )

    for document in job_documents:
        job = document.to_dict()
        job["id"] = document.id

        # ==============================================
        # Salary Display
        # ==============================================

        salary_type = str(job.get("salaryType", "")).lower().strip()

        if salary_type == "fixed":
            salary = job.get("salary", "")

            try:
                salary = float(str(salary).replace(",", ""))

                job["salary_display"] = f"RM {salary:,.0f}"

            except (ValueError, TypeError):
                job["salary_display"] = "Negotiable"

        elif salary_type == "range":
            minimum = job.get("minSalary", "")
            maximum = job.get("maxSalary", "")

            try:
                minimum = float(str(minimum).replace(",", ""))

                maximum = float(str(maximum).replace(",", ""))

                job["salary_display"] = f"RM {minimum:,.0f} - " f"RM {maximum:,.0f}"

            except (ValueError, TypeError):
                job["salary_display"] = "Negotiable"

        else:
            job["salary_display"] = "Negotiable"

        jobs.append(job)

    return jobs


# ======================================================
# Company Review Summary
# ======================================================


def get_company_review_summary(company_id: str):
    reviews = []

    review_documents = (
        db.collection("company_review")
        .where("company_id", "==", company_id)
        .where("status", "==", "Active")
        .stream()
    )

    total_rating = 0
    total_work_environment = 0
    total_management = 0
    total_career_growth = 0
    total_work_life_balance = 0
    total_benefits = 0
    total_company_culture = 0
    total_learning = 0

    five_star = 0
    four_star = 0
    three_star = 0
    two_star = 0
    one_star = 0

    for document in review_documents:
        review = document.to_dict()
        review["id"] = document.id

        reviews.append(review)

        rating = review.get("overall_rating", 0)

        total_rating += rating

        total_work_environment += review.get(
            "work_environment",
            0,
        )

        total_management += review.get(
            "management",
            0,
        )

        total_career_growth += review.get(
            "career_growth",
            0,
        )

        total_work_life_balance += review.get(
            "work_life_balance",
            0,
        )

        total_benefits += review.get(
            "benefits",
            0,
        )

        total_company_culture += review.get(
            "company_culture",
            0,
        )

        total_learning += review.get(
            "learning_opportunities",
            0,
        )

        if rating == 5:
            five_star += 1
        elif rating == 4:
            four_star += 1
        elif rating == 3:
            three_star += 1
        elif rating == 2:
            two_star += 1
        elif rating == 1:
            one_star += 1

    review_count = len(reviews)

    if review_count > 0:
        summary = {
            "rating": round(
                total_rating / review_count,
                1,
            ),
            "review_count": review_count,
            "work_environment_avg": round(
                total_work_environment / review_count,
                1,
            ),
            "management_avg": round(
                total_management / review_count,
                1,
            ),
            "career_growth_avg": round(
                total_career_growth / review_count,
                1,
            ),
            "work_life_balance_avg": round(
                total_work_life_balance / review_count,
                1,
            ),
            "benefits_avg": round(
                total_benefits / review_count,
                1,
            ),
            "company_culture_avg": round(
                total_company_culture / review_count,
                1,
            ),
            "learning_opportunities_avg": round(
                total_learning / review_count,
                1,
            ),
            "five_star": five_star,
            "four_star": four_star,
            "three_star": three_star,
            "two_star": two_star,
            "one_star": one_star,
        }

    else:
        summary = {
            "rating": 0,
            "review_count": 0,
            "work_environment_avg": 0,
            "management_avg": 0,
            "career_growth_avg": 0,
            "work_life_balance_avg": 0,
            "benefits_avg": 0,
            "company_culture_avg": 0,
            "learning_opportunities_avg": 0,
            "five_star": 0,
            "four_star": 0,
            "three_star": 0,
            "two_star": 0,
            "one_star": 0,
        }

    return reviews, summary


# ======================================================
# Company Details
# ======================================================


@router.get(
    "/company/{company_id}",
    response_class=HTMLResponse,
)
async def company_details(
    request: Request,
    company_id: str,
):
    # User is optional.
    user = get_current_user(request)

    company = get_company(company_id)

    if company is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "user": user,
                "active_page": "companies",
            },
            status_code=404,
        )

    jobs = get_company_jobs(company_id)

    company["job_count"] = len(jobs)

    # Display only the latest five jobs.
    display_jobs = jobs[:5]

    reviews, summary = get_company_review_summary(company_id)

    company.update(summary)

    return templates.TemplateResponse(
        request=request,
        name="companyDetails.html",
        context={
            "user": user,
            "company": company,
            "jobs": display_jobs,
            "total_jobs": len(jobs),
            "active_page": "companies",
        },
    )


# ======================================================
# Company Jobs
# ======================================================


@router.get(
    "/company/{company_id}/jobs",
    response_class=HTMLResponse,
)
async def company_jobs(
    request: Request,
    company_id: str,
):
    # User is optional.
    user = get_current_user(request)

    company = get_company(company_id)

    if company is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "user": user,
                "active_page": "companies",
            },
            status_code=404,
        )

    jobs = get_company_jobs(company_id)

    company["job_count"] = len(jobs)

    reviews, summary = get_company_review_summary(company_id)

    company.update(summary)

    return templates.TemplateResponse(
        request=request,
        name="companyJobs.html",
        context={
            "user": user,
            "company": company,
            "jobs": jobs,
            "total_jobs": len(jobs),
            "active_page": "companies",
        },
    )


# ======================================================
# Company Reviews
# ======================================================


@router.get(
    "/company/{company_id}/reviews",
    response_class=HTMLResponse,
)
async def company_reviews(
    request: Request,
    company_id: str,
):
    # User is optional.
    user = get_current_user(request)

    company = get_company(company_id)

    if company is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "user": user,
                "active_page": "companies",
            },
            status_code=404,
        )

    reviews, summary = get_company_review_summary(company_id)

    company.update(summary)

    jobs = get_company_jobs(company_id)

    company["job_count"] = len(jobs)

    return templates.TemplateResponse(
        request=request,
        name="companyReviews.html",
        context={
            "user": user,
            "company": company,
            "reviews": reviews,
            "active_page": "companies",
        },
    )
