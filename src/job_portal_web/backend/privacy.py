import os
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from .database import db
from .notifications import get_unread_notifications_count

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")

templates = Jinja2Templates(directory=UI_DIR)


# =====================================================
# PAGE — Privacy settings
#
# Lists every employer that currently has access to this job seeker's
# personal information -- i.e. every employer whose job posting this job
# seeker has submitted an application to (see applicant.get_application,
# which enforces that only those employers may fetch the applicant's
# details).
# =====================================================


@router.get("/privacy-settings", name="privacy_settings_page")
def privacy_settings_page(request: Request):

    if request.session.get("user_type") != "job_seeker":
        return RedirectResponse(url="/login?next=/privacy-settings", status_code=303)

    job_seeker_id = request.session.get("applicant_id")

    if not job_seeker_id:
        return RedirectResponse(url="/login?next=/privacy-settings", status_code=303)

    user_doc = db.collection("job_seeker").document(job_seeker_id).get()

    user = user_doc.to_dict() if user_doc.exists else None

    application_docs = (
        db.collection("application")
        .where(filter=FieldFilter("job_seeker_id", "==", job_seeker_id))
        .stream()
    )

    employers_by_company: dict[str, dict[str, Any]] = {}
    for doc in application_docs:
        data = doc.to_dict()

        job_id = data.get("job_id")

        if not job_id:
            continue

        job_doc = db.collection("job_list").document(job_id).get()

        if not job_doc.exists:
            continue

        job = job_doc.to_dict()

        company_id = job.get("company_id")

        if not company_id:
            continue

        entry = employers_by_company.get(company_id)

        if entry is None:
            company_doc = db.collection("company").document(company_id).get()

            company = company_doc.to_dict() if company_doc.exists else {}

            entry = employers_by_company[company_id] = {
                "company_id": company_id,
                "companyName": company.get("companyName") or "Unknown employer",
                "logo": company.get("logo"),
                "verified": company.get("verified", False),
                "job_titles": [],
                "application_count": 0,
            }

        job_title = job.get("job_title") or "Untitled position"

        if job_title not in entry["job_titles"]:
            entry["job_titles"].append(job_title)

        entry["application_count"] += 1

    employers = sorted(employers_by_company.values(), key=lambda e: e["companyName"].lower())

    return templates.TemplateResponse(
        request=request,
        name="privacy_settings.html",
        context={
            "user": user,
            "active_page": "privacy_settings",
            "employers": employers,
            "unread_notifications_count": get_unread_notifications_count(request),
        },
    )
