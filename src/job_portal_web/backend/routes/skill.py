from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from job_portal_web.backend.database import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))

def get_industry_name(industry_id):

    docs = (
        db.collection("industries")
        .where("industry_id", "==", industry_id)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.to_dict().get("industry_name", "")

    return ""


def get_category_name(category_id):

    docs = (
        db.collection("skill_categories")
        .where("category_id", "==", category_id)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.to_dict().get("category_name", "")

    return ""


def get_skill_name(skill_id):

    docs = (
        db.collection("skills")
        .where("skill_id", "==", skill_id)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.to_dict().get("skill_name", "")

    return ""

@router.get("/manageSkills")
async def manage_skills(request: Request):

    applicant_id = "applicant001"

    skill_list = []

    docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        data["industry_name"] = get_industry_name(
            data.get("industry_id")
        )

        data["category_name"] = get_category_name(
            data.get("category_id")
        )

        data["skill_name"] = get_skill_name(
            data.get("skill_id")
        )

        skill_list.append(data)

    return templates.TemplateResponse(
        request=request,
        name="manageSkill.html",
        context={
            "skills": skill_list
        }
    )

@router.get("/api/industries")
async def load_industries():

    result = []

    docs = db.collection("industries").stream()

    for doc in docs:

        data = doc.to_dict()

        result.append({

            "industry_id": data["industry_id"],
            "industry_name": data["industry_name"]

        })

    result.sort(key=lambda x: x["industry_name"])

    return JSONResponse(result)

@router.get("/api/skill-categories/{industry_id}")
async def load_categories(industry_id: str):

    result = []

    docs = (
        db.collection("skill_categories")
        .where("industry_id", "==", industry_id)
        .stream()
    )

    for doc in docs:

        data = doc.to_dict()

        result.append({

            "category_id": data["category_id"],
            "category_name": data["category_name"]

        })

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

        result.append({

            "skill_id": data["skill_id"],
            "skill_name": data["skill_name"]

        })

    result.sort(key=lambda x: x["skill_name"])

    return JSONResponse(result)

# ======================================================
# Add Skill
# ======================================================

@router.post("/add-skill")
async def add_skill(
    industry_id: str = Form(...),
    category_id: str = Form(...),
    skill_id: str = Form(...),
    level: str = Form(...),
):

    # Temporary applicant
    applicant_id = "applicant001"

    # ------------------------------------------
    # Prevent duplicate skill
    # ------------------------------------------

    duplicate = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .where("skill_id", "==", skill_id)
        .limit(1)
        .stream()
    )

    if any(True for _ in duplicate):

        return RedirectResponse(
            "/manageSkills",
            status_code=303
        )

    # ------------------------------------------
    # Save
    # ------------------------------------------

    now = datetime.utcnow()

    db.collection("job_seeker_skill").add({

        "applicant_id": applicant_id,

        "industry_id": industry_id,

        "category_id": category_id,

        "skill_id": skill_id,

        "level": level,

        "created_at": now,

        "updated_at": now

    })

    return RedirectResponse(
        "/manageSkills",
        status_code=303
    )

# ======================================================
# Edit Skill
# ======================================================

@router.post("/edit-skill/{document_id}")
async def edit_skill(
    document_id: str,
    industry_id: str = Form(...),
    category_id: str = Form(...),
    skill_id: str = Form(...),
    level: str = Form(...),
):

    applicant_id = "applicant001"

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

            return RedirectResponse(
                "/manageSkills",
                status_code=303
            )

    # ------------------------------------------
    # Update
    # ------------------------------------------

    db.collection("job_seeker_skill") \
        .document(document_id) \
        .update({

            "industry_id": industry_id,

            "category_id": category_id,

            "skill_id": skill_id,

            "level": level,

            "updated_at": datetime.utcnow()

        })

    return RedirectResponse(
        "/manageSkills",
        status_code=303
    )

# ======================================================
# Delete Skill
# ======================================================

@router.post("/delete-skill/{document_id}")
async def delete_skill(document_id: str):

    db.collection("job_seeker_skill") \
        .document(document_id) \
        .delete()

    return RedirectResponse(
        "/manageSkills",
        status_code=303
    )