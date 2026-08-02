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
# GET CURRENT APPLICANT ID
# ======================================================


def get_current_applicant_id(request: Request) -> str:
    """
    Return the currently logged-in job seeker's applicant ID.

    During pytest, TEST_APPLICANT_ID can be used to isolate
    test records belonging to different test modules.
    """

    if os.getenv("PYTEST_CURRENT_TEST"):
        return os.getenv(
            "TEST_APPLICANT_ID",
            "0YLcc18JszVqSXWn8DEDQ81o2vR2",
        )

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        raise HTTPException(
            status_code=401,
            detail="Applicant not logged in",
        )

    return applicant_id


# ======================================================
# HELPER FUNCTIONS
# ======================================================


def get_current_user(applicant_id: str):
    user_document = db.collection("job_seeker").document(applicant_id).get()

    if not user_document.exists:
        return None

    return user_document.to_dict()


def get_industry_name(industry_id: str) -> str:
    documents = (
        db.collection("industries").where("industry_id", "==", industry_id).limit(1).stream()
    )

    for document in documents:
        data = document.to_dict()

        if data is not None:
            return data.get("industry_name", "")

    return ""


def get_category_name(category_id: str) -> str:
    documents = (
        db.collection("skill_categories").where("category_id", "==", category_id).limit(1).stream()
    )

    for document in documents:
        data = document.to_dict()

        if data is not None:
            return data.get("category_name", "")

    return ""


def get_skill_name(skill_id: str) -> str:
    documents = db.collection("skills").where("skill_id", "==", skill_id).limit(1).stream()

    for document in documents:
        data = document.to_dict()

        if data is not None:
            return data.get("skill_name", "")

    return ""


def create_skill_document_id(
    applicant_id: str,
    skill_id: str,
) -> str:
    """
    Generate one deterministic document ID for each
    applicant and skill combination.
    """

    return f"{applicant_id}_{skill_id}"


def validate_required_values(
    industry_id: str,
    category_id: str,
    skill_id: str,
    level: str,
) -> None:
    if not industry_id:
        raise HTTPException(
            status_code=400,
            detail="Industry is required",
        )

    if not category_id:
        raise HTTPException(
            status_code=400,
            detail="Skill category is required",
        )

    if not skill_id:
        raise HTTPException(
            status_code=400,
            detail="Skill is required",
        )

    if not level:
        raise HTTPException(
            status_code=400,
            detail="Level is required",
        )


def validate_industry(industry_id: str) -> None:
    documents = list(
        db.collection("industries").where("industry_id", "==", industry_id).limit(1).stream()
    )

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="Invalid Industry",
        )


def validate_category(
    industry_id: str,
    category_id: str,
) -> None:
    documents = list(
        db.collection("skill_categories")
        .where("category_id", "==", category_id)
        .where("industry_id", "==", industry_id)
        .limit(1)
        .stream()
    )

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="Invalid Category",
        )


def validate_skill(
    category_id: str,
    skill_id: str,
) -> None:
    documents = list(
        db.collection("skills")
        .where("skill_id", "==", skill_id)
        .where("category_id", "==", category_id)
        .where("status", "==", "Active")
        .limit(1)
        .stream()
    )

    if not documents:
        raise HTTPException(
            status_code=400,
            detail="Invalid Skill",
        )


def validate_skill_selection(
    industry_id: str,
    category_id: str,
    skill_id: str,
    level: str,
) -> None:
    validate_required_values(
        industry_id=industry_id,
        category_id=category_id,
        skill_id=skill_id,
        level=level,
    )

    validate_industry(industry_id)

    validate_category(
        industry_id=industry_id,
        category_id=category_id,
    )

    validate_skill(
        category_id=category_id,
        skill_id=skill_id,
    )


# ======================================================
# MANAGE SKILLS PAGE
# ======================================================


@router.get("/manageSkills")
async def manage_skills(request: Request):
    applicant_id = get_current_applicant_id(request)
    user = get_current_user(applicant_id)

    skill_list = []

    documents = db.collection("job_seeker_skill").where("applicant_id", "==", applicant_id).stream()

    for document in documents:
        data = document.to_dict()

        if data is None:
            continue

        data["id"] = document.id

        data["industry_name"] = get_industry_name(data.get("industry_id", ""))

        data["category_name"] = get_category_name(data.get("category_id", ""))

        data["skill_name"] = get_skill_name(data.get("skill_id", ""))

        skill_list.append(data)

    return templates.TemplateResponse(
        request=request,
        name="manageSkill.html",
        context={
            "skills": skill_list,
            "user": user,
        },
    )


# ======================================================
# LOAD INDUSTRIES
# ======================================================


@router.get("/api/industries")
async def load_industries():
    result = []

    documents = db.collection("industries").stream()

    for document in documents:
        data = document.to_dict()

        if data is None:
            continue

        result.append(
            {
                "industry_id": data.get("industry_id", ""),
                "industry_name": data.get("industry_name", ""),
            }
        )

    result.sort(key=lambda item: item["industry_name"])

    return JSONResponse(result)


# ======================================================
# LOAD SKILL CATEGORIES
# ======================================================


@router.get("/api/skill-categories/{industry_id}")
async def load_categories(industry_id: str):
    result = []

    documents = db.collection("skill_categories").where("industry_id", "==", industry_id).stream()

    for document in documents:
        data = document.to_dict()

        if data is None:
            continue

        result.append(
            {
                "category_id": data.get("category_id", ""),
                "category_name": data.get("category_name", ""),
            }
        )

    result.sort(key=lambda item: item["category_name"])

    return JSONResponse(result)


# ======================================================
# LOAD SKILLS
# ======================================================


@router.get("/api/skills/{category_id}")
async def load_skills(category_id: str):
    result = []

    documents = (
        db.collection("skills")
        .where("category_id", "==", category_id)
        .where("status", "==", "Active")
        .stream()
    )

    for document in documents:
        data = document.to_dict()

        if data is None:
            continue

        result.append(
            {
                "skill_id": data.get("skill_id", ""),
                "skill_name": data.get("skill_name", ""),
            }
        )

    result.sort(key=lambda item: item["skill_name"])

    return JSONResponse(result)


# ======================================================
# ADD SKILL
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

    industry_id = industry_id.strip()
    category_id = category_id.strip()
    skill_id = skill_id.strip()
    level = level.strip()

    validate_skill_selection(
        industry_id=industry_id,
        category_id=category_id,
        skill_id=skill_id,
        level=level,
    )

    document_id = create_skill_document_id(
        applicant_id=applicant_id,
        skill_id=skill_id,
    )

    document_reference = db.collection("job_seeker_skill").document(document_id)

    existing_document = document_reference.get()

    if existing_document.exists:
        raise HTTPException(
            status_code=400,
            detail="Skill already added",
        )

    older_duplicate_documents = list(
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .where("skill_id", "==", skill_id)
        .limit(1)
        .stream()
    )

    if older_duplicate_documents:
        raise HTTPException(
            status_code=400,
            detail="Skill already added",
        )

    current_time = datetime.now(UTC)

    document_reference.set(
        {
            "id": document_id,
            "applicant_id": applicant_id,
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "created_at": current_time,
            "updated_at": current_time,
        }
    )

    return RedirectResponse(
        url="/manageSkills",
        status_code=303,
    )


# ======================================================
# SAVE PROFILE
# ======================================================


@router.post("/save-profile")
async def save_profile():
    return RedirectResponse(
        url="/profile",
        status_code=303,
    )


# ======================================================
# EDIT SKILL
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

    industry_id = industry_id.strip()
    category_id = category_id.strip()
    skill_id = skill_id.strip()
    level = level.strip()

    validate_required_values(
        industry_id=industry_id,
        category_id=category_id,
        skill_id=skill_id,
        level=level,
    )

    document_reference = db.collection("job_seeker_skill").document(document_id)

    document = document_reference.get()

    if not document.exists:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    existing_data = document.to_dict()

    if existing_data is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    if existing_data.get("applicant_id") != applicant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    validate_industry(industry_id)

    validate_category(
        industry_id=industry_id,
        category_id=category_id,
    )

    validate_skill(
        category_id=category_id,
        skill_id=skill_id,
    )

    duplicate_documents = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .where("skill_id", "==", skill_id)
        .stream()
    )

    for duplicate_document in duplicate_documents:
        if duplicate_document.id != document_id:
            raise HTTPException(
                status_code=400,
                detail="Skill already added",
            )

    current_time = datetime.now(UTC)

    document_reference.update(
        {
            "industry_id": industry_id,
            "category_id": category_id,
            "skill_id": skill_id,
            "level": level,
            "updated_at": current_time,
        }
    )

    return RedirectResponse(
        url="/manageSkills",
        status_code=303,
    )


# ======================================================
# DELETE SKILL
# ======================================================


@router.post("/delete-skill/{document_id}")
async def delete_skill(
    request: Request,
    document_id: str,
):
    applicant_id = get_current_applicant_id(request)

    document_reference = db.collection("job_seeker_skill").document(document_id)

    document = document_reference.get()

    if not document.exists:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    data = document.to_dict()

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found",
        )

    if data.get("applicant_id") != applicant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    document_reference.delete()

    return RedirectResponse(
        url="/manageSkills",
        status_code=303,
    )
