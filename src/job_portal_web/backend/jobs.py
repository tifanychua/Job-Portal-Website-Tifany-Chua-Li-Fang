from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from database import db
from collections import Counter

import math
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


def get_categories():

    categories = set()

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:
        job = doc.to_dict()

        category = job.get("category")

        if category:
            categories.add(category)

    return sorted(categories)


def _find_company(company_ref):
    """
    Look up a company by document ID first,
    then by name as fallback.
    """

    if not company_ref:
        return None

    # Search by document ID

    company_doc = db.collection("company").document(company_ref).get()

    if company_doc.exists:
        return company_doc.to_dict()

    # Search by company name

    matches = (
        db.collection("company")
        .where(filter=FieldFilter("name", "==", company_ref))
        .limit(1)
        .stream()
    )

    for c in matches:
        return c.to_dict()

    return None


def _attach_company_info(job):

    job.setdefault("company_logo", "image/default.jpg")

    job.setdefault("companyName", "Unknown")

    job.setdefault("location", "Unknown")

    company = _find_company(job.get("company_id"))

    if company:

        job["company_logo"] = company.get("logo", "image/default.png")

        job["company_name"] = company.get("name", "Unknown")

        job["location"] = company.get("location", "Unknown")

    return job


@router.get("/jobs", name="browse_jobs")
def browse_jobs(
    request: Request, q: str = Query(""), location: str = Query(""), page: int = Query(1)
):

    jobs = []

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        job["id"] = doc.id

        job = _attach_company_info(job)

        jobs.append(job)

    # ---- Search filter ----

    if q:

        search = q.lower()

        jobs = [
            j
            for j in jobs
            if search in j.get("job_title", "").lower()
            or search in j.get("companyName", "").lower()
        ]

    # ---- Location filter ----

    if location:

        loc = location.lower()

        jobs = [j for j in jobs if loc in j.get("location", "").lower()]

    # ---- Sidebar counts ----

    location_count = {}

    job_type_count = {}

    experience_count = {}

    for job in jobs:

        loc = job.get("location", "Unknown")

        location_count[loc] = location_count.get(loc, 0) + 1

        job_type = job.get("jobType", "Unknown")

        job_type_count[job_type] = job_type_count.get(job_type, 0) + 1

        experience = job.get("experience", "Unknown")

        experience_count[experience] = experience_count.get(experience, 0) + 1

    locations = [{"name": k, "count": v} for k, v in location_count.items()]

    job_types = [{"name": k, "count": v} for k, v in job_type_count.items()]

    experience_levels = [{"name": k, "count": v} for k, v in experience_count.items()]

    # ---- Pagination ----

    per_page = 5

    total_jobs = len(jobs)

    total_pages = math.ceil(total_jobs / per_page)

    start = (page - 1) * per_page

    end = start + per_page

    jobs = jobs[start:end]

    topCategories = get_top_categories()

    categories = get_categories()

    return templates.TemplateResponse(
        request=request,
        name="jobs.html",
        context={
            "request": request,
            "jobs": jobs,
            "total_jobs": total_jobs,
            "total_pages": total_pages,
            "topCategories": topCategories[:5],
            "categories": categories,
            "page": page,
            "query": q,
            "location_query": location,
            "locations": locations,
            "job_types": job_types,
            "experience_levels": experience_levels,
        },
    )
