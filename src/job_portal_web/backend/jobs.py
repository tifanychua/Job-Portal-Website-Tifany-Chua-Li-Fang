from collections import Counter

from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List
import math
import os

from .database import db

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")

templates = Jinja2Templates(directory=UI_DIR)


# =====================================================
# Cache
# =====================================================


def load_company_cache():

    cache = {}

    docs = db.collection("company").stream()

    for doc in docs:

        company = doc.to_dict()

        # document id
        cache[doc.id] = company

        # company_id field
        company_id = company.get("company_id")

        if company_id:
            cache[company_id] = company

    return cache


def load_gallery_cache():

    cache = {}

    docs = db.collection("gallery").stream()

    for doc in docs:

        gallery = doc.to_dict()

        company_id = gallery.get("company_id")

        image = gallery.get("image")

        if company_id and image:

            cache[company_id] = image

    return cache


# =====================================================
# Read Active Jobs
# =====================================================


def load_jobs():

    jobs = []

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        job["id"] = doc.id

        jobs.append(job)

    return jobs


# =====================================================
# Attach Company
# =====================================================


def attach_company_information(jobs, company_cache, gallery_cache):

    for job in jobs:

        company = company_cache.get(job.get("company_id"))

        job.setdefault("company_name", "Unknown")

        job.setdefault("company_logo", "default.jpg")

        if company:

            job["company_name"] = company.get("companyName", "Unknown")

            job["company_logo"] = company.get("logo", "default.jpg")

            if not job.get("location"):

                job["location"] = company.get("location", "Unknown")

    return jobs


# =====================================================
# Search
# =====================================================


def apply_search(jobs, keyword, category):

    if keyword:

        keyword = keyword.lower()

        jobs = [
            job
            for job in jobs
            if keyword in job.get("job_title", "").lower()
            or keyword in job.get("company_name", "").lower()
            or keyword in job.get("position", "").lower()
            or keyword in job.get("location", "").lower()
            or keyword in job.get("category", "").lower()
        ]

    if category:

        jobs = [job for job in jobs if job.get("category", "").lower() == category.lower()]

    return jobs


# =====================================================
# Sidebar Data
# =====================================================


def build_sidebar(jobs):

    location_counter = Counter()

    position_counter = Counter()

    benefit_counter = Counter()

    category_set = set()

    top_category_counter = Counter()

    for job in jobs:

        location_counter[job.get("location", "Unknown")] += 1

        position_counter[job.get("position", "Unknown")] += 1

        category = job.get("category")

        if category:

            category_set.add(category)

            top_category_counter[category] += 1

        for benefit in job.get("benefits", []):

            benefit_counter[benefit] += 1

    return {
        "locations": [{"name": k, "count": v} for k, v in sorted(location_counter.items())],
        "positions": [{"name": k, "count": v} for k, v in sorted(position_counter.items())],
        "benefits": [{"name": k, "count": v} for k, v in sorted(benefit_counter.items())],
        "categories": sorted(category_set),
        "topCategories": [c for c, _ in top_category_counter.most_common(5)],
    }


@router.get("/jobs", name="browse_jobs")
def browse_jobs(
    request: Request,
    q: str = Query(""),
    category: str = Query(""),
    location: List[str] = Query([]),
    position: List[str] = Query([]),
    benefits: List[str] = Query([]),
    page: int = Query(1),
):

    # =====================================================
    # Load Cache
    # =====================================================

    company_cache = load_company_cache()
    gallery_cache = load_gallery_cache()

    # =====================================================
    # Load All Jobs
    # =====================================================

    all_jobs = load_jobs()

    all_jobs = attach_company_information(all_jobs, company_cache, gallery_cache)

    # =====================================================
    # Category (Search Dropdown)
    # =====================================================

    categories = sorted({job.get("category") for job in all_jobs if job.get("category")})

    # =====================================================
    # Popular Search
    # =====================================================

    category_counter: Counter = Counter()

    for job in all_jobs:

        if job.get("category"):

            category_counter[job["category"]] += 1

    topCategories = [c for c, _ in category_counter.most_common(5)]

    # =====================================================
    # Search
    # =====================================================

    jobs = apply_search(all_jobs, q, category)

    # =====================================================
    # Sidebar (Based on Search Result)
    # =====================================================
    search_jobs = jobs.copy()

    # =====================================================
    # Checkbox Filter
    # =====================================================

    if location:

        jobs = [job for job in jobs if job.get("location") in location]

    if position:

        jobs = [job for job in jobs if job.get("position") in position]

    if benefits:

        jobs = [job for job in jobs if any(b in job.get("benefits", []) for b in benefits)]
    sidebar = build_sidebar(search_jobs)
    # =====================================================
    # Sort
    # =====================================================

    jobs.sort(key=lambda x: x.get("postedDate", ""), reverse=True)

    # =====================================================
    # Pagination
    # =====================================================

    per_page = 5

    total_jobs = len(jobs)

    total_pages = max(1, math.ceil(total_jobs / per_page))

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    start_index = (page - 1) * per_page

    end_index = start_index + per_page

    display_jobs = jobs[start_index:end_index]

    if total_jobs == 0:

        show_start = 0
        show_end = 0

    else:

        show_start = start_index + 1

        show_end = min(end_index, total_jobs)

    # =====================================================
    # Logged In User
    # =====================================================

    user = None

    if request.session.get("user_type") == "job_seeker":

        uid = request.session.get("applicant_id")

        if uid:

            doc = db.collection("job_seeker").document(uid).get()

            if doc.exists:

                user = doc.to_dict()

    # =====================================================
    # Return
    # =====================================================

    return templates.TemplateResponse(
        request=request,
        name="jobs.html",
        context={
            "request": request,
            "user": user,
            "jobs": display_jobs,
            "total_jobs": total_jobs,
            "total_pages": total_pages,
            "page": page,
            "start": show_start,
            "end": show_end,
            "query": q,
            "category": category,
            # Search
            "categories": categories,
            "topCategories": topCategories,
            # Filters
            "locations": sidebar["locations"],
            "positions": sidebar["positions"],
            "benefits": sidebar["benefits"],
            "selected_locations": location,
            "selected_positions": position,
            "selected_benefits": benefits,
        },
    )
