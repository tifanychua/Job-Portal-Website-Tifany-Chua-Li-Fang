from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from .database import db
from collections import Counter

import os

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")


templates = Jinja2Templates(directory=UI_DIR)


def get_top_categories(limit=5):

    counter = Counter()

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        category = job.get("category")

        if category:
            counter[category] += 1

    result = [category for category, count in counter.most_common(limit)]

    return result


def _attach_company_info(job):

    job.setdefault("company_logo", "default.jpg")

    company_id = job.get("company_id")

    if company_id:

        company_doc = db.collection("company").document(company_id).get()

        company = company_doc.to_dict()
        job["company_name"] = company.get("companyName", "Unknown")
        job["company_logo"] = company.get("logo", "default.jpg")

        # ===== LOCATION =====
        job["location"] = job.get("location", "Unknown")

    # ===== SALARY =====

    salary_display = job.get("salary_display")

    if salary_display:

        job["salary_text"] = salary_display

    else:

        min_salary = job.get("minSalary")
        max_salary = job.get("maxSalary")

        if min_salary and max_salary:

            job["salary_text"] = f"RM {min_salary} - RM {max_salary}"

        elif min_salary:

            job["salary_text"] = f"RM {min_salary}"

        elif max_salary:

            job["salary_text"] = f"RM {max_salary}"

        else:

            job["salary_text"] = "Negotiable"

    return job


@router.get("/")
def home(request: Request):

    # ===========================
    # Get Current Logged-in User
    # ===========================

    user = None

    if request.session.get("user_type") == "job_seeker":

        uid = request.session.get("applicant_id")

        if uid:

            doc = db.collection("job_seeker").document(uid).get()

            if doc.exists:

                user = doc.to_dict()

    # ===========================
    # Featured Jobs
    # ===========================

    job_docs = (
        db.collection("job_list")
        .where(filter=FieldFilter("status", "==", "Active"))
        .order_by("created_at", direction="DESCENDING")
        .limit(4)
        .stream()
    )

    jobs = []

    for doc in job_docs:

        job = doc.to_dict()

        job["id"] = doc.id

        job = _attach_company_info(job)

        jobs.append(job)

    # ===========================
    # Companies
    # ===========================

    companies = []

    docs = db.collection("company").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        companies.append(doc.to_dict())

    # ===========================
    # Statistics
    # ===========================

    categories = get_top_categories()

    total_jobs = len(
        list(db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream())
    )

    # ===========================
    # Return Template
    # ===========================

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "user": user,
            "featured_jobs": jobs,
            "top_companies": companies[:5],
            "categories": categories,
            "total_jobs": total_jobs,
            "total_companies": len(companies),
        },
    )
