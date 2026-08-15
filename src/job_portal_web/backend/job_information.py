import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from .database import db
from .notifications import get_unread_notifications_count

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")

templates = Jinja2Templates(directory=UI_DIR)


def _find_company(company_id):

    if not company_id:
        return None

    company_doc = db.collection("company").document(company_id).get()

    if company_doc.exists:
        return company_doc.to_dict()

    return None


def _format_timestamp(ts):
    """Firestore timestamps come back as datetime objects; guard against
    missing values and plain strings too."""

    if not ts:
        return "—"

    if hasattr(ts, "strftime"):
        return ts.strftime("%B %d, %Y")

    return str(ts)


def _split_lines(text):
    """job_desc / job_req / job_responsibility are stored as single strings.
    Split on newlines so they can render as bullet lists when the user
    entered multiple lines, otherwise fall back to one paragraph-style item."""

    if not text:
        return []

    lines = [line.strip() for line in str(text).splitlines() if line.strip()]

    return lines


def _build_salary_display(job):

    if job.get("salary_display"):
        return job["salary_display"]

    salary_type = job.get("salaryType")

    if salary_type == "negotiable":
        return "Negotiable"

    min_salary = job.get("minSalary")
    max_salary = job.get("maxSalary")

    if min_salary and max_salary:
        return f"RM {min_salary} - RM {max_salary}"

    if job.get("salary"):
        return job["salary"]

    return "Not disclosed"


def _normalize_job(job, job_id):

    job["id"] = job_id

    job.setdefault("job_title", "Untitled Position")
    job.setdefault("category", "General")
    job.setdefault("position", "Not specified")
    job.setdefault("location", "Not specified")
    job.setdefault("employment_type", "Not specified")
    job.setdefault("status", "Active")
    job.setdefault("vacancies", 0)
    job.setdefault("benefits", [])
    job.setdefault("other_benefit", "")
    job.setdefault("additional_info", "")

    job["salary_display"] = _build_salary_display(job)
    job["job_desc_lines"] = _split_lines(job.get("job_desc"))
    job["job_req_lines"] = _split_lines(job.get("job_req"))
    job["job_responsibility_lines"] = _split_lines(job.get("job_responsibility"))
    job["created_at_display"] = _format_timestamp(job.get("created_at"))
    job["updated_at_display"] = _format_timestamp(job.get("updated_at"))

    return job


def _attach_company_fields(job, company):

    job.setdefault("company_logo", "default.jpg")
    job.setdefault("companyName", "Unknown")
    job.setdefault("company_verified", False)
    job["company_description"] = ""
    job["company_address"] = ""
    job["company_industry"] = ""
    job["company_website"] = ""

    if not company:
        return job

    job["companyName"] = company.get("companyName", "Unknown")
    job["company_logo"] = company.get("logo", "default.jpg")
    job["company_verified"] = company.get("verified", False)
    job["company_description"] = company.get("description", "")
    job["company_address"] = company.get("address", "")
    job["company_industry"] = company.get("industry", "")
    job["company_website"] = company.get("website", "")

    return job


@router.get("/jobs/{job_id}", name="job_information")
def job_detail(request: Request, job_id: str):
    user = None

    if request.session.get("user_type") == "job_seeker":
        uid = request.session.get("applicant_id")

        if uid:
            doc = db.collection("job_seeker").document(uid).get()

            if doc.exists:
                user = doc.to_dict()

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_doc.to_dict()

    job = _normalize_job(job, job_id)

    # -----------------------------
    # Company information
    # -----------------------------

    company = _find_company(job.get("company_id"))

    job = _attach_company_fields(job, company)

    # -----------------------------
    # Check Existing Application
    # -----------------------------

    application_status = None
    application_id = None

    # Only check for an existing application when this session is actually
    # a logged-in job seeker -- matches the `user` check above. Without
    # this, a stale `applicant_id` left over from a previous login (e.g.
    # after switching accounts) could make this page report "already
    # applied" even though the header shows the visitor as logged out.
    if request.session.get("user_type") == "job_seeker":
        job_seeker_id = request.session.get("applicant_id")

        applications = (
            db.collection("application").where(filter=FieldFilter("job_id", "==", job_id)).stream()
        )

        for app in applications:
            application = app.to_dict()

            if (
                application.get("job_seeker_id") == job_seeker_id
                and application.get("status") == "Submitted"
            ):
                application_status = "Submitted"
                application_id = app.id

                break

    # -----------------------------
    # Similar jobs
    # -----------------------------

    similar_jobs = []

    category = job.get("category")
    job_position = job.get("job_title")
    location = job.get("location")

    query = db.collection("job_list").where(filter=FieldFilter("status", "==", "Active"))

    docs = query.stream()

    scored_jobs = []

    for doc in docs:
        if doc.id == job_id:
            continue

        sim = doc.to_dict()

        score = 0

        # -----------------------------
        # Category
        # -----------------------------
        sim_category = sim.get("category")

        if category is not None and sim_category is not None:
            if category.lower() == sim_category.lower():
                score += 1

        # -----------------------------
        # Job Position
        # -----------------------------
        sim_position = sim.get("job_title")

        if job_position is not None and sim_position is not None:
            if job_position.lower() == sim_position.lower():
                score += 1

        # -----------------------------
        # Location
        # -----------------------------
        sim_location = sim.get("location")

        if location is not None and sim_location is not None:
            if location.lower() == sim_location.lower():
                score += 1

        # Only keep jobs with at least one similarity
        if score > 0:
            sim["id"] = doc.id
            sim["similarity_score"] = score

            sim.setdefault("job_title", "Untitled Position")
            sim.setdefault("location", "Not specified")

            sim_company = _find_company(sim.get("company_id"))

            if sim_company:
                sim["companyName"] = sim_company.get("companyName", "Unknown")
                sim["company_logo"] = sim_company.get("logo", "default.jpg")
            else:
                sim["companyName"] = "Unknown"
                sim["company_logo"] = "default.jpg"

            scored_jobs.append(sim)

    # -----------------------------
    # Highest similarity first
    # -----------------------------

    scored_jobs.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Maximum 2 similar jobs
    similar_jobs = scored_jobs[:2]

    return templates.TemplateResponse(
        request=request,
        name="job_information.html",
        context={
            "user": user,
            "request": request,
            "job": job,
            "similar_jobs": similar_jobs,
            # new data
            "application_status": application_status,
            "application_id": application_id,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )
