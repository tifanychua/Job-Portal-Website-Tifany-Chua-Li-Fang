from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List

from .database import db
from collections import Counter
from collections import defaultdict
import math
import os

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")


templates = Jinja2Templates(directory=UI_DIR)


# ==============================
# Popular Categories
# ==============================


def get_top_categories(limit=5):

    counter = Counter()

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        category = job.get("category")

        if category:

            counter[category] += 1

    return [category for category, count in counter.most_common(limit)]


# ==============================
# Category List
# ==============================


def get_categories():

    categories = set()

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        category = job.get("category")

        if category:

            categories.add(category)

    return sorted(categories)


# ==============================
# Find Company
# ==============================


def _find_company(company_ref):

    if not company_ref:

        return None

    # Search document ID

    company_doc = db.collection("company").document(company_ref).get()

    if company_doc.exists:

        return company_doc.to_dict()

    # Search company_id field

    matches = (
        db.collection("company")
        .where(filter=FieldFilter("company_id", "==", company_ref))
        .limit(1)
        .stream()
    )

    for c in matches:

        return c.to_dict()

    return None


# ==============================
# Attach Company Information
# ==============================


def _attach_company_info(job):

    job.setdefault("company_name", "Unknown")

    # only filename
    job.setdefault("company_logo", "default.jpg")

    company = _find_company(job.get("company_id"))

    if company:

        job["company_name"] = company.get("companyName", "Unknown")

        gallery_docs = (
            db.collection("gallery")
            .where(filter=FieldFilter("company_id", "==", job.get("company_id")))
            .limit(1)
            .stream()
        )

        for img in gallery_docs:

            gallery = img.to_dict()

            if gallery.get("image"):

                job["company_logo"] = gallery.get("image")

            break

        if not job.get("location"):

            job["location"] = company.get("location", "Unknown")

    return job


# ==============================
# Apply User Filters
# ==============================


def apply_filters(jobs, locations=None, positions=None, benefits=None):

    if locations is None:

        locations = []

    if positions is None:

        positions = []

    if benefits is None:

        benefits = []

    filtered = jobs

    # Location checkbox

    if locations:

        filtered = [job for job in filtered if job.get("location") in locations]

    # Position checkbox

    if positions:

        filtered = [job for job in filtered if job.get("position") in positions]

    # Benefit checkbox
    # benefits stored as array

    if benefits:

        filtered = [job for job in filtered if any(b in job.get("benefits", []) for b in benefits)]

    return filtered


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

    # ==================================
    # Get all active jobs
    # ==================================

    jobs = []

    docs = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active")).stream()

    for doc in docs:

        job = doc.to_dict()

        job["id"] = doc.id

        job = _attach_company_info(job)

        jobs.append(job)

    # ==================================
    # Search Filter
    # (ONLY this changes sidebar)
    # ==================================

    if q:

        keyword = q.lower()

        jobs = [
            job
            for job in jobs
            if keyword in job.get("job_title", "").lower()
            or keyword in job.get("company_name", "").lower()
        ]

    # Category search

    if category:

        jobs = [job for job in jobs if job.get("category", "").lower() == category.lower()]

    # ==================================
    # Save search result
    # Sidebar depends on this
    # ==================================

    search_jobs = jobs.copy()

    # ==================================
    # Sidebar Count
    # ==================================

    location_count: defaultdict[str, int] = defaultdict(int)
    position_count: defaultdict[str, int] = defaultdict(int)
    benefit_count: defaultdict[str, int] = defaultdict(int)

    for job in search_jobs:

        location_count[job.get("location", "Unknown")] += 1

        position_count[job.get("position", "Unknown")] += 1

        for benefit in job.get("benefits", []):

            benefit_count[benefit] += 1

    locations = [{"name": key, "count": value} for key, value in location_count.items()]

    positions = [{"name": key, "count": value} for key, value in position_count.items()]

    benefits_list = [{"name": key, "count": value} for key, value in benefit_count.items()]

    # ==================================
    # Apply checkbox filters
    # (does NOT affect sidebar)
    # ==================================

    jobs = apply_filters(search_jobs, locations=location, positions=position, benefits=benefits)

    # ==================================
    # Pagination
    # ==================================

    per_page = 5

    page = int(page)

    total_jobs = len(jobs)

    total_pages = max(1, math.ceil(total_jobs / per_page))

    # pagination index
    start_index = (page - 1) * per_page

    end_index = start_index + per_page

    # display jobs
    jobs = jobs[start_index:end_index]

    # for showing "Showing x-y of z jobs"
    show_start = start_index + 1

    show_end = min(end_index, total_jobs)

    # ==================================
    # Other data
    # ==================================

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
            "page": page,
            "start": show_start,
            "end": show_end,
            # Search value
            "query": q,
            "categories": categories,
            "category": category,
            "topCategories": topCategories,
            # Sidebar
            "locations": locations,
            "positions": positions,
            "benefits": benefits_list,
            # Checked state
            "selected_locations": location,
            "selected_positions": position,
            "selected_benefits": benefits,
        },
    )
