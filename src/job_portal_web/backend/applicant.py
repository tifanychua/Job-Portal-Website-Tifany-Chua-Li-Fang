from fastapi import APIRouter
from .database import db, bucket
from datetime import timedelta

router = APIRouter()


# =================================
# Generate Firebase Storage Resume URL
# =================================


def get_resume_url(path):

    if not path:
        return None

    blob = bucket.blob(path)

    url = blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")

    return url


# =================================
# Get Skills
# =================================


def get_skills(skill_ids):

    skills = []

    for skill_id in skill_ids:

        skill_doc = db.collection("skills").document(skill_id).get()

        if skill_doc.exists:

            skill = skill_doc.to_dict()

            skills.append({"id": skill_id, "name": skill.get("name")})

    return skills


# =================================
# Get Job Seeker
# =================================


def get_job_seeker(job_seeker_id):

    if not job_seeker_id:
        return None

    seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

    if not seeker_doc.exists:
        return None

    seeker = seeker_doc.to_dict()

    skill_ids = seeker.get("skill", [])

    seeker["skills"] = get_skills(skill_ids)

    seeker.pop("skill", None)

    return seeker


# =================================
# GET ALL SHORTLISTED APPLICANTS
# =================================


@router.get("/api/applicants/shortlisted")
def get_shortlisted_candidates():

    applicants = []

    docs = db.collection("application").where("status", "==", "Shortlisted").stream()

    for doc in docs:

        application = doc.to_dict()

        application["applicationId"] = doc.id

        # Get job seeker information

        job_seeker_id = application.get("job_seeker_id")

        seeker = get_job_seeker(job_seeker_id)

        if seeker:
            application.update(seeker)

        # Answers

        answers = application.get("answers") or {}

        application["years_experience"] = answers.get("years_experience")

        application["notice_period"] = answers.get("notice_period")

        application["relocate"] = answers.get("relocate")

        # Resume

        application["resume_filename"] = application.get("resume_filename")

        application["resume_path"] = application.get("resume_path")

        application["resume_url"] = get_resume_url(application.get("resume_path"))

        application.pop("answers", None)

        applicants.append(application)

    return applicants


# =================================
# GET SINGLE APPLICATION
# Used for Schedule Interview Page
# =================================


@router.get("/api/applications/{application_id}")
def get_application(application_id: str):

    doc = db.collection("application").document(application_id).get()

    if not doc.exists:

        return {"error": "Application not found"}

    application = doc.to_dict()

    application["applicationId"] = application_id

    # Get job seeker information

    job_seeker_id = application.get("job_seeker_id")

    seeker = get_job_seeker(job_seeker_id)

    if seeker:

        application.update(seeker)

    # Answers

    answers = application.get("answers") or {}

    application["years_experience"] = answers.get("years_experience")

    application["notice_period"] = answers.get("notice_period")

    application["relocate"] = answers.get("relocate")

    # Resume

    application["resume_filename"] = application.get("resume_filename")

    application["resume_path"] = application.get("resume_path")

    application["resume_url"] = get_resume_url(application.get("resume_path"))

    application.pop("answers", None)

    return application
