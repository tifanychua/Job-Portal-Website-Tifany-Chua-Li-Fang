import os
import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from .database import bucket, db
from .job_information import (
    _attach_company_fields,
    _find_company,
    _normalize_job,
)
from .notifications import (
    get_unread_notifications_count,
)

router = APIRouter()


# =====================================================
# Directories
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(
    BASE_DIR,
    "ui",
)

STATIC_DIR = os.path.join(
    BASE_DIR,
    "static",
)

RESUME_UPLOAD_DIR = os.path.join(
    STATIC_DIR,
    "uploads",
    "resumes",
)

templates = Jinja2Templates(directory=UI_DIR)


# =====================================================
# Resume Configuration
# =====================================================

MAX_RESUME_SIZE_MB = 5

ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}


# =====================================================
# Default Screening Questions
# =====================================================

DEFAULT_QUESTIONS = [
    {
        "id": "years_experience",
        "label": ("What is your total years of " "experience in this field?"),
        "type": "select",
        "required": True,
        "options": [
            "Less than 1 year",
            "1 - 2 years",
            "3 - 5 years",
            "6 - 10 years",
            "10+ years",
        ],
    },
    {
        "id": "notice_period",
        "label": "What is your notice period?",
        "type": "select",
        "required": True,
        "options": [
            "Immediate",
            "2 weeks",
            "1 month",
            "2 months",
            "3 months or more",
        ],
    },
    {
        "id": "relocate",
        "label": None,
        "type": "radio",
        "required": True,
        "options": [
            "Yes",
            "No",
            "Maybe",
        ],
    },
]


# =====================================================
# Screening Questions
# =====================================================


def _get_screening_questions(job: dict):
    custom_questions = job.get("screening_questions")

    if custom_questions:
        return custom_questions

    questions = [dict(question) for question in DEFAULT_QUESTIONS]

    company_name = job.get("companyName") or job.get("company_name") or "the company"

    location = job.get("location") or "this location"

    questions[2]["label"] = (
        "Are you willing to relocate or work " f"from {company_name}'s office in " f"{location}?"
    )

    return questions


# =====================================================
# Current Job Seeker
# =====================================================


def _load_current_job_seeker(
    request: Request,
):
    if request.session.get("user_type") != "job_seeker":
        return None, None

    job_seeker_id = (
        request.session.get("applicant_id")
        or request.session.get("job_seeker_id")
        or request.session.get("user_id")
    )

    if not job_seeker_id:
        return None, None

    job_seeker_id = str(job_seeker_id)

    job_seeker_document = db.collection("job_seeker").document(job_seeker_id).get()

    if not job_seeker_document.exists:
        return job_seeker_id, None

    return (
        job_seeker_id,
        job_seeker_document.to_dict(),
    )


# Compatibility function required by existing tests.
def _get_currentjob_seeker(
    request: Request,
):
    return _load_current_job_seeker(request)


# Function used by current routes.
def _get_current_job_seeker(
    request: Request,
):
    result = _get_currentjob_seeker(request)

    # New/current return format:
    # (job_seeker_id, job_seeker_data)
    if isinstance(result, tuple) and len(result) == 2:
        return result

    # Compatibility with a test returning a dictionary.
    if isinstance(result, dict):
        job_seeker_id = (
            result.get("job_seeker_id")
            or result.get("applicant_id")
            or result.get("user_id")
            or result.get("id")
            or request.session.get("applicant_id")
        )

        if not job_seeker_id:
            return None, None

        return str(job_seeker_id), result

    # Compatibility with a test returning only an ID.
    if result:
        job_seeker_id = str(result)

        job_seeker_document = db.collection("job_seeker").document(job_seeker_id).get()

        if job_seeker_document.exists:
            return (
                job_seeker_id,
                job_seeker_document.to_dict(),
            )

        return (
            job_seeker_id,
            {
                "job_seeker_id": job_seeker_id,
                "applicant_id": job_seeker_id,
            },
        )

    return None, None


# =====================================================
# Load Job
# =====================================================


def _load_job(job_id: str):
    job_document = db.collection("job_list").document(job_id).get()

    if not job_document.exists:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    job = job_document.to_dict() or {}

    job = _normalize_job(
        job,
        job_id,
    )

    company = _find_company(job.get("company_id"))

    job = _attach_company_fields(
        job,
        company,
    )

    return job


# =====================================================
# Job Application Form
# =====================================================


@router.get(
    "/jobs/{job_id}/apply",
    name="job_apply",
)
def job_apply_form(
    request: Request,
    job_id: str,
):
    job = _load_job(job_id)

    job_seeker_id, job_seeker = _get_current_job_seeker(request)

    job_seeker_display = job_seeker or {
        "full_name": "Guest Applicant",
        "headline": ("Complete your profile to speed " "up applications"),
        "photo": "",
    }

    return templates.TemplateResponse(
        request=request,
        name="job_apply.html",
        context={
            "user": job_seeker,
            "request": request,
            "job": job,
            "job_seeker": job_seeker_display,
            "questions": (_get_screening_questions(job)),
            "unread_notifications_count": (get_unread_notifications_count(request)),
        },
    )


# =====================================================
# Submit Job Application
# =====================================================


@router.post(
    "/jobs/{job_id}/apply",
    name="job_apply_submit",
)
async def job_apply_submit(
    request: Request,
    job_id: str,
    cover_letter: str = Form(""),
    resume: UploadFile | None = File(None),
):
    job = _load_job(job_id)

    job_seeker_id, job_seeker = _get_current_job_seeker(request)

    # ==============================================
    # Check Login
    # ==============================================

    if not job_seeker_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": ("Please log in to apply for " "this job."),
            },
        )

    # ==============================================
    # Check Registered Job Seeker
    # ==============================================

    if not job_seeker:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "message": (
                    "Only registered job seekers "
                    "can apply. Please log in with "
                    "a registered account."
                ),
            },
        )

    form_data = await request.form()

    answers = {}

    for question in _get_screening_questions(job):
        question_id = question["id"]

        answers[question_id] = form_data.get(
            f"answer_{question_id}",
            "",
        )

    # ==============================================
    # Upload Resume
    # ==============================================

    resume_name = None
    resume_path = None

    if resume is not None and resume.filename:
        extension = os.path.splitext(resume.filename)[1].lower()

        if extension not in ALLOWED_RESUME_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": ("Resume must be a PDF, " "DOC, or DOCX file."),
                },
            )

        contents = await resume.read()

        maximum_size = MAX_RESUME_SIZE_MB * 1024 * 1024

        if len(contents) > maximum_size:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": ("Resume must be under " f"{MAX_RESUME_SIZE_MB}MB."),
                },
            )

        resume_name = f"{job_seeker_id}_" f"{job_id}_" f"{uuid.uuid4().hex[:8]}" f"{extension}"

        blob = bucket.blob(f"resumes/{resume_name}")

        blob.upload_from_string(
            contents,
            content_type=resume.content_type,
        )

        resume_path = blob.name

    # ==============================================
    # Save Application
    # ==============================================

    application_reference = db.collection("application").document()

    now = datetime.now(UTC)

    application_reference.set(
        {
            "application_id": (application_reference.id),
            "job_id": job_id,
            "job_seeker_id": job_seeker_id,
            "applicant_id": job_seeker_id,
            "company_id": job.get("company_id"),
            "resume_filename": resume_name,
            "resume_path": resume_path,
            "cover_letter": cover_letter,
            "answers": answers,
            "status": "Submitted",
            "created_at": now,
            "updated_on": now,
        }
    )

    # ==============================================
    # Notify Employer
    # ==============================================

    applicant_name = job_seeker.get("name") or job_seeker.get("full_name") or "A candidate"

    job_title = job.get("job_title") or "your job posting"

    db.collection("notification").document().set(
        {
            "user_id": job.get("company_id"),
            "user_type": "employer",
            "is_read": False,
            "type": "application",
            "title": "New application received",
            "message": (f"{applicant_name} applied for " f"{job_title}."),
            "link": "/applications",
            "created_at": now,
        }
    )

    return JSONResponse(
        content=jsonable_encoder(
            {
                "user": job_seeker,
                "success": True,
                "message": ("Application submitted " "successfully!"),
                "application_id": (application_reference.id),
                "redirect_url": f"/jobs/{job_id}",
            }
        )
    )
