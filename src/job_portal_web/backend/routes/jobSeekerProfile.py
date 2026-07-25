from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
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

    doc = db.collection("applicants").document(applicant_id).get()

    applicant = {}

    if doc.exists:
        applicant = doc.to_dict()

    return templates.TemplateResponse(
        request=request,
        name="jobSeekerProfile.html",
        context={
            "applicant": applicant
        }
    )