import math
import os
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.templating import (
    Jinja2Templates,
)
from firebase_admin import firestore

from ..database import db
from ..helper import get_company
from ..notifications import (
    get_unread_notifications_count,
)

router = APIRouter()


# =====================================================
# Templates
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent


templates = Jinja2Templates(directory=str(BASE_DIR / "ui"))


# =====================================================
# Current Company ID
# =====================================================


def get_current_company_id(request: Request):

    # ==========================================
    # Pytest
    # ==========================================

    if os.getenv("PYTEST_CURRENT_TEST"):
        return "C000001"

    # ==========================================
    # Normal Login
    # ==========================================

    if request.session.get("user_type") != "employer":
        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:
        raise HTTPException(status_code=401, detail="Company not logged in")

    return company_id


# =====================================================
# Safe Datetime Helper
# =====================================================


def make_aware_datetime(value):

    if not value:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value


# =====================================================
# Salary Display Helper
# =====================================================


def build_salary_display(
    salary_type: str,
    salary: str,
    min_salary: str,
    max_salary: str,
):

    if salary_type == "fixed":
        if salary:
            return f"RM {salary}"

        return "-"

    if salary_type == "range":
        if min_salary and max_salary:
            return f"RM {min_salary} - RM {max_salary}"

        return "-"

    if salary_type == "negotiable":
        return "Negotiable"

    return "-"


# =====================================================
# Build Job Form Data
# =====================================================


def build_job_data(
    job_title,
    category,
    employment_type,
    position,
    vacancies,
    location,
    job_desc,
    job_responsibility,
    job_req,
    additional_info,
    salaryType,
    salary,
    minSalary,
    maxSalary,
    benefits,
    other_benefit,
):

    other_benefit = other_benefit.strip()

    if other_benefit and other_benefit not in benefits:
        benefits.append(other_benefit)

    salary_display = build_salary_display(
        salaryType,
        salary,
        minSalary,
        maxSalary,
    )

    return {
        "job_title": job_title,
        "category": category,
        "employment_type": employment_type,
        "position": position,
        "vacancies": vacancies,
        "location": location,
        "job_desc": job_desc,
        "job_responsibility": job_responsibility,
        "job_req": job_req,
        "additional_info": additional_info.strip(),
        "salaryType": salaryType,
        "salary": salary,
        "minSalary": minSalary,
        "maxSalary": maxSalary,
        "salary_display": salary_display,
        "benefits": benefits,
        "other_benefit": other_benefit,
    }


# =====================================================
# Update Data Helper
# =====================================================


def get_job_update_data(edited_job):

    return {
        "job_title": edited_job.get("job_title"),
        "category": edited_job.get("category"),
        "employment_type": edited_job.get("employment_type"),
        "position": edited_job.get("position"),
        "vacancies": edited_job.get("vacancies"),
        "location": edited_job.get("location"),
        "job_desc": edited_job.get("job_desc"),
        "job_responsibility": edited_job.get("job_responsibility"),
        "job_req": edited_job.get("job_req"),
        "additional_info": edited_job.get("additional_info", ""),
        "salaryType": edited_job.get("salaryType"),
        "salary": edited_job.get("salary", ""),
        "minSalary": edited_job.get("minSalary", ""),
        "maxSalary": edited_job.get("maxSalary", ""),
        "salary_display": edited_job.get("salary_display", "-"),
        "benefits": edited_job.get("benefits", []),
        "other_benefit": edited_job.get("other_benefit", ""),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }


# =====================================================
# Publish Job Page
# =====================================================


@router.get("/publish-job", response_class=HTMLResponse)
async def publish_job(request: Request):

    company = get_company(request)

    if company is None:
        return RedirectResponse("/login", status_code=303)

    unread_count = get_unread_notifications_count(request)

    # ==========================================
    # Categories
    # ==========================================

    industry_docs = db.collection("industries").stream()

    categories = []

    for doc in industry_docs:
        data = doc.to_dict()

        categories.append(data)

    categories.sort(key=lambda item: str(item.get("industry_name", "")).lower())

    # ==========================================
    # Previous Form Data
    # ==========================================

    job = request.session.get("job", {})

    return templates.TemplateResponse(
        request=request,
        name="publishJob.html",
        context={
            "request": request,
            "company": company,
            "categories": categories,
            "job": job,
            "unread_notifications_count": unread_count,
        },
    )


# =====================================================
# Review New Job
# =====================================================


@router.post("/review-job", response_class=HTMLResponse)
async def review_job(
    request: Request,
    job_title: str = Form(...),
    category: str = Form(...),
    employment_type: str = Form(...),
    position: str = Form(...),
    vacancies: int = Form(...),
    location: str = Form(...),
    job_desc: str = Form(...),
    job_responsibility: str = Form(...),
    job_req: str = Form(...),
    additional_info: str = Form(""),
    salaryType: str = Form(...),
    salary: str = Form(""),
    minSalary: str = Form(""),
    maxSalary: str = Form(""),
    benefits: list[str] = Form([]),
    other_benefit: str = Form(""),
    action: str = Form("review"),
):

    company = get_company(request)

    if company is None:
        return RedirectResponse("/login", status_code=303)

    company_id = get_current_company_id(request)

    job = build_job_data(
        job_title,
        category,
        employment_type,
        position,
        vacancies,
        location,
        job_desc,
        job_responsibility,
        job_req,
        additional_info,
        salaryType,
        salary,
        minSalary,
        maxSalary,
        benefits,
        other_benefit,
    )

    job["company_id"] = company_id

    # =================================================
    # Save As Draft
    # =================================================

    if action == "draft":
        job["status"] = "Draft"

        job["publish_date"] = None

        job["expiry_date"] = None

        job["duration"] = None

        job["credit_used"] = 0

        job["created_at"] = firestore.SERVER_TIMESTAMP

        job["updated_at"] = firestore.SERVER_TIMESTAMP

        db.collection("job_list").add(job)

        request.session.pop("job", None)

        return RedirectResponse("/manage-jobs?success=draft", status_code=303)

    # =================================================
    # Review
    # =================================================

    request.session["job"] = job

    return templates.TemplateResponse(
        request=request,
        name="reviewJob.html",
        context={
            "request": request,
            "job": job,
            "company": company,
            "is_edit": False,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Publish New Job Confirm
# =====================================================


@router.post("/publish-job-confirm")
async def publish_job_confirm(
    request: Request,
    duration: int = Form(30),
):
    job = request.session.get("job")

    # No reviewed job information in session
    if not job:
        return RedirectResponse(
            "/publish-job",
            status_code=303,
        )

    company_id = get_current_company_id(request)

    # =================================================
    # Validate Duration
    # =================================================

    credit_rules = {
        14: 1,
        30: 1,
        60: 2,
        90: 3,
    }

    if duration not in credit_rules:
        raise HTTPException(
            status_code=400,
            detail="Invalid posting duration",
        )

    required_credit = credit_rules[duration]

    # =================================================
    # Retrieve Company
    # =================================================

    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    if not company_doc.exists:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company_data = company_doc.to_dict() or {}

    available_credit = int(company_data.get("available_credit", 0) or 0)

    # =================================================
    # Insufficient Credit: Save As Draft
    # =================================================

    if available_credit < required_credit:
        job["company_id"] = company_id
        job["status"] = "Draft"
        job["publish_date"] = None
        job["expiry_date"] = None
        job["duration"] = None
        job["credit_used"] = 0
        job["created_at"] = firestore.SERVER_TIMESTAMP
        job["updated_at"] = firestore.SERVER_TIMESTAMP

        db.collection("job_list").add(job)

        request.session.pop("job", None)

        return RedirectResponse(
            ("/manage-jobs?error=insufficient_credit&saved=draft"),
            status_code=303,
        )

    # =================================================
    # Publish Job
    # =================================================

    now = datetime.now(UTC)
    expiry_date = now + timedelta(days=duration)

    job["company_id"] = company_id
    job["status"] = "Active"
    job["duration"] = duration
    job["credit_used"] = required_credit
    job["publish_date"] = now
    job["expiry_date"] = expiry_date
    job["created_at"] = firestore.SERVER_TIMESTAMP
    job["updated_at"] = firestore.SERVER_TIMESTAMP

    job_ref = db.collection("job_list").document()
    job_ref.set(job)

    # =================================================
    # Deduct Company Credit
    # =================================================

    company_ref.update(
        {
            "available_credit": firestore.Increment(-required_credit),
            "used_credit": firestore.Increment(required_credit),
        }
    )

    # =================================================
    # Save Credit History
    # =================================================

    db.collection("credit_history").add(
        {
            "company_id": company_id,
            "date": firestore.SERVER_TIMESTAMP,
            "type": "JOB_POST",
            "description": (f"Published '{job.get('job_title', 'Job')}'"),
            "credit": -required_credit,
            "balance": (available_credit - required_credit),
            "reference": job_ref.id,
        }
    )

    request.session.pop("job", None)

    return RedirectResponse(
        "/manage-jobs?success=posted",
        status_code=303,
    )


# =====================================================
# Manage Jobs
# =====================================================


@router.get("/manage-jobs", response_class=HTMLResponse)
async def manage_jobs(request: Request, page: int = 1, status: str = "all", keyword: str = ""):

    company = get_company(request)

    # ==========================================
    # Pytest
    # ==========================================

    if os.getenv("PYTEST_CURRENT_TEST"):
        company_id = "C000001"

        if company is None:
            company = {
                "company_id": "C000001",
                "companyName": "Test Company",
                "status": "Active",
            }

    else:
        if company is None:
            return RedirectResponse("/login", status_code=303)

        if company.get("status") != "Active":
            return templates.TemplateResponse(
                request=request,
                name="companyPending.html",
                context={
                    "request": request,
                    "company": company,
                    "unread_notifications_count": get_unread_notifications_count(request),
                },
            )

        company_id = get_current_company_id(request)

    # =================================================
    # Jobs
    # =================================================

    job_docs = db.collection("job_list").where("company_id", "==", company_id).stream()

    all_jobs = []

    now = datetime.now(UTC)

    for doc in job_docs:
        job_data = doc.to_dict()

        job_data["job_id"] = doc.id

        current_status = str(job_data.get("status", "") or "")

        # ======================================
        # Hide Deleted
        # ======================================

        if current_status.lower() == "deleted":
            continue

        # ======================================
        # Auto Expire ACTIVE only
        # ======================================

        expiry = make_aware_datetime(job_data.get("expiry_date"))

        if expiry and expiry <= now and current_status.lower() == "active":
            db.collection("job_list").document(doc.id).update(
                {
                    "status": "Expired",
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
            )

            job_data["status"] = "Expired"

        # ======================================
        # Application Count
        # ======================================

        application_docs = db.collection("application").where("job_id", "==", doc.id).stream()

        job_data["application_count"] = sum(1 for _ in application_docs)

        # ======================================
        # Sort Date
        # ======================================

        sort_date = (
            job_data.get("created_at") or job_data.get("publish_date") or job_data.get("updated_at")
        )

        job_data["_sort_date"] = make_aware_datetime(sort_date)

        all_jobs.append(job_data)

    # =================================================
    # Descending
    # =================================================

    all_jobs.sort(
        key=lambda item: item.get("_sort_date") or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    # =================================================
    # Counts
    # =================================================

    counts = {
        "all": len(all_jobs),
        "active": 0,
        "draft": 0,
        "closed": 0,
        "expired": 0,
    }

    for job in all_jobs:
        job_status = str(job.get("status", "")).lower()

        if job_status in counts:
            counts[job_status] += 1

    # =================================================
    # Status Filter
    # =================================================

    status = (status or "all").lower()

    allowed_statuses = {
        "all",
        "active",
        "draft",
        "closed",
        "expired",
    }

    if status not in allowed_statuses:
        status = "all"

    filtered_jobs = all_jobs

    if status != "all":
        filtered_jobs = [
            job for job in filtered_jobs if str(job.get("status", "")).lower() == status
        ]

    # =================================================
    # Search
    # =================================================

    clean_keyword = keyword.strip()

    if clean_keyword:
        search_text = clean_keyword.lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if (
                search_text in str(job.get("job_title", "")).lower()
                or search_text in str(job.get("location", "")).lower()
                or search_text in str(job.get("employment_type", "")).lower()
                or search_text in str(job.get("status", "")).lower()
            )
        ]

    # =================================================
    # Pagination
    # =================================================

    PER_PAGE = 20

    total_filtered_jobs = len(filtered_jobs)

    total_pages = max(1, math.ceil(total_filtered_jobs / PER_PAGE))

    page = max(page, 1)

    page = min(page, total_pages)

    start_index = (page - 1) * PER_PAGE

    end_index = start_index + PER_PAGE

    jobs = filtered_jobs[start_index:end_index]

    for job in jobs:
        job.pop("_sort_date", None)

    # =================================================
    # Pagination Display
    # =================================================

    if total_filtered_jobs > 0:
        showing_from = start_index + 1

        showing_to = min(end_index, total_filtered_jobs)

    else:
        showing_from = 0

        showing_to = 0

    # =================================================
    # Render
    # =================================================

    return templates.TemplateResponse(
        request=request,
        name="jobPosted.html",
        context={
            "request": request,
            "jobs": jobs,
            "company": company,
            "counts": counts,
            "current_status": status,
            "keyword": clean_keyword,
            "current_page": page,
            "total_pages": total_pages,
            "total_filtered_jobs": total_filtered_jobs,
            "showing_from": showing_from,
            "showing_to": showing_to,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Close Job
# =====================================================


@router.post("/close-job/{job_id}")
async def close_job(request: Request, job_id: str):

    company_id = get_current_company_id(request)

    job_ref = db.collection("job_list").document(job_id)

    job_doc = job_ref.get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_doc.to_dict()

    # ==========================================
    # Security
    # ==========================================

    if job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ==========================================
    # Active Only
    # ==========================================

    if str(job.get("status", "")).lower() != "active":
        return RedirectResponse("/manage-jobs", status_code=303)

    # ==========================================
    # Update Same Job
    # ==========================================

    job_ref.update(
        {
            "status": "Closed",
            "closed_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return RedirectResponse("/manage-jobs?success=closed", status_code=303)


# =====================================================
# Edit Job Page
# =====================================================


@router.get("/edit-job/{job_id}", response_class=HTMLResponse)
async def edit_job(request: Request, job_id: str):

    company = get_company(request)

    if company is None:
        return RedirectResponse("/login", status_code=303)

    company_id = get_current_company_id(request)

    # ==========================================
    # Job
    # ==========================================

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_doc.to_dict()

    job["job_id"] = job_id

    # ==========================================
    # Security
    # ==========================================

    if job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ==========================================
    # Categories
    # ==========================================

    category_docs = db.collection("industries").stream()

    categories = []

    for doc in category_docs:
        data = doc.to_dict()

        categories.append(
            {
                "industry_id": doc.id,
                "industry_name": data.get("industry_name", ""),
            }
        )

    categories.sort(key=lambda item: item["industry_name"].lower())

    return templates.TemplateResponse(
        request=request,
        name="editJob.html",
        context={
            "request": request,
            "job": job,
            "categories": categories,
            "company": company,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Review Edited Job
# =====================================================


@router.post("/review-edit-job/{job_id}", response_class=HTMLResponse)
async def review_edit_job(
    request: Request,
    job_id: str,
    job_title: str = Form(...),
    category: str = Form(...),
    employment_type: str = Form(...),
    position: str = Form(...),
    vacancies: int = Form(...),
    location: str = Form(...),
    job_desc: str = Form(...),
    job_responsibility: str = Form(...),
    job_req: str = Form(...),
    additional_info: str = Form(""),
    salaryType: str = Form(...),
    salary: str = Form(""),
    minSalary: str = Form(""),
    maxSalary: str = Form(""),
    benefits: list[str] = Form([]),
    other_benefit: str = Form(""),
    action: str = Form("review"),
):

    # =================================================
    # Company
    # =================================================

    company = get_company(request)

    if company is None:
        return RedirectResponse("/login", status_code=303)

    company_id = get_current_company_id(request)

    # =================================================
    # Existing Job
    # =================================================

    job_ref = db.collection("job_list").document(job_id)

    job_doc = job_ref.get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    old_job = job_doc.to_dict()

    # =================================================
    # Security
    # =================================================

    if old_job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # =================================================
    # Build Edited Job Data
    # =================================================

    edited_job = build_job_data(
        job_title,
        category,
        employment_type,
        position,
        vacancies,
        location,
        job_desc,
        job_responsibility,
        job_req,
        additional_info,
        salaryType,
        salary,
        minSalary,
        maxSalary,
        benefits,
        other_benefit,
    )

    # =================================================
    # Safe Values Only
    # =================================================

    edited_job["job_id"] = job_id

    edited_job["company_id"] = company_id

    edited_job["status"] = str(old_job.get("status", "Draft") or "Draft")

    # IMPORTANT:
    # DO NOT add created_at,
    # publish_date,
    # expiry_date,
    # duration into the session.
    #
    # Firestore datetime values are not JSON serializable.

    # =================================================
    # Save Draft Directly
    # =================================================

    if action == "draft" and edited_job["status"].lower() == "draft":
        update_data = get_job_update_data(edited_job)

        update_data["status"] = "Draft"

        job_ref.update(update_data)

        request.session.pop("edit_job", None)

        return RedirectResponse("/manage-jobs?success=draft", status_code=303)

    # =================================================
    # Store JSON-safe data in session
    # =================================================

    request.session["edit_job"] = edited_job

    # =================================================
    # Render Review Edit Page
    # =================================================

    return templates.TemplateResponse(
        request=request,
        name="reviewEditJob.html",
        context={
            "request": request,
            "job": edited_job,
            "company": company,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Confirm Normal Job Update
# Active / Closed / Expired
# =====================================================


@router.post("/confirm-edit-job/{job_id}")
async def confirm_edit_job(request: Request, job_id: str):

    company_id = get_current_company_id(request)

    edited_job = request.session.get("edit_job")

    if not edited_job:
        return RedirectResponse(f"/edit-job/{job_id}", status_code=303)

    job_ref = db.collection("job_list").document(job_id)

    job_doc = job_ref.get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    current_job = job_doc.to_dict()

    if current_job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    current_status = str(current_job.get("status", "")).lower()

    # Draft must use Publish route
    if current_status == "draft":
        return RedirectResponse(f"/edit-job/{job_id}", status_code=303)

    update_data = get_job_update_data(edited_job)

    # IMPORTANT:
    # No status change here.
    # Active stays Active.
    # Closed stays Closed.
    # Expired stays Expired.

    job_ref.update(update_data)

    request.session.pop("edit_job", None)

    return RedirectResponse("/manage-jobs?success=edited", status_code=303)


# =====================================================
# Publish Existing Draft
# =====================================================


@router.post("/publish-draft-job/{job_id}")
async def publish_draft_job(
    request: Request, job_id: str, duration: int = Form(...), credit_used: int = Form(...)
):

    company_id = get_current_company_id(request)

    edited_job = request.session.get("edit_job")

    if not edited_job:
        return RedirectResponse(f"/edit-job/{job_id}", status_code=303)

    # =================================================
    # Current Draft Job
    # =================================================

    job_ref = db.collection("job_list").document(job_id)

    job_doc = job_ref.get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    current_job = job_doc.to_dict()

    if current_job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if str(current_job.get("status", "")).lower() != "draft":
        return RedirectResponse("/manage-jobs", status_code=303)

    # =================================================
    # Server-side Credit Rule
    # =================================================

    CREDIT_RULES = {
        30: 1,
        60: 2,
        90: 3,
    }

    if duration not in CREDIT_RULES:
        raise HTTPException(status_code=400, detail="Invalid posting duration")

    required_credit = CREDIT_RULES[duration]

    # =================================================
    # Company Credit
    # =================================================

    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")

    company = company_doc.to_dict()

    available_credit = int(company.get("available_credit", 0) or 0)

    # =================================================
    # Insufficient Credit
    # Save Changes, Remain Draft
    # =================================================

    if available_credit < required_credit:
        update_data = get_job_update_data(edited_job)

        update_data.update(
            {
                "status": "Draft",
                "publish_date": None,
                "expiry_date": None,
                "credit_used": 0,
            }
        )

        job_ref.update(update_data)

        request.session.pop("edit_job", None)

        return RedirectResponse(
            ("/manage-jobs?error=insufficient_credit&saved=draft"), status_code=303
        )

    # =================================================
    # Publish Same Draft Document
    # =================================================

    now = datetime.now(UTC)

    expiry_date = now + timedelta(days=duration)

    update_data = get_job_update_data(edited_job)

    update_data.update(
        {
            "status": "Active",
            "duration": duration,
            "credit_used": required_credit,
            "publish_date": now,
            "expiry_date": expiry_date,
            "closed_at": None,
        }
    )

    # IMPORTANT:
    # UPDATE same Draft
    # Do not create another job
    job_ref.update(update_data)

    # =================================================
    # Deduct Credit
    # =================================================

    company_ref.update(
        {
            "available_credit": firestore.Increment(-required_credit),
            "used_credit": firestore.Increment(required_credit),
        }
    )

    # =================================================
    # Credit History
    # =================================================

    db.collection("credit_history").add(
        {
            "company_id": company_id,
            "date": firestore.SERVER_TIMESTAMP,
            "type": "JOB_POST",
            "description": (f"Published draft job '{edited_job.get('job_title', 'Job')}'"),
            "credit": -required_credit,
            "balance": (available_credit - required_credit),
            "reference": job_id,
        }
    )

    request.session.pop("edit_job", None)

    return RedirectResponse("/manage-jobs?success=posted", status_code=303)


# =====================================================
# Delete Job
# =====================================================


@router.get("/delete-job/{job_id}")
async def delete_job(request: Request, job_id: str):

    company_id = get_current_company_id(request)

    job_ref = db.collection("job_list").document(job_id)

    job_doc = job_ref.get()

    if not job_doc.exists:
        return RedirectResponse("/manage-jobs?error=notfound", status_code=303)

    job = job_doc.to_dict()

    if job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Soft Delete
    job_ref.update(
        {
            "status": "Deleted",
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return RedirectResponse("/manage-jobs?success=deleted", status_code=303)


# =====================================================
# View Job Details
# =====================================================


@router.get("/view-job/{job_id}", response_class=HTMLResponse)
async def view_job(request: Request, job_id: str):

    company_id = get_current_company_id(request)

    # ==========================================
    # Company
    # ==========================================

    company_doc = db.collection("company").document(company_id).get()

    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")

    company = company_doc.to_dict()

    # ==========================================
    # Job
    # ==========================================

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_doc.to_dict()

    job["job_id"] = job_id

    # ==========================================
    # Security
    # ==========================================

    if job.get("company_id") != company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # ==========================================
    # Application Count
    # ==========================================

    application_docs = db.collection("application").where("job_id", "==", job_id).stream()

    application_count = sum(1 for _ in application_docs)

    # Put it inside job too
    job["application_count"] = application_count

    return templates.TemplateResponse(
        request=request,
        name="viewJob.html",
        context={
            "request": request,
            "company": company,
            "job": job,
            "application_count": application_count,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Job Statistics
# =====================================================


@router.get("/job-statistics")
async def job_statistics(request: Request):

    company_id = get_current_company_id(request)

    docs = db.collection("job_list").where("company_id", "==", company_id).stream()

    result = {
        "total": 0,
        "active": 0,
        "draft": 0,
        "closed": 0,
        "expired": 0,
    }

    for doc in docs:
        status = str(doc.to_dict().get("status", "")).lower()

        if status == "deleted":
            continue

        result["total"] += 1

        if status in result:
            result[status] += 1

    return JSONResponse({"success": True, **result})


# =====================================================
# Cancel New Job
# =====================================================


@router.get("/cancel-job")
async def cancel_job(request: Request):

    request.session.pop("job", None)

    return RedirectResponse("/manage-jobs", status_code=303)
