import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from .database import db
from .job_information import _attach_company_fields, _find_company, _normalize_job
from .notifications import get_unread_notifications_count

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")

templates = Jinja2Templates(directory=UI_DIR)


# =====================================================
# Helpers
# =====================================================


def _get_current_job_seeker_id(request: Request):

    if request.session.get("user_type") != "job_seeker":
        return None

    return request.session.get("applicant_id")


def _saved_doc_id(job_seeker_id, job_id):

    return f"{job_seeker_id}_{job_id}"


# =====================================================
# PAGE — Saved Jobs list
# =====================================================


@router.get("/saved-jobs", name="saved_jobs_page")
def saved_jobs_page(request: Request):

    job_seeker_id = _get_current_job_seeker_id(request)

    if not job_seeker_id:
        return RedirectResponse("/login", status_code=303)

    user_doc = db.collection("job_seeker").document(job_seeker_id).get()

    user = user_doc.to_dict() if user_doc.exists else None

    # =====================================================
    # Load saved job links for this job seeker
    # =====================================================

    saved_docs = (
        db.collection("saved_job")
        .where(filter=FieldFilter("job_seeker_id", "==", job_seeker_id))
        .stream()
    )

    # =====================================================
    # Load applications so we can flag "Applied" saved jobs
    # =====================================================

    applied_job_ids = {
        data.get("job_id")
        for doc in db.collection("application")
        .where(filter=FieldFilter("job_seeker_id", "==", job_seeker_id))
        .stream()
        if (data := doc.to_dict()).get("status") != "Cancelled"
    }

    now = datetime.now(UTC)

    saved_jobs = []

    for doc in saved_docs:
        saved = doc.to_dict()

        job_id = saved.get("job_id")

        if not job_id:
            continue

        job_doc = db.collection("job_list").document(job_id).get()

        if not job_doc.exists:
            # Job was removed/unpublished — skip it from the list
            continue

        job = job_doc.to_dict()

        job = _normalize_job(job, job_id)

        company = _find_company(job.get("company_id"))

        job = _attach_company_fields(job, company)

        saved_at = saved.get("saved_at")

        job["saved_at_display"] = (
            saved_at.strftime("%d %b %Y") if hasattr(saved_at, "strftime") else "—"
        )

        job["saved_at_sort"] = saved_at.isoformat() if hasattr(saved_at, "isoformat") else ""

        is_recent = False

        if hasattr(saved_at, "tzinfo"):
            ts = saved_at if saved_at.tzinfo else saved_at.replace(tzinfo=UTC)

            is_recent = (now - ts).days <= 7

        job["is_recent"] = is_recent

        job["is_applied"] = job_id in applied_job_ids

        saved_jobs.append(job)

    saved_jobs.sort(key=lambda j: j.get("saved_at_sort", ""), reverse=True)

    return templates.TemplateResponse(
        request=request,
        name="savedJob.html",
        context={
            "user": user,
            "active_page": "saved_jobs",
            "saved_jobs": saved_jobs,
            "total_saved": len(saved_jobs),
            "total_recent": sum(1 for j in saved_jobs if j["is_recent"]),
            "total_applied": sum(1 for j in saved_jobs if j["is_applied"]),
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# API — Save a job
# =====================================================


@router.post("/api/saved-jobs/{job_id}", name="save_job")
def save_job(request: Request, job_id: str):

    job_seeker_id = _get_current_job_seeker_id(request)

    if not job_seeker_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Please log in to save jobs."},
        )

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    doc_id = _saved_doc_id(job_seeker_id, job_id)

    db.collection("saved_job").document(doc_id).set(
        {
            "job_seeker_id": job_seeker_id,
            "job_id": job_id,
            "saved_at": datetime.now(UTC),
        }
    )

    return JSONResponse(content={"success": True, "saved": True, "message": "Job saved."})


# =====================================================
# API — Unsave a job
# =====================================================


@router.delete("/api/saved-jobs/{job_id}", name="unsave_job")
def unsave_job(request: Request, job_id: str):

    job_seeker_id = _get_current_job_seeker_id(request)

    if not job_seeker_id:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Please log in."},
        )

    doc_id = _saved_doc_id(job_seeker_id, job_id)

    saved_ref = db.collection("saved_job").document(doc_id)

    if not saved_ref.get().exists:
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "saved": False,
                "message": "This job is not in your saved list.",
            },
        )

    saved_ref.delete()

    return JSONResponse(
        content={"success": True, "saved": False, "message": "Job removed from saved list."}
    )


# =====================================================
# API — Check saved status (for wiring bookmark buttons
# on other pages such as jobs.html / job_information.html)
# =====================================================


@router.get("/api/saved-jobs/{job_id}/status", name="saved_job_status")
def saved_job_status(request: Request, job_id: str):

    job_seeker_id = _get_current_job_seeker_id(request)

    if not job_seeker_id:
        return JSONResponse(content={"saved": False})

    doc_id = _saved_doc_id(job_seeker_id, job_id)

    doc = db.collection("saved_job").document(doc_id).get()

    return JSONResponse(content={"saved": doc.exists})
