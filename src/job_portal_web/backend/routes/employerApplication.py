from pathlib import Path

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from firebase_admin import storage
from firebase_admin import firestore
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from pydantic import BaseModel
from src.job_portal_web.backend.helper import get_company
from src.job_portal_web.backend.database import db


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

BASE_DIR = Path(
    __file__
).resolve().parent.parent.parent


templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "ui"
    )
)


# ==================================================
# View All Applications
# ==================================================

@router.get(
    "/applications",
    response_class=HTMLResponse
)
async def view_applications(
    request: Request
):

    # Temporary company ID
    # Later retrieve from the employer login session

    company_id = "C000001"

    company = get_company()

    # ==================================================
    # Retrieve Jobs Posted by Current Company
    # ==================================================

    jobs = []

    job_docs = (
        db.collection("job_list")
        .where("company_id", "==", company_id)
        .stream()
    )

    for job_doc in job_docs:

        job = job_doc.to_dict()

        # Get and normalize the job status
        job_status = str(
            job.get("status", "")
        ).strip().lower()

        # Do not display deleted jobs
        if job_status == "deleted":
            continue

        # Add non-deleted job to the dropdown
        jobs.append({
            "job_id": job_doc.id,

            "job_title": job.get(
                "job_title",
                "Untitled Job"
            )
        })


    # Store applications that belong
    # to the current employer

    applications = []


    # ==================================================
    # Retrieve All Application Documents
    # ==================================================

    application_docs = (
        db.collection(
            "application"
        )
        .stream()
    )


    for application_doc in application_docs:

        # Convert Firestore document
        # into a Python dictionary

        application = (
            application_doc.to_dict()
        )


        # ==================================================
        # Do Not Display Cancelled Applications
        # ==================================================

        application_status = (
            application.get(
                "status",
                ""
            )
            .strip()
            .lower()
        )


        if application_status == "cancelled":

            continue


        # ==================================================
        # Get Job ID from Application
        # ==================================================

        job_id = application.get(
            "job_id"
        )


        # Skip application if job_id
        # does not exist

        if not job_id:

            continue


        # ==================================================
        # Retrieve Related Job
        # ==================================================

        job_doc = (
            db.collection(
                "job_list"
            )
            .document(
                job_id
            )
            .get()
        )


        # Skip application if its
        # related job cannot be found

        if not job_doc.exists:

            continue


        # Convert job document
        # into a Python dictionary

        job = job_doc.to_dict()


        # ==================================================
        # Check Company
        # ==================================================

        job_company_id = (
            job.get(
                "company_id"
            )
        )


        # Do not display applications
        # belonging to another company

        if job_company_id != company_id:

            continue


        # ==================================================
        # Add Application Information
        # ==================================================

        # Use the actual Firestore document ID

        application[
            "application_id"
        ] = application_doc.id


        # Store normalized status
        # Example: "new" becomes "New"

        application[
            "status"
        ] = application_status.title()


        # ==================================================
        # Add Job Information
        # ==================================================

        application[
            "job_title"
        ] = (

            job.get(
                "job_title"
            )

            or

            "Unknown Position"

        )


        # ==================================================
        # Default Applicant Information
        # ==================================================

        application[
            "applicant_name"
        ] = "Unknown Applicant"


        application[
            "applicant_email"
        ] = "No email provided"


        application[
            "experience"
        ] = "Not provided"


        application[
            "skills"
        ] = []


        # ==================================================
        # Get Job Seeker ID
        # ==================================================

        job_seeker_id = (
            application.get(
                "job_seeker_id"
            )
        )


        # ==================================================
        # Retrieve Job Seeker Information
        # ==================================================

        if job_seeker_id:

            job_seeker_doc = (

                db.collection(
                    "job_seeker"
                )

                .document(
                    job_seeker_id
                )

                .get()

            )


            # Check whether the
            # job seeker exists

            if job_seeker_doc.exists:

                job_seeker = (

                    job_seeker_doc
                    .to_dict()

                )


                # Applicant name

                application[
                    "applicant_name"
                ] = (

                    job_seeker.get(
                        "name"
                    )

                    or

                    "Unknown Applicant"

                )


                # Applicant email

                application[
                    "applicant_email"
                ] = (

                    job_seeker.get(
                        "email"
                    )

                    or

                    "No email provided"

                )


                # Applicant experience

                application[
                    "experience"
                ] = (

                    job_seeker.get(
                        "experience"
                    )

                    or

                    "Not provided"

                )


                # Applicant skills

                application[
                    "skills"
                ] = (

                    job_seeker.get(
                        "skills"
                    )

                    or

                    []

                )


        # ==================================================
        # Add Completed Application
        # ==================================================

        applications.append(
            application
        )


    # ==================================================
    # Calculate Application Statistics
    # ==================================================

    # Total displayed applications
    total_count = len(applications)


    # Count New applications
    new_count = sum(
        1
        for application in applications
        if str(
            application.get("status", "")
        ).strip().lower() == "submitted"
    )

    # Count Reviewed applications
    reviewed_count = sum(
        1
        for application in applications
        if str(
            application.get("status", "")
        ).strip().lower() == "reviewed"
    )


    # Count Shortlisted applications
    shortlisted_count = sum(
        1
        for application in applications
        if str(
            application.get("status", "")
        ).strip().lower() == "shortlisted"
    )


    # Count Offered applications
    offered_count = sum(
        1
        for application in applications
        if str(
            application.get("status", "")
        ).strip().lower() == "offered"
    )


    # Count Rejected applications
    rejected_count = sum(
        1
        for application in applications
        if str(
            application.get("status", "")
        ).strip().lower() == "rejected"
    )


    # ==================================================
    # Display Application Page
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
            "rejected_count": rejected_count
        }
    )

# ==================================================
# View Applicant Resume
# ==================================================

@router.get(
    "/application/resume/{application_id}"
)
async def view_resume(
    application_id: str
):

    # Retrieve application document
    application_doc = (
        db.collection("application")
        .document(application_id)
        .get()
    )


    # Check whether application exists
    if not application_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )


    # Convert Firestore document
    # into a Python dictionary
    application = (
        application_doc.to_dict()
    )


    # Get resume path
    resume_path = (
        application.get(
            "resume_path"
        )
    )


    # Check whether resume path exists
    if not resume_path:

        raise HTTPException(
            status_code=404,
            detail="Resume is not available."
        )


    # Get Firebase Storage bucket
    bucket = storage.bucket()


    # Retrieve the resume file
    resume_blob = bucket.blob(
        resume_path
    )


    # Check whether the resume exists
    if not resume_blob.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Resume file was not found "
                "in Firebase Storage."
            )
        )


    # Generate a temporary URL
    # that is valid for one hour
    resume_url = (
        resume_blob.generate_signed_url(
            expiration=timedelta(
                hours=1
            ),
            method="GET",
            version="v4"
        )
    )


    # Redirect to the PDF
    return RedirectResponse(
        url=resume_url
    )

# ==================================================
# Update Application Status
# ==================================================

@router.put(
    "/application/{application_id}/status"
)
async def update_application_status(

    application_id: str,

    status_data: ApplicationStatusUpdate

):

    # ==================================================
    # Normalize Received Status
    # ==================================================

    received_status = (

        status_data.status
        .strip()
        .lower()

    )


    # ==================================================
    # Map UI Status to Firestore Status
    # ==================================================

    status_mapping = {
        # New application

        "new":
            "Submitted",

        "submitted":
            "Submitted",


        # Reviewed application

        "reviewed":
            "Reviewed",


        # Other statuses

        "shortlisted":
            "Shortlisted",

        "offered":
            "Offered",

        "rejected":
            "Rejected"

    }


    # ==================================================
    # Validate Status
    # ==================================================

    if received_status not in status_mapping:

        raise HTTPException(

            status_code=400,

            detail=(
                "Invalid application status: "
                +
                status_data.status
            )

        )


    # Get the correct Firestore value

    firestore_status = (

        status_mapping[
            received_status
        ]

    )


    # ==================================================
    # Retrieve Application
    # ==================================================

    application_ref = (

        db.collection(
            "application"
        )

        .document(
            application_id
        )

    )


    application_doc = (

        application_ref.get()

    )


    # ==================================================
    # Check Whether Application Exists
    # ==================================================

    if not application_doc.exists:

        raise HTTPException(

            status_code=404,

            detail=(
                "Application not found."
            )

        )


    # ==================================================
    # Update Firestore Status and Time
    # ==================================================

    application_ref.update({

        # Update application status

        "status":
            firestore_status,


        # Store the current server date and time

        "updated_on":
            firestore.SERVER_TIMESTAMP

    })


    # ==================================================
    # Return Successful Result
    # ==================================================

    return {

        "success":
            True,

        "message":
            "Application status updated successfully.",

        "status":
            firestore_status

    }