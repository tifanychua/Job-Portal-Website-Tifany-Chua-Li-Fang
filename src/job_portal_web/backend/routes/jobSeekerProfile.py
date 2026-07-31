from pathlib import Path

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

    # ===========================
    # Load Skills
    # ===========================

    applicant["skills"] = []

    skill_docs = (
        db.collection("job_seeker_skill").where("applicant_id", "==", applicant_id).stream()
    )

    for skill_doc in skill_docs:

        skill = skill_doc.to_dict()

        applicant["skills"].append(skill.get("skill_id"))

    # ===========================
    # Return Template
    # ===========================

    return templates.TemplateResponse(
        request=request,
        name="jobSeekerProfile.html",
        context={
            # Shared header
            "user": applicant,
            # Profile page
            "applicant": applicant,
        },
    )
