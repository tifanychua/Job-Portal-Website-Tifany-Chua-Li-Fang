from pathlib import Path
from typing import List
from fastapi import APIRouter, Request, Form, HTTPException

from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse


from fastapi.templating import Jinja2Templates

from ..helper import get_company

from firebase_admin import firestore

from ..database import db

router = APIRouter()


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


templates = Jinja2Templates(directory=str(BASE_DIR / "ui"))


# ==================================================
# Get Current Company ID
# ==================================================


def get_current_company_id(request: Request):

    if request.session.get("user_type") != "employer":

        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:

        raise HTTPException(status_code=401, detail="Company not logged in")

    return company_id


# ==================================================
# Publish Job Confirm
# ==================================================


@router.post("/publish-job-confirm")
async def publish_job_confirm(request: Request):

    job = request.session.get("job")

    if not job:

        return RedirectResponse(url="/publish-job", status_code=303)

    company = get_company(request)

    if company is None:

        return RedirectResponse("/login", status_code=303)

    company_id = get_current_company_id(request)

    doc_ref = db.collection("job_list").document()

    job["company_id"] = company_id

    job["status"] = "Active"

    job["created_at"] = firestore.SERVER_TIMESTAMP

    job["updated_at"] = firestore.SERVER_TIMESTAMP

    doc_ref.set(job)

    request.session.pop("job", None)

    return RedirectResponse(url="/manage-jobs?success=posted", status_code=303)


# ==================================================
# Manage Jobs
# ==================================================


@router.get("/manage-jobs", response_class=HTMLResponse)
async def manage_jobs(request: Request):

    company = get_company(request)

    if company is None:

        return RedirectResponse("/login", status_code=303)

    if company.get("status") != "Active":

        return templates.TemplateResponse(
            request=request,
            name="companyPending.html",
            context={"request": request, "company": company},
        )

    company_id = get_current_company_id(request)

    job_docs = db.collection("job_list").where("company_id", "==", company_id).stream()

    jobs = []

    for doc in job_docs:

        job_data = doc.to_dict()

        job_data["job_id"] = doc.id

        if job_data.get("status", "").lower() != "deleted":

            jobs.append(job_data)

    return templates.TemplateResponse(
        request=request,
        name="jobPosted.html",
        context={"request": request, "jobs": jobs, "company": company},
    )


# ==================================================
# Edit Job Page
# ==================================================


@router.get("/edit-job/{job_id}", response_class=HTMLResponse)
async def edit_job(request: Request, job_id: str):

    company = get_company(request)

    if company is None:
        return RedirectResponse("/login", status_code=303)

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:

        return RedirectResponse("/manage-jobs", status_code=303)

    job = job_doc.to_dict()

    job["job_id"] = job_id

    category_docs = db.collection("job_category").stream()

    categories = []

    for doc in category_docs:

        categories.append(doc.to_dict())

    return templates.TemplateResponse(
        request=request,
        name="editJob.html",
        context={"request": request, "job": job, "categories": categories, "company": company},
    )


# ==================================================
# Review Edit Job
# ==================================================


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
    action: str = Form("review"),
):

    company = get_company(request)

    if company is None:

        return RedirectResponse("/login", status_code=303)

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:

        return RedirectResponse("/manage-jobs", status_code=303)

    original_job = job_doc.to_dict()

    original_status = original_job.get("status", "Active")

    if other_benefit.strip():

        benefits.append(other_benefit.strip())

    if salaryType == "fixed":

        salary_display = f"RM {salary}"

    elif salaryType == "range":

        salary_display = f"RM {minSalary} - RM {maxSalary}"

    else:

        salary_display = "Negotiable"

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
        "status": original_status,
    }

    # Save draft directly

    if action == "draft":

        if original_status.lower() == "draft":

            edited_job.pop("job_id", None)

            edited_job["updated_at"] = firestore.SERVER_TIMESTAMP

            db.collection("job_list").document(job_id).update(edited_job)

        return RedirectResponse("/manage-jobs?success=draft", status_code=303)

    # Store temporary data

    request.session["edit_job"] = edited_job

    return templates.TemplateResponse(
        request=request,
        name="reviewJob.html",
        context={"request": request, "job": edited_job, "is_edit": True, "company": company},
    )


# ==================================================
# Confirm Update Job
# ==================================================


@router.post("/update-job-confirm/{job_id}")
async def update_job_confirm(request: Request, job_id: str):

    edited_job = request.session.get("edit_job")

    if not edited_job:

        return RedirectResponse(f"/edit-job/{job_id}", status_code=303)

    edited_job = edited_job.copy()

    edited_job.pop("job_id", None)

    # Convert Draft to Active after publish

    if edited_job.get("status", "").lower() == "draft":

        edited_job["status"] = "Active"

    edited_job["updated_at"] = firestore.SERVER_TIMESTAMP

    db.collection("job_list").document(job_id).update(edited_job)

    request.session.pop("edit_job", None)

    return RedirectResponse("/manage-jobs?success=edited", status_code=303)


# ==================================================
# Delete Job
# ==================================================


@router.get("/delete-job/{job_id}")
async def delete_job(request: Request, job_id: str):

    company_id = request.session.get("company_id")

    if not company_id:

        return RedirectResponse("/login", status_code=303)

    doc_ref = db.collection("job_list").document(job_id)

    doc = doc_ref.get()

    if not doc.exists:

        return RedirectResponse("/manage-jobs?error=notfound", status_code=303)

    job = doc.to_dict()

    # Prevent deleting another company's job

    if job.get("company_id") != company_id:

        return RedirectResponse("/manage-jobs?error=unauthorized", status_code=303)

    doc_ref.update({"status": "Deleted", "updated_at": firestore.SERVER_TIMESTAMP})

    return RedirectResponse("/manage-jobs?success=deleted", status_code=303)


# ==================================================
# View Job Details (Optional)
# ==================================================


@router.get("/view-job/{job_id}", response_class=HTMLResponse)
async def view_job(request: Request, job_id: str):

    company = get_company(request)

    if company is None:

        return RedirectResponse("/login", status_code=303)

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:

        return RedirectResponse("/manage-jobs", status_code=303)

    job = job_doc.to_dict()

    return templates.TemplateResponse(
        request=request,
        name="viewJob.html",
        context={"request": request, "job": job, "company": company},
    )


# ==================================================
# Restore Deleted Job (Optional)
# ==================================================


@router.get("/restore-job/{job_id}")
async def restore_job(request: Request, job_id: str):

    company_id = request.session.get("company_id")

    if not company_id:

        return RedirectResponse("/login", status_code=303)

    doc_ref = db.collection("job_list").document(job_id)

    doc = doc_ref.get()

    if not doc.exists:

        return RedirectResponse("/manage-jobs", status_code=303)

    job = doc.to_dict()

    if job.get("company_id") != company_id:

        return RedirectResponse("/manage-jobs", status_code=303)

    doc_ref.update({"status": "Active", "updated_at": firestore.SERVER_TIMESTAMP})

    return RedirectResponse("/manage-jobs?success=restored", status_code=303)


# ==================================================
# Company Job Statistics (Optional)
# ==================================================


@router.get("/job-statistics")
async def job_statistics(request: Request):

    company_id = request.session.get("company_id")

    if not company_id:

        return JSONResponse({"success": False, "message": "Not logged in"}, status_code=401)

    docs = db.collection("job_list").where("company_id", "==", company_id).stream()

    total = 0

    active = 0

    draft = 0

    deleted = 0

    for doc in docs:

        total += 1

        status = doc.to_dict().get("status", "").lower()

        if status == "active":

            active += 1

        elif status == "draft":

            draft += 1

        elif status == "deleted":

            deleted += 1

    return JSONResponse(
        {"success": True, "total": total, "active": active, "draft": draft, "deleted": deleted}
    )
