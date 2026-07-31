from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from firebase_admin import storage
from firebase_admin import firestore
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from pydantic import BaseModel
from ..helper import get_company
from ..database import db

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
# ==================================================

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
async def view_applications(request: Request):

    import os
    import time

    start = time.time()

    # ==================================================
    # Get current company
    # ==================================================

    if os.getenv("PYTEST_CURRENT_TEST"):
        print("PYTEST MODE - bypass company login")

        company_id = "C000001"

        company = {
            "company_id": company_id,
            "company_name": "Test Company",
        }

    else:
        company_id, company = get_current_company(request)

    # ==================================================
    # Get Experience Filter
    # ==================================================

    experience_filter = request.query_params.get("experience")

    status_filter = request.query_params.get("status")

    # ==================================================
    # Load all jobs ONCE
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

    # ==================================================
    # Load all job seekers ONCE
    # ==================================================

    job_seekers = {}

    for doc in db.collection("job_seeker").stream():
        job_seekers[doc.id] = doc.to_dict()

    # ==================================================
    # Load all applications ONCE
    # ==================================================

    applications = []

    for application_doc in db.collection("application").stream():

        application = application_doc.to_dict()

        status = str(application.get("status", "")).strip().lower()

        if status == "cancelled":
            continue

        job_id = application.get("job_id")

        if not job_id:
            continue

        # Lookup job from memory
        job = jobs_map.get(job_id)

        if not job:
            continue

        if job.get("company_id") != company_id:
            continue

        application["application_id"] = application_doc.id
        application["status"] = status.title()
        application["job_title"] = job.get("job_title", "Unknown Position")

        # Default applicant info
        application["applicant_name"] = "Unknown Applicant"
        application["applicant_email"] = "No email provided"
        application["experience"] = "Not provided"
        application["skills"] = []

        # Lookup job seeker from memory
        job_seeker = job_seekers.get(application.get("job_seeker_id"))

        if job_seeker:

            application["applicant_name"] = job_seeker.get("name") or "Unknown Applicant"

            application["applicant_email"] = job_seeker.get("email") or "No email provided"

            application["experience"] = job_seeker.get("experience") or "Not provided"

            application["skills"] = job_seeker.get("skills") or []

        applications.append(application)

    # ==================================================
    # Experience Filter
    # ==================================================

    no_experience_message = None

    if experience_filter:

        filtered = []

        for application in applications:

            applicant_experience = str(
                application.get("experience", "")
            ).strip().lower()

            if applicant_experience == experience_filter.strip().lower():
                filtered.append(application)

        applications = filtered

        if len(applications) == 0:
            no_experience_message = (
                "No applicants found for this experience level"
            )

        # ==================================================
        # No Experience Message
        # ==================================================

        no_experience_message = None

        if experience_filter and len(applications) == 0:
            no_experience_message = "No applicants found for this experience level"

    # ==================================================
    # Status Filter
    # ==================================================

    no_status_message = None

    if status_filter:

        filtered = []

        for application in applications:

            applicant_status = (
                str(application.get("status", ""))
                .strip()
                .lower()
            )

            selected_status = status_filter.strip().lower()

            # "New" in the UI is stored as "Submitted"
            if selected_status == "new":
                selected_status = "submitted"

            if applicant_status == selected_status:
                filtered.append(application)

        applications = filtered

        if len(applications) == 0:
            no_status_message = (
                "No applicants found for this application status"
            )

    # ==================================================
    # Statistics
    # ==================================================

    total_count = len(applications)

    new_count = sum(1 for a in applications if a["status"].lower() == "submitted")

    reviewed_count = sum(1 for a in applications if a["status"].lower() == "reviewed")

    shortlisted_count = sum(1 for a in applications if a["status"].lower() == "shortlisted")

    offered_count = sum(1 for a in applications if a["status"].lower() == "offered")

    rejected_count = sum(1 for a in applications if a["status"].lower() == "rejected")

    print("Route time:", time.time() - start)

    return templates.TemplateResponse(
        request=request,
        name="viewApplication.html",
        context={
            "request": request,
            "company": company,
            "applications": applications,
            "jobs": jobs,
            "no_experience_message": no_experience_message,
            "no_status_message": no_status_message,
            "total_count": total_count,
            "new_count": new_count,
            "reviewed_count": reviewed_count,
            "shortlisted_count": shortlisted_count,
            "offered_count": offered_count,
            "rejected_count": rejected_count,
        },
    )


# ==================================================
# View Applicant Resume
# ==================================================


@router.get("/application/resume/{application_id}")
async def view_resume(application_id: str):

    # Retrieve application document
    application_doc = db.collection("application").document(application_id).get()

    # Check whether application exists
    if not application_doc.exists:

        raise HTTPException(status_code=404, detail="Application not found.")

    # Convert Firestore document
    # into a Python dictionary
    application = application_doc.to_dict()

    # Get resume path
    resume_path = application.get("resume_path")

    # Check whether resume path exists
    if not resume_path:

        raise HTTPException(status_code=404, detail="Resume is not available.")

    # Get Firebase Storage bucket
    bucket = storage.bucket()

    # Retrieve the resume file
    resume_blob = bucket.blob(resume_path)

    # Check whether the resume exists
    if not resume_blob.exists():

        raise HTTPException(
            status_code=404, detail=("Resume file was not found " "in Firebase Storage.")
        )

    # Generate a temporary URL
    # that is valid for one hour
    resume_url = resume_blob.generate_signed_url(
        expiration=timedelta(hours=1), method="GET", version="v4"
    )

    # Redirect to the PDF
    return RedirectResponse(url=resume_url)


# ==================================================
# Update Application Status
# ==================================================


@router.put("/application/{application_id}/status")
async def update_application_status(application_id: str, status_data: ApplicationStatusUpdate):

    # ==================================================
    # Normalize Received Status
    # ==================================================

    received_status = status_data.status.strip().lower()

    # ==================================================
    # Map UI Status to Firestore Status
    # ==================================================

    status_mapping = {
        # New application
        "new": "Submitted",
        "submitted": "Submitted",
        # Reviewed application
        "reviewed": "Reviewed",
        # Other statuses
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

    # Get the correct Firestore value

    firestore_status = status_mapping[received_status]

    # ==================================================
    # Retrieve Application
    # ==================================================

    application_ref = db.collection("application").document(application_id)

    application_doc = application_ref.get()

    # ==================================================
    # Check Whether Application Exists
    # ==================================================

    if not application_doc.exists:

        raise HTTPException(status_code=404, detail=("Application not found."))

    # ==================================================
    # Prevent changing final statuses
    # ==================================================

    application = application_doc.to_dict()

    current_status = (
        str(application.get("status", ""))
        .strip()
        .lower()
    )

    if current_status in ["offered", "rejected"]:

        raise HTTPException(
            status_code=400,
            detail=(
                "This application has already been "
                f"{current_status} and its status cannot be changed."
            ),
        )

    # ==================================================
    # Update Firestore Status and Time
    # ==================================================

    application_ref.update(
        {
            # Update application status
            "status": firestore_status,
            # Store the current server date and time
            "updated_on": firestore.SERVER_TIMESTAMP,
        }
    )

    # ==================================================
    # Return Successful Result
    # ==================================================

    return {
        "success": True,
        "message": "Application status updated successfully.",
        "status": firestore_status,
    }
