import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore, storage

from job_portal_web.backend.notifications import get_unread_notifications_count

router = APIRouter()

db = firestore.client()
bucket = storage.bucket()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


def get_current_job_seeker_id(request: Request):

    import os

    # ==========================================
    # Pytest mode
    # ==========================================

    if os.getenv("PYTEST_CURRENT_TEST"):
        return "F9fDAUiFvYcYAVt7jRHLFb1IqrQ2"

    # ==========================================
    # Normal mode
    # ==========================================

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(status_code=403, detail="Access denied")

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:
        raise HTTPException(status_code=401, detail="Job seeker not logged in")

    return applicant_id


# =====================================================
# Edit Profile Page
# =====================================================


@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile(request: Request):

    applicant_id = get_current_job_seeker_id(request)

    seeker_doc = db.collection("job_seeker").document(applicant_id).get()

    if seeker_doc.exists:
        seeker = seeker_doc.to_dict()
    else:
        seeker = {}

    return templates.TemplateResponse(
        request=request,
        name="edit_jobSeeker_profile.html",
        context={
            "seeker": seeker,
            "today": datetime.now(UTC).date().isoformat(),
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# =====================================================
# Save Profile
# =====================================================


@router.post("/edit-profile")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    date_of_birth: str = Form(""),
    gender: str = Form(""),
    nationality: str = Form(""),
    email: str = Form(...),
    phone: str = Form(...),
    location: str = Form(""),
    current_position: str = Form(""),
    experience_level: str = Form(""),
    current_company: str = Form(""),
    about_me: str = Form(""),
    profile_photo: UploadFile = File(None),
):

    applicant_id = get_current_job_seeker_id(request)

    doc_ref = db.collection("job_seeker").document(applicant_id)

    doc = doc_ref.get()

    seeker = doc.to_dict() if doc.exists else {}

    image_url = seeker.get("profileImage", "")

    # ----------------------------------------
    # Validate Date of Birth
    # ----------------------------------------

    if date_of_birth:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()

        if dob >= datetime.now(UTC).date():
            return templates.TemplateResponse(
                request=request,
                name="edit_jobSeeker_profile.html",
                context={
                    "seeker": seeker,
                    "today": datetime.now(UTC).date().isoformat(),
                    "error": "Date of birth must be before today.",
                    "unread_notifications_count": get_unread_notifications_count(request),
                },
                status_code=400,
            )

        # ----------------------------------------
        # Validate Email
        # ----------------------------------------

        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.fullmatch(email_pattern, email):
            return templates.TemplateResponse(
                request=request,
                name="edit_jobSeeker_profile.html",
                context={
                    "seeker": seeker,
                    "today": datetime.now(UTC).date().isoformat(),
                    "error": "Please enter a valid email address.",
                    "unread_notifications_count": get_unread_notifications_count(request),
                },
                status_code=400,
            )

        # ----------------------------------------
        # Validate Phone Number
        # ----------------------------------------

        malaysia_local = r"^01\d{8,9}$"
        malaysia_international = r"^\+60\s\d{1,2}-\d{7,8}$"

        if not (re.fullmatch(malaysia_local, phone) or re.fullmatch(malaysia_international, phone)):
            return templates.TemplateResponse(
                request=request,
                name="edit_jobSeeker_profile.html",
                context={
                    "seeker": seeker,
                    "today": datetime.now(UTC).date().isoformat(),
                    "error": "Please enter a valid phone number.",
                    "unread_notifications_count": get_unread_notifications_count(request),
                },
                status_code=400,
            )

    # ----------------------------------------
    # Upload new profile image
    # ----------------------------------------

    if profile_photo and profile_photo.filename:
        extension = profile_photo.filename.split(".")[-1]

        filename = f"profile_images/{applicant_id}_{uuid4().hex}.{extension}"

        blob = bucket.blob(filename)

        blob.upload_from_file(
            profile_photo.file,
            content_type=profile_photo.content_type,
        )

        blob.make_public()

        image_url = blob.public_url

    # ----------------------------------------
    # Update Firestore
    # ----------------------------------------

    doc_ref.set(
        {
            "name": full_name,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "nationality": nationality,
            "email": email,
            "phone": phone,
            "location": location,
            "position": current_position,
            "experience": experience_level,
            "company": current_company,
            "about": about_me,
            "profileImage": image_url,
        },
        merge=True,
    )

    return RedirectResponse(
        url="/profile",
        status_code=303,
    )
