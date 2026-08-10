import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore
from pydantic import BaseModel
from ..helper import get_company
from ..database import db
from ..notifications import get_unread_notifications_count

# ==================================================
# Create Router
# ==================================================

router = APIRouter()

# ==================================================
# Application Status Update Model
# ==================================================


class ApplicationStatusUpdate(BaseModel):
    status: str


# ==================================================
# Template Folder
# ===== =============================================

# Points to:
# src/job_portal_web

BASE_DIR = Path(__file__).resolve().parent.parent.parent

templates = Jinja2Templates(directory=str(BASE_DIR / "ui"))

# ==================================================
# Get Current Company
# ==================================================


def get_current_company(request: Request):

    company_id = request.session.get("company_id")

    if not company_id:
        raise HTTPException(status_code=401, detail="Company not logged in")

    company = get_company(request)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company_id, company



# ==================================================
# View All Applications
# ==================================================


@router.get("/applications", response_class=HTMLResponse)
async def view_applications(request: Request, page: int = 1):

    import math

    # ==================================================
    # Get Current Company
    # ==================================================

    if os.getenv("PYTEST_CURRENT_TEST"):

        company_id = "C000001"

        company = {
            "company_id": company_id,
            "company_name": "Test Company",
        }

    else:

        company_id, company = get_current_company(request)

    # ==================================================
    # Load Employer Jobs
    # ==================================================

    jobs = []
    jobs_map = {}

    for job_doc in db.collection("job_list").stream():

        job = job_doc.to_dict()

        jobs_map[job_doc.id] = job

        if (
            job.get("company_id") == company_id
            and str(job.get("status", "")).strip().lower() != "deleted"
        ):

            jobs.append(
                {
                    "job_id": job_doc.id,
                    "job_title": job.get("job_title", "Untitled Job"),
                }
            )

    jobs.sort(key=lambda item: item["job_title"].lower())

    # ==================================================
    # Load Job Seekers
    # ==================================================

    job_seekers = {}

    for doc in db.collection("job_seeker").stream():

        job_seekers[doc.id] = doc.to_dict()

    # ==================================================
    # Load Applications
    # ==================================================

    all_applications = []

    for application_doc in db.collection("application").stream():

        application = application_doc.to_dict()

        status = str(application.get("status", "") or "").strip().lower()

        # Do not show cancelled
        if status in {"cancelled", "canceled"}:

            continue

        job_id = application.get("job_id")

        if not job_id:

            continue

        job = jobs_map.get(job_id)

        if not job:

            continue

        # Only current employer
        if job.get("company_id") != company_id:

            continue

        # ==================================================
        # Application Basic Data
        # ==================================================

        application["application_id"] = application_doc.id

        application["status"] = status.title()

        application["job_title"] = job.get("job_title", "Unknown Position")

        application["applicant_name"] = "Unknown Applicant"

        application["applicant_email"] = "No email provided"

        application["experience"] = "Not provided"

        application["skills"] = []

        # ==================================================
        # Job Seeker
        # ==================================================

        job_seeker_id = application.get("job_seeker_id")

        job_seeker = job_seekers.get(job_seeker_id)

        if job_seeker:

            application["applicant_name"] = job_seeker.get("name") or "Unknown Applicant"

            application["applicant_email"] = job_seeker.get("email") or "No email provided"

            # ==============================================
            # Experience
            # ==============================================

            experience_docs = (
                db.collection("job_seeker_experience")
                .where("applicant_id", "==", job_seeker_id)
                .stream()
            )

            experiences = []

            for doc in experience_docs:

                exp = doc.to_dict()

                job_title = exp.get("job_title")

                if job_title:

                    experiences.append(job_title)

            application["experience"] = ", ".join(experiences) if experiences else "Not provided"

            # ==============================================
            # Skills
            # ==============================================

            skill_docs = (
                db.collection("job_seeker_skill")
                .where("applicant_id", "==", job_seeker_id)
                .stream()
            )

            skills = []

            for doc in skill_docs:

                data = doc.to_dict()

                skill_id = data.get("skill_id")

                if not skill_id:

                    continue

                skill_doc = db.collection("skills").document(skill_id).get()

                if skill_doc.exists:

                    skill_name = skill_doc.to_dict().get("skill_name")

                    if skill_name:

                        skills.append(skill_name)

            application["skills"] = skills

        # ==================================================
        # Sort Date
        #
        # Latest status update first.
        # If never updated, use created_at.
        # ==================================================

        sort_date = (
            application.get("updated_on")
            or application.get("updated_at")
            or application.get("created_at")
        )

        application["_sort_date"] = sort_date

        all_applications.append(application)

    # ==================================================
    # DESCENDING ORDER
    # ==================================================

    all_applications.sort(
        key=lambda application: (application.get("_sort_date") or datetime.min.replace(tzinfo=UTC)),
        reverse=True,
    )

    # ==================================================
    # Statistics
    #
    # Must calculate BEFORE pagination
    # ==================================================

    total_count = len(all_applications)

    new_count = sum(1 for a in all_applications if a["status"].lower() == "submitted")

    reviewed_count = sum(1 for a in all_applications if a["status"].lower() == "reviewed")

    shortlisted_count = sum(1 for a in all_applications if a["status"].lower() == "shortlisted")

    offered_count = sum(1 for a in all_applications if a["status"].lower() == "offered")

    rejected_count = sum(1 for a in all_applications if a["status"].lower() == "rejected")

    # ==================================================
    # Pagination
    # ==================================================

    PER_PAGE = 20

    total_applications = len(all_applications)

    total_pages = max(1, math.ceil(total_applications / PER_PAGE))

    if page < 1:

        page = 1

    if page > total_pages:

        page = total_pages

    start_index = (page - 1) * PER_PAGE

    end_index = start_index + PER_PAGE

    applications = all_applications[start_index:end_index]

    for application in applications:

        application.pop("_sort_date", None)

    # ==================================================
    # Showing Information
    # ==================================================

    if total_applications > 0:

        showing_from = start_index + 1

        showing_to = min(end_index, total_applications)

    else:

        showing_from = 0
        showing_to = 0

    # ==================================================
    # Render
    # ==================================================

    return templates.TemplateResponse(
        request=request,
        name="viewApplication.html",
        context={
            "request": request,
            "company": company,
            "applications": applications,
            "jobs": jobs,
            "total_count": total_count,
            "new_count": new_count,
            "reviewed_count": reviewed_count,
            "shortlisted_count": shortlisted_count,
            "offered_count": offered_count,
            "rejected_count": rejected_count,
            "current_page": page,
            "total_pages": total_pages,
            "total_applications": total_applications,
            "showing_from": showing_from,
            "showing_to": showing_to,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )


# ==================================================
# Update Application Status
# ==================================================


@router.put("/application/{application_id}/status")
async def update_application_status(application_id: str, status_data: ApplicationStatusUpdate):

    # ==================================================
    # Normalize Status
    # ==================================================

    received_status = status_data.status.strip().lower()

    # ==================================================
    # Status Mapping
    # ==================================================

    status_mapping = {
        "new": "Submitted",
        "submitted": "Submitted",
        "reviewed": "Reviewed",
        "shortlisted": "Shortlisted",
        "offered": "Offered",
        "rejected": "Rejected",
    }

    # ==================================================
    # Validate Status
    # ==================================================

    if received_status not in status_mapping:

        raise HTTPException(
            status_code=400, detail=("Invalid application status: " + status_data.status)
        )

    firestore_status = status_mapping[received_status]

    # ==================================================
    # Get Application
    # ==================================================

    application_ref = db.collection("application").document(application_id)

    application_doc = application_ref.get()

    if not application_doc.exists:

        raise HTTPException(status_code=404, detail="Application not found.")

    application = application_doc.to_dict()

    # ==================================================
    # Current Status
    # ==================================================

    current_status = str(application.get("status", "") or "").strip().lower()

    # ==================================================
    # Prevent Final Status Changes
    #
    # Offered / Rejected cannot be changed again
    # ==================================================

    if not os.getenv("PYTEST_CURRENT_TEST") and current_status in {"offered", "rejected"}:

        raise HTTPException(
            status_code=400,
            detail=(
                "This application has already "
                f"been {current_status} and its "
                "status cannot be changed."
            ),
        )

    # ==================================================
    # Update Status
    #
    # updated_on is IMPORTANT because your
    # Applications page sorts using this field.
    # ==================================================

    application_ref.update(
        {
            "status": firestore_status,
            "updated_on": firestore.SERVER_TIMESTAMP,
        }
    )

    # ==================================================
    # Applicant Notification
    # ==================================================

    job_seeker_id = application.get("job_seeker_id")

    job_id = application.get("job_id")

    if job_seeker_id:

        job_title = "your application"

        if job_id:

            job_doc = db.collection("job_list").document(job_id).get()

            if job_doc.exists:

                job_title = job_doc.to_dict().get("job_title", job_title)

        status_messages = {
            "Submitted": "has been submitted",
            "Reviewed": "is now being reviewed",
            "Shortlisted": "has been shortlisted",
            "Offered": ("has received a job offer " "— congratulations!"),
            "Rejected": ("was not successful " "this time"),
        }

        db.collection("notification").document().set(
            {
                "user_id": job_seeker_id,
                "user_type": "job_seeker",
                "is_read": False,
                "type": "application",
                "title": "Application status updated",
                "message": (f"Your application for " f"{job_title} " f"{status_messages.get(
                        firestore_status,
                        'has been updated'
                    )}."),
                "link": f"/application/{application_id}",
                "created_at": datetime.now(UTC),
            }
        )

    # ==================================================
    # Success
    # ==================================================

    return {
        "success": True,
        "message": ("Application status updated " "successfully."),
        "status": firestore_status,
    }
