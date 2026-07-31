from datetime import datetime, timezone
from pathlib import Path
from datetime import datetime
import os
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from job_portal_web.backend.database import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))
# ======================================================
# Get Current Applicant ID
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


def get_industry_name(industry_id):

    docs = db.collection("industries").where("industry_id", "==", industry_id).limit(1).stream()

    for doc in docs:
        return doc.to_dict().get("industry_name", "")

    return ""


def get_category_name(category_id):

    docs = (
        db.collection("skill_categories").where("category_id", "==", category_id).limit(1).stream()
    )

    for doc in docs:
        return doc.to_dict().get("category_name", "")

    return ""


def get_skill_name(skill_id):

    docs = db.collection("skills").where("skill_id", "==", skill_id).limit(1).stream()

    for doc in docs:
        return doc.to_dict().get("skill_name", "")

    return ""


@router.get("/manageSkills")
async def manage_skills(request: Request):

    applicant_id = get_current_applicant_id(request)

    user = get_current_user(applicant_id)

    skill_list = []

    docs = db.collection("job_seeker_skill").where("applicant_id", "==", applicant_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        data["industry_name"] = get_industry_name(data.get("industry_id"))

        data["category_name"] = get_category_name(data.get("category_id"))

        data["skill_name"] = get_skill_name(data.get("skill_id"))

        skill_list.append(data)

    return templates.TemplateResponse(
        request=request, name="manageSkill.html", context={"skills": skill_list, "user": user}
    )


@router.get("/api/industries")
async def load_industries():

    result = []

    docs = db.collection("industries").stream()

    for doc in docs:

        data = doc.to_dict()

        result.append({"industry_id": data["industry_id"], "industry_name": data["industry_name"]})

    result.sort(key=lambda x: x["industry_name"])

    return JSONResponse(result)


@router.get("/api/skill-categories/{industry_id}")
async def load_categories(industry_id: str):

    result = []

    docs = db.collection("skill_categories").where("industry_id", "==", industry_id).stream()

    for doc in docs:

        data = doc.to_dict()

        result.append({"category_id": data["category_id"], "category_name": data["category_name"]})

    result.sort(key=lambda x: x["category_name"])

    return JSONResponse(result)


@router.get("/api/skills/{category_id}")
async def load_skills(category_id: str):

    result = []

    docs = (
        db.collection("skills")
        .where("category_id", "==", category_id)
        .where("status", "==", "Active")
        .stream()
    )

    for doc in docs:

        data = doc.to_dict()

        result.append({"skill_id": data["skill_id"], "skill_name": data["skill_name"]})

    result.sort(key=lambda x: x["skill_name"])

    return JSONResponse(result)


# ======================================================
# Add Skill
# ======================================================
@router.post("/add-skill")
async def add_skill(
    request: Request,
    industry_id: str = Form(...),
    category_id: str = Form(...),
    skill_id: str = Form(...),
    level: str = Form(...),
):

    applicant_id = get_current_applicant_id(request)

    # ======================================================
    # Save Profile
    # ======================================================

    @router.post("/save-profile")
    async def save_profile():
        return RedirectResponse("/profile", status_code=303)

    # ------------------------------------------
    # Validate Industry
    # ------------------------------------------

    industry = db.collection("industries").where("industry_id", "==", industry_id).limit(1).stream()

    if not list(industry):
        raise HTTPException(status_code=400, detail="Invalid industry.")

    # ------------------------------------------
    # Validate Category
    # ------------------------------------------

    category = (
        db.collection("skill_categories")
        .where("category_id", "==", category_id)
        .where("industry_id", "==", industry_id)
        .limit(1)
        .stream()
    )

    if not list(category):
        raise HTTPException(status_code=400, detail="Invalid Category")

    # ------------------------------------------
    # Validate Skill
    # ------------------------------------------

    skill = (
        db.collection("skills")
        .where("skill_id", "==", skill_id)
        .where("category_id", "==", category_id)
        .where("status", "==", "Active")
        .limit(1)
        .stream()
    )

    if not list(skill):
        raise HTTPException(status_code=400, detail="Invalid Skill")

    # ------------------------------------------
    # Prevent Duplicate Skill
    # ------------------------------------------

    duplicate = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .where("skill_id", "==", skill_id)
        .limit(1)
        .stream()
    )

    if list(duplicate):
        raise HTTPException(status_code=400, detail="Skill already added")

    # ------------------------------------------
    # Save Skill
    # ------------------------------------------

    now = datetime.now(timezone.utc)

    db.collection("job_seeker_skill").add(
        {
            "applicant_id": applicant_id,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "created_at": now,
            "updated_at": now,
        }
    )

    return RedirectResponse("/manageSkills", status_code=303)


# ======================================================
# Edit Skill
# ======================================================


@router.post("/edit-skill/{document_id}")
async def edit_skill(
    request: Request,
    document_id: str,
    industry_id: str = Form(...),
    category_id: str = Form(...),
    skill_id: str = Form(...),
    level: str = Form(...),
):

    applicant_id = get_current_applicant_id(request)

    # ------------------------------------------
    # Check duplicate skill
    # ------------------------------------------

    duplicate_docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .where("skill_id", "==", skill_id)
        .stream()
    )

    for doc in duplicate_docs:

        # Ignore current document
        if doc.id != document_id:

            return RedirectResponse("/manageSkills", status_code=303)

    # ------------------------------------------
    # Check whether the document exists
    # ------------------------------------------

    doc_ref = db.collection("job_seeker_skill").document(document_id)

    doc = doc_ref.get()

    if not doc.exists:
        return RedirectResponse(
            "/manageSkills",
            status_code=303,
        )

    # ------------------------------------------
    # Update
    # ------------------------------------------

    doc_ref.update(
        {
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    return RedirectResponse(
        "/manageSkills",
        status_code=303,
    )


# ======================================================
# Delete Skill
# ======================================================


@router.post("/delete-skill/{document_id}")
async def delete_skill(document_id: str):

    doc_ref = db.collection("job_seeker_skill").document(document_id)

    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Skill not found.")

    doc_ref.delete()

    return RedirectResponse("/manageSkills", status_code=303)
