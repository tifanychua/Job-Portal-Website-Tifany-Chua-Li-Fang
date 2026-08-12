import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from .database import bucket, db
from .job_information import (
    _attach_company_fields,
    _find_company,
    _normalize_job,
)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")
STATIC_DIR = os.path.join(BASE_DIR, "static")
RESUME_UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads", "resumes")

templates = Jinja2Templates(directory=UI_DIR)

MAX_RESUME_SIZE_MB = 5
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}

DEFAULT_QUESTIONS = [
    {
        "id": "years_experience",
        "label": "What is your total years of experience in this field?",
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
        "options": ["Immediate", "2 weeks", "1 month", "2 months", "3 months or more"],
    },
    {
        "id": "relocate",
        "label": None,  # filled in dynamically with company/location, see _get_screening_questions
        "type": "radio",
        "required": True,
        "options": ["Yes", "No", "Maybe"],
    },
]


def _get_screening_questions(job):
    """Use job-specific screening questions if the job document defines them,
    otherwise fall back to a sensible default set."""

    custom = job.get("screening_questions")

    if custom:
        return custom

    questions = [dict(q) for q in DEFAULT_QUESTIONS]

    questions[2]["label"] = (
        f"Are you willing to relocate or work from {job.get('companyName', 'the')} "
        f"office in {job.get('location', 'this location')}?"
    )

    return questions


def _get_currentjob_seeker(request: Request):
    job_seeker_id = request.session.get("applicant_id")

    if not job_seeker_id:
        return None, None

    doc = db.collection("job_seeker").document(job_seeker_id).get()

    if doc.exists:
        print(doc.to_dict())

    if not doc.exists:
        return job_seeker_id, None

    return job_seeker_id, doc.to_dict()


def _load_job(job_id: str):

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_doc.to_dict()
    job = _normalize_job(job, job_id)

    company = _find_company(job.get("company_id"))
    job = _attach_company_fields(job, company)

    return job


@router.get("/jobs/{job_id}/apply", name="job_apply")
def job_apply_form(request: Request, job_id: str):

    job = _load_job(job_id)

    job_seeker_id, job_seeker = _get_currentjob_seeker(request)

    job_seeker = job_seeker or {
        "full_name": "Guest Applicant",
        "headline": "Complete your profile to speed up applications",
        "photo": "",
    }
    user = job_seeker
    print(user)

    return templates.TemplateResponse(
        request=request,
        name="job_apply.html",
        context={
            "user": user,
            "request": request,
            "job": job,
            "job_seeker": job_seeker,
            "questions": _get_screening_questions(job),
        },
    )


@router.post("/jobs/{job_id}/apply", name="job_apply_submit")
async def job_apply_submit(
    request: Request,
    job_id: str,
    cover_letter: str = Form(""),
    resume: UploadFile = File(None),
):

    job = _load_job(job_id)

    job_seeker_id, job_seeker = _get_currentjob_seeker(request)

    # ==============================
    # Check Login
    # ==============================

    if not job_seeker_id:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Please log in to apply for this job.",
            },
        )

    form_data = await request.form()

    answers = {}

    for question in _get_screening_questions(job):
        answers[question["id"]] = form_data.get(f"answer_{question['id']}", "")

    # ==============================
    # Upload Resume
    # ==============================

    resume_name = None
    resume_path = None

    if resume is not None and resume.filename:
        ext = os.path.splitext(resume.filename)[1].lower()

        if ext not in ALLOWED_RESUME_EXTENSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Resume must be a PDF, DOC, or DOCX file.",
                },
            )

        contents = await resume.read()

        if len(contents) > MAX_RESUME_SIZE_MB * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": f"Resume must be under {MAX_RESUME_SIZE_MB}MB.",
                },
            )

        resume_name = f"{job_seeker_id}_{job_id}_{uuid.uuid4().hex[:8]}{ext}"

        blob = bucket.blob(f"resumes/{resume_name}")

        blob.upload_from_string(contents, content_type=resume.content_type)

        resume_path = blob.name

    application_ref = db.collection("application").document()

    application_ref.set(
        {
            "job_id": job_id,
            "job_seeker_id": job_seeker_id,
            "resume_filename": resume_name,
            "resume_path": resume_path,
            "cover_letter": cover_letter,
            "answers": answers,
            "status": "Submitted",
            "created_at": datetime.now(UTC),
            "updated_on": datetime.now(UTC),
        }
    )

    user = job_seeker

    return JSONResponse(
        content=jsonable_encoder(
            {
                "user": user,
                "success": True,
                "message": "Application submitted successfully!",
                "application_id": application_ref.id,
                "redirect_url": f"/jobs/{job_id}",
            }
        )
    )
