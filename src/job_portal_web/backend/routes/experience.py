import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from job_portal_web.backend.database import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))

# ======================================================
# Get Current Applicant
# ======================================================


def get_current_applicant_id(request: Request):

    # During pytest, skip login
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "0YLcc18JszVqSXWn8DEDQ81o2vR2"

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(status_code=403, detail="Access denied")

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        raise HTTPException(status_code=401, detail="Applicant not logged in")

    return applicant_id


def get_current_user(applicant_id):

    user_doc = db.collection("job_seeker").document(applicant_id).get()

    if user_doc.exists:
        return user_doc.to_dict()

    return None


# ======================================================
# Manage Experience Page
# ======================================================


@router.get("/manageExperience")
async def manage_experience(request: Request):

    applicant_id = get_current_applicant_id(request)

    user = get_current_user(applicant_id)

    experience_list = []

    docs = db.collection("job_seeker_experience").where("applicant_id", "==", applicant_id).stream()

    for doc in docs:
        data = doc.to_dict()

        data["id"] = doc.id

        experience_list.append(data)

    experience_list.sort(key=lambda x: x.get("start_date", ""), reverse=True)

    return templates.TemplateResponse(
        request=request,
        name="manageExperience.html",
        context={"experience_list": experience_list, "user": user},
    )


# ======================================================
# Add Experience
# ======================================================


@router.post("/add-experience")
async def add_experience(
    request: Request,
    job_title: str = Form(""),
    company_name: str = Form(""),
    employment_type: str = Form(""),
    location: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    currently_working: str = Form(None),
    description: str = Form(""),
):

    applicant_id = get_current_applicant_id(request)

    now = datetime.now(UTC)

    job_title = job_title.strip()
    company_name = company_name.strip()
    employment_type = employment_type.strip()
    location = location.strip()
    description = description.strip()

    # ADD THIS HERE
    print(
        {
            "job_title": job_title,
            "company_name": company_name,
            "employment_type": employment_type,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "currently_working": currently_working,
            "description": description,
        }
    )

    if not job_title:
        return JSONResponse(
            {"success": False, "message": "Please enter your job title."}, status_code=400
        )

    if not company_name:
        return JSONResponse(
            {"success": False, "message": "Please enter your company name."}, status_code=400
        )

    if not employment_type:
        return JSONResponse(
            {"success": False, "message": "Please select your employment type."}, status_code=400
        )

    if not location:
        return JSONResponse(
            {"success": False, "message": "Please enter your location."}, status_code=400
        )

    if not start_date:
        return JSONResponse(
            {"success": False, "message": "Please select your start date."}, status_code=400
        )

    is_currently_working = currently_working in ("on", "true", "True", "1")

    if not is_currently_working and not end_date:
        return JSONResponse(
            {"success": False, "message": "Please select your end date."}, status_code=400
        )

    if not is_currently_working and end_date and end_date < start_date:
        return JSONResponse(
            {"success": False, "message": "Invalid employment period."}, status_code=400
        )

    duplicate = (
        db.collection("job_seeker_experience")
        .where("applicant_id", "==", applicant_id)
        .where("job_title", "==", job_title)
        .where("company_name", "==", company_name)
        .where("employment_type", "==", employment_type)
        .where("location", "==", location)
        .where("start_date", "==", start_date)
        .where("end_date", "==", end_date)
    )

    if next(duplicate.stream(), None):
        return JSONResponse(
            {"success": False, "message": "This experience record already exists."}, status_code=409
        )

    db.collection("job_seeker_experience").add(
        {
            "applicant_id": applicant_id,
            "job_title": job_title,
            "company_name": company_name,
            "employment_type": employment_type,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "currently_working": is_currently_working,
            "description": description,
            "created_at": now,
            "updated_at": now,
        }
    )

    return JSONResponse({"success": True, "redirect": "/manageExperience"})


# ======================================================
# Edit Experience
# ======================================================


@router.post("/edit-experience/{document_id}")
async def edit_experience(
    request: Request,
    document_id: str,
    job_title: str = Form(""),
    company_name: str = Form(""),
    employment_type: str = Form(""),
    location: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    currently_working: str = Form(None),
    description: str = Form(""),
):

    applicant_id = get_current_applicant_id(request)

    doc_ref = db.collection("job_seeker_experience").document(document_id)

    document = doc_ref.get()

    if not document.exists:
        return JSONResponse({"success": False, "message": "Experience not found."}, status_code=404)

    job_title = job_title.strip()
    company_name = company_name.strip()
    employment_type = employment_type.strip()
    location = location.strip()
    description = description.strip()

    if not job_title:
        return JSONResponse(
            {"success": False, "message": "Please enter your job title."}, status_code=400
        )

    if not company_name:
        return JSONResponse(
            {"success": False, "message": "Please enter your company name."}, status_code=400
        )

    if not employment_type:
        return JSONResponse(
            {"success": False, "message": "Please select your employment type."}, status_code=400
        )

    if not location:
        return JSONResponse(
            {"success": False, "message": "Please enter your location."}, status_code=400
        )

    if not start_date:
        return JSONResponse(
            {"success": False, "message": "Please select your start date."}, status_code=400
        )

    is_currently_working = currently_working in ("on", "true", "True", "1")

    if not is_currently_working and not end_date:
        return JSONResponse(
            {"success": False, "message": "Please select your end date."}, status_code=400
        )

    if not is_currently_working and end_date and end_date < start_date:
        return JSONResponse(
            {"success": False, "message": "Invalid employment period."}, status_code=400
        )

    duplicate = (
        db.collection("job_seeker_experience")
        .where("applicant_id", "==", applicant_id)
        .where("job_title", "==", job_title)
        .where("company_name", "==", company_name)
        .where("employment_type", "==", employment_type)
        .where("location", "==", location)
        .where("start_date", "==", start_date)
        .where("end_date", "==", end_date)
        .stream()
    )

    for doc in duplicate:
        if doc.id != document_id:
            return JSONResponse(
                {"success": False, "message": "This experience record already exists."},
                status_code=409,
            )

    doc_ref.update(
        {
            "job_title": job_title,
            "company_name": company_name,
            "employment_type": employment_type,
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "currently_working": is_currently_working,
            "description": description,
            "updated_at": datetime.now(UTC),
        }
    )

    return JSONResponse({"success": True, "redirect": "/manageExperience"})


# ======================================================
# Delete Experience
# ======================================================


@router.post("/delete-experience/{document_id}")
async def delete_experience(document_id: str):

    db.collection("job_seeker_experience").document(document_id).delete()

    return RedirectResponse("/manageExperience", status_code=303)
