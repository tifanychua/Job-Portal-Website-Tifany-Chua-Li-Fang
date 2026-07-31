from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from firebase_admin import firestore

router = APIRouter()

db = firestore.client()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


def get_current_job_seeker_id(request: Request):

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(status_code=403, detail="Access denied")

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        raise HTTPException(status_code=401, detail="Job seeker not logged in")

    return applicant_id


@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile(request: Request):

    applicant_id = get_current_job_seeker_id(request)

    seeker_doc = db.collection("job_seeker").document(applicant_id).get()

    if seeker_doc.exists:

        seeker = seeker_doc.to_dict()

    else:

        seeker = {}

    return templates.TemplateResponse(
        request=request, name="edit_jobSeeker_profile.html", context={"seeker": seeker}
    )
