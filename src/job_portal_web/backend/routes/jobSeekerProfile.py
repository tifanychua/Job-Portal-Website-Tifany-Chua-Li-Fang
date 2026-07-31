from pathlib import Path
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
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
        
    print("SESSION:", request.session)

    if request.session.get("user_type") != "job_seeker":

        raise HTTPException(status_code=403, detail="Access denied")

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:

        raise HTTPException(status_code=401, detail="Applicant not logged in")

    return applicant_id


# ======================================================
# View Profile
# ======================================================


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    applicant_id = get_current_applicant_id(request)

    # ===========================
    # Get Applicant Information
    # ===========================

    doc = db.collection("job_seeker").document(applicant_id).get()

    applicant = {}

    if doc.exists:

        applicant = doc.to_dict()

        print("Applicant data:", applicant)
        print("Image field:", applicant.get("image"))

    # ===========================
    # Load Education
    # ===========================

    education_docs = (
        db.collection("education")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    applicant["education"] = []

    for doc in education_docs:
        applicant["education"].append(doc.to_dict())

    # ===========================
    # Load Experience
    # ===========================

    experience_docs = (
        db.collection("job_seeker_experience")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    applicant["experience_list"] = []

    for doc in experience_docs:
        applicant["experience_list"].append(doc.to_dict())

    # ===========================
    # Load Skills
    # ===========================

    applicant["skills"] = []

    skill_docs = (
    db.collection("job_seeker_skill")
    .where("applicant_id", "==", applicant_id)
    .stream()
)

    applicant["skills"] = []

    for doc in skill_docs:

        data = doc.to_dict()

        skill_id = data.get("skill_id")

        if skill_id:

            skill_doc = db.collection("skills").document(skill_id).get()

            if skill_doc.exists:

                skill_data = skill_doc.to_dict()

                applicant["skills"].append(
                    skill_data.get("skill_name", skill_id)
                )

    # ===========================
    # Return Template
    # ===========================

    response = templates.TemplateResponse(
        request=request,
        name="jobSeekerProfile.html",
        context={
            # Shared header
            "user": applicant,

            # Profile page
            "applicant": applicant,
        },
    )

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response

