from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
    Form,
    UploadFile,
    File,
    HTTPException
)

import re
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from job_portal_web.backend.database import db, bucket

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


# ==================================================
# Edit Profile Page
# ==================================================

@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile(request: Request):

    applicant_id = "applicant001"

    doc = db.collection("applicants").document(applicant_id).get()

    applicant = {}

    if doc.exists:
        applicant = doc.to_dict()

    return templates.TemplateResponse(
        request=request,
        name="edit_jobSeeker_profile.html",
        context={
            "applicant": applicant
        }
    )


# ==================================================
# Save Profile
# ==================================================

@router.post("/edit-profile")
async def save_profile(

    full_name: str = Form(...),
    date_of_birth: str = Form(""),
    gender: str = Form(""),
    nationality: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    location: str = Form(""),
    current_position: str = Form(""),
    experience_level: str = Form(""),
    current_company: str = Form(""),
    about_me: str = Form(""),
    profile_photo: UploadFile | None = File(None)

):

    applicant_id = "applicant001"

    print("========== EDIT PROFILE ==========")
    print("Full Name:", full_name)
    print("Email:", email)

    # ==========================================
    # Validation
    # ==========================================

    if not full_name.strip():

        return templates.TemplateResponse(
            request=request,
            name="edit_jobSeeker_profile.html",
            context={
                "applicant": {
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
                },
                "error": "Full name is required."
            },
            status_code=400
        )

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if email and not re.match(email_pattern, email):

        return templates.TemplateResponse(
            request=request,
            name="edit_jobSeeker_profile.html",
            context={
                "applicant": {
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
                },
                "error": "Invalid email address."
            },
            status_code=400
        )

    phone_pattern = r"^(\+60\s\d{1,2}-\d{7,8}|\+65\s\d{4}\s\d{4})$"

    if phone and not re.match(phone_pattern, phone):

        raise HTTPException(
            status_code=400,
            detail=(
                "Please enter a valid Malaysian or Singapore phone number. "
                "Examples: +60 11-12345678 or +65 8123 4567."
            )
        )

    allowed_types = [
        "image/png",
        "image/jpeg",
        "image/jpg"
    ]

    if profile_photo and profile_photo.filename:

        if profile_photo.content_type not in allowed_types:

            raise HTTPException(
                status_code=400,
                detail="Only PNG and JPG images are allowed."
            )

    image_url = None

    try:

        if profile_photo and profile_photo.filename:

            print("Uploading image...")
            print("Filename:", profile_photo.filename)

            blob = bucket.blob(
                f"profile_images/{applicant_id}_{profile_photo.filename}"
            )

            blob.upload_from_file(
                profile_photo.file,
                content_type=profile_photo.content_type
            )

            blob.make_public()

            image_url = blob.public_url

            print("Upload Success!")
            print("Image URL:", image_url)

    except Exception as e:

        print("========== IMAGE UPLOAD ERROR ==========")
        print(type(e).__name__)
        print(e)

    update_data = {

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

    }

    if image_url:

        update_data["image"] = image_url

    db.collection("applicants").document(applicant_id).set(
        update_data,
        merge=True
    )

    print("Firestore Updated Successfully!")

    return RedirectResponse(
        url="/profile",
        status_code=303
    )