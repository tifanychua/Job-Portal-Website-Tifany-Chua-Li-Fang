from pathlib import Path
from typing import List
import uuid

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.job_portal_web.backend.helper import get_company
from firebase_admin import firestore
from src.job_portal_web.backend.database import db

router = APIRouter()

# Project root (job_portal_web)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "ui")
)


# ==================================================
# Manage Jobs
# ==================================================

@router.post("/publish-job-confirm")
async def publish_job_confirm(
    request: Request
):

    job = request.session.get("job")


    # No job information found

    if not job:

        return RedirectResponse(
            url="/publish-job",
            status_code=303
        )


    company_id = "C000001"


    # Generate Firestore document ID

    doc_ref = (
        db.collection("job_list")
        .document()
    )


    # Add job information

    job["company_id"] = company_id

    job["status"] = "Active"

    job["created_at"] = (
        firestore.SERVER_TIMESTAMP
    )

    job["updated_at"] = (
        firestore.SERVER_TIMESTAMP
    )


    # Save job to Firestore

    doc_ref.set(job)


    # Clear temporary session

    request.session.pop(
        "job",
        None
    )


    # Redirect with successful status

    return RedirectResponse(
        url="/manage-jobs?success=posted",
        status_code=303
    )

@router.get("/manage-jobs", response_class=HTMLResponse)
async def manage_jobs(request: Request):

    company_id = "C000001"

    company = get_company()

    job_docs = (
        db.collection("job_list")
        .where("company_id", "==", company_id)
        .stream()
    )

    jobs = []

    for doc in job_docs:

        job_data = doc.to_dict()

        # Get Firestore document ID for HTML usage
        job_data["job_id"] = doc.id

        # Do not display deleted jobs
        if job_data.get("status", "").lower() != "deleted":
            jobs.append(job_data)

    return templates.TemplateResponse(
        request=request,
        name="jobPosted.html",
        context={
            "request": request,
            "jobs": jobs,
            "company": company
        }
    )


# ==================================================
# Publish Job Page
# ==================================================

@router.get("/publish-job", response_class=HTMLResponse)
async def publish_job(request: Request):

    job = request.session.get("job", {})

    company = get_company()

    # Get job categories from Firebase
    category_docs = db.collection("job_category").stream()

    categories = []

    for doc in category_docs:
        category_data = doc.to_dict()
        categories.append(category_data)

    return templates.TemplateResponse(
        request=request,
        name="publishJob.html",
        context={
            "request": request,
            "job": job,
            "categories": categories,
            "company": company
        }
    )


# ==================================================
# Save Form -> Session -> Preview
# ==================================================

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

    benefits: List[str] = Form([]),
    other_benefit: str = Form(""),

    action: str = Form(...)
):

    if other_benefit.strip():
        benefits.append(other_benefit.strip())

    if salaryType == "fixed":
        salary_display = f"RM {salary}"
    elif salaryType == "range":
        salary_display = f"RM {minSalary} - RM {maxSalary}"
    else:
        salary_display = "Negotiable"

    request.session["job"] = {
        "job_title": job_title,
        "category": category,
        "employment_type": employment_type,
        "position": position,
        "vacancies": vacancies,
        "location": location,

        "job_desc": job_desc,
        "job_responsibility": job_responsibility,
        "job_req": job_req,
        "additional_info": additional_info,

        "salaryType": salaryType,
        "salary": salary,
        "minSalary": minSalary,
        "maxSalary": maxSalary,
        "salary_display": salary_display,

        "benefits": benefits,
        "other_benefit": other_benefit.strip()
    }

    if action == "draft":

        job = request.session["job"]
        company_id = "C000001"

        doc_ref = db.collection("job_list").document()

        job["company_id"] = company_id
        job["status"] = "Draft"
        job["created_at"] = firestore.SERVER_TIMESTAMP
        job["updated_at"] = firestore.SERVER_TIMESTAMP

        doc_ref.set(job)

        request.session.pop("job", None)

        return RedirectResponse(
            url="/manage-jobs?success=draft",
            status_code=303
        )
    
    company = get_company()

    # If not draft, show the review page
    return templates.TemplateResponse(
        request=request,
        name="reviewJob.html",
        context={
            "request": request,
            "job": request.session["job"],
            "is_edit": False,
            "company": company
            
        }
    )

# ==================================================
# Cancel Button
# ==================================================

@router.get("/cancel-job")
async def cancel_job(request: Request):

    # Clear temporary job information from session
    request.session.pop("job", None)

    return RedirectResponse(
        url="/manage-jobs",
        status_code=303
    )


# ==================================================
# Review Page
# ==================================================

@router.get("/review-job", response_class=HTMLResponse)
async def review_page(request: Request):

    company = get_company()
    
    job = request.session.get("job")

    if not job:
        return RedirectResponse(
            url="/publish-job",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="reviewJob.html",
        context={
            "request": request,
            "job": job,
            "is_edit": False,
            "company": company
        }
    )

@router.get("/delete-job/{job_id}")
async def delete_job(job_id: str):

    # Change status to Deleted instead of permanently deleting document
    db.collection("job_list").document(job_id).update({
        "status": "Deleted",
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    return RedirectResponse(
        url="/manage-jobs?success=deleted",
        status_code=303
    )

# ==================================================
# Edit Job Page
# ==================================================

@router.get("/edit-job/{job_id}", response_class=HTMLResponse)
async def edit_job(request: Request, job_id: str):

    job_ref = db.collection("job_list").document(job_id)
    job_doc = job_ref.get()

    if not job_doc.exists:
        return RedirectResponse(
            url="/manage-jobs",
            status_code=303
        )

    company = get_company()
    job = job_doc.to_dict()

    # Temporarily add Firestore document ID for HTML
    job["job_id"] = job_id

    category_docs = db.collection("job_category").stream()

    categories = []

    for doc in category_docs:
        categories.append(doc.to_dict())

    return templates.TemplateResponse(
        request=request,
        name="editJob.html",
        context={
            "request": request,
            "job": job,
            "categories": categories,
            "company": company
        }
    )

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

    benefits: List[str] = Form([]),
    other_benefit: str = Form(""),

    action: str = Form("review")
):

    company = get_company()
    
    # Get original job from Firestore
    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        return RedirectResponse(
            url="/manage-jobs",
            status_code=303
        )

    original_job = job_doc.to_dict()
    original_status = original_job.get("status", "Active")


    # Add custom benefit
    if other_benefit.strip():
        benefits.append(other_benefit.strip())


    # Create salary display
    if salaryType == "fixed":

        salary_display = f"RM {salary}"

    elif salaryType == "range":

        salary_display = f"RM {minSalary} - RM {maxSalary}"

    else:

        salary_display = "Negotiable"


    # Store edited information
    edited_job = {

        "job_id": job_id,

        "job_title": job_title,
        "category": category,
        "employment_type": employment_type,
        "position": position,
        "vacancies": vacancies,
        "location": location,

        "job_desc": job_desc,
        "job_responsibility": job_responsibility,
        "job_req": job_req,
        "additional_info": additional_info,

        "salaryType": salaryType,
        "salary": salary,
        "minSalary": minSalary,
        "maxSalary": maxSalary,
        "salary_display": salary_display,

        "benefits": benefits,
        "other_benefit": other_benefit.strip(),

        # Keep original status
        "status": original_status
    }


    # ==========================================
    # Save Draft directly
    # ==========================================

    if action == "draft":

        # Only allow this if original job was Draft
        if original_status.lower() == "draft":

            edited_job["updated_at"] = firestore.SERVER_TIMESTAMP

            db.collection("job_list").document(job_id).update(
                edited_job
            )

        return RedirectResponse(
            url="/manage-jobs?success=draft",
            status_code=303
        )


    # ==========================================
    # Save temporary edit data to session
    # ==========================================

    request.session["edit_job"] = edited_job

    # Go to review page
    return templates.TemplateResponse(
        request=request,
        name="reviewJob.html",
        context={
            "request": request,
            "job": edited_job,
            "is_edit": True,
            "company": company
        }
    )

@router.post("/update-job-confirm/{job_id}")
async def update_job_confirm(
    request: Request,
    job_id: str
):

    edited_job = request.session.get("edit_job")

    if not edited_job:
        return RedirectResponse(
            url=f"/edit-job/{job_id}",
            status_code=303
        )

    edited_job = edited_job.copy()

    edited_job.pop("job_id", None)

    # If original status was Draft and user confirms publishing,
    # change status to Active
    if edited_job.get("status", "").lower() == "draft":
        edited_job["status"] = "Active"

    # Update timestamp
    edited_job["updated_at"] = firestore.SERVER_TIMESTAMP

    # Update existing Firestore document
    db.collection("job_list").document(job_id).update(
        edited_job
    )

    # Clear temporary edit session
    request.session.pop("edit_job", None)

    return RedirectResponse(
        url="/manage-jobs?success=edited",
        status_code=303
    )