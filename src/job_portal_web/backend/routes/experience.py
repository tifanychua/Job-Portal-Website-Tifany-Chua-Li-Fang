from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from job_portal_web.backend.database import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


# ======================================================
# Manage Experience Page
# ======================================================

@router.get("/manageExperience")
async def manage_experience(request: Request):

    applicant_id = "applicant001"

    experience_list = []

    docs = (
        db.collection("job_seeker_experience")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        experience_list.append(data)

    experience_list.sort(
        key=lambda x: x.get("start_date", ""),
        reverse=True
    )

    return templates.TemplateResponse(
        request=request,
        name="manageExperience.html",
        context={
            "experience_list": experience_list
        }
    )


# ======================================================
# Add Experience
# ======================================================

@router.post("/add-experience")
async def add_experience(

    job_title: str = Form(...),

    company_name: str = Form(...),

    employment_type: str = Form(...),

    location: str = Form(...),

    start_date: str = Form(...),

    end_date: str = Form(""),

    currently_working: str = Form(None),

    description: str = Form(""),

):

    applicant_id = "applicant001"

    now = datetime.utcnow()

    db.collection("job_seeker_experience").add({

        "applicant_id": applicant_id,

        "job_title": job_title,

        "company_name": company_name,

        "employment_type": employment_type,

        "location": location,

        "start_date": start_date,

        "end_date": end_date,

        "currently_working": currently_working is not None,

        "description": description,

        "created_at": now,

        "updated_at": now

    })

    return RedirectResponse(
        "/manageExperience",
        status_code=303
    )


# ======================================================
# Edit Experience
# ======================================================

@router.post("/edit-experience/{document_id}")
async def edit_experience(

    document_id: str,

    job_title: str = Form(...),

    company_name: str = Form(...),

    employment_type: str = Form(...),

    location: str = Form(...),

    start_date: str = Form(...),

    end_date: str = Form(""),

    currently_working: str = Form(None),

    description: str = Form(""),

):

    db.collection("job_seeker_experience") \
        .document(document_id) \
        .update({

            "job_title": job_title,

            "company_name": company_name,

            "employment_type": employment_type,

            "location": location,

            "start_date": start_date,

            "end_date": end_date,

            "currently_working": currently_working is not None,

            "description": description,

            "updated_at": datetime.utcnow()

        })

    return RedirectResponse(
        "/manageExperience",
        status_code=303
    )


# ======================================================
# Delete Experience
# ======================================================

@router.post("/delete-experience/{document_id}")
async def delete_experience(document_id: str):

    db.collection("job_seeker_experience") \
        .document(document_id) \
        .delete()

    return RedirectResponse(
        "/manageExperience",
        status_code=303
    )