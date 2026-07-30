from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from job_portal_web.backend.database import db
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    applicant_id = "applicant001"

    # Get applicant information
    doc = db.collection("applicants").document(applicant_id).get()

    applicant = {}

    if doc.exists:
        applicant = doc.to_dict()

    # ==========================================
    # Load applicant skills
    # ==========================================

    applicant["skills"] = []

    skill_docs = (
        db.collection("job_seeker_skill")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    for skill_doc in skill_docs:

        skill = skill_doc.to_dict()

        applicant["skills"].append(
            skill["skill_id"]
        )

    return templates.TemplateResponse(
        request=request,
        name="jobSeekerProfile.html",
        context={
            "applicant": applicant
        }
    )

# ======================================================
# Save Profile
# ======================================================

@router.post("/save-profile")
async def save_profile():

    return JSONResponse(
        content={
            "message": "Profile saved successfully."
        },
        status_code=200
    )