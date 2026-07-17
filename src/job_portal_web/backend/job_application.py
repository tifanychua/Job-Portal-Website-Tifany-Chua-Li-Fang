from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from google.cloud.firestore_v1.base_query import FieldFilter
from database import db, bucket
from job_information import _find_company
from job_apply import UI_DIR, _get_current_applicant, _get_screening_questions

router = APIRouter()

templates = Jinja2Templates(directory=UI_DIR)

# Order controls how tabs are displayed; label/color drive the badge styling.
STATUS_META = {
    "Submitted": {"label": "Submitted", "color": "blue"},
    "Cancelled": {"label": "Cancelled", "color": "grey"},
    "Shortlisted": {"label": "Shortlisted", "color": "orange"},
    "Rejected": {"label": "Rejected", "color": "red"},
    "Offered": {"label": "Offered", "color": "green"},
    "Reviewed": {"label": "Reviewed", "color": "yellow"},
}


FILTER_TABS = ["all", "submitted", "reviewed", "shortlisted", "offered", "rejected", "cancelled"]


def _format_timestamp(ts):

    if not ts:
        return "—"

    if hasattr(ts, "strftime"):
        return ts.strftime("%B %d, %Y")

    return str(ts)


def _get_job_summary(job_id):
    """Lightweight job lookup for the applications list — just enough to
    render a card, not the full detail-page payload."""

    if not job_id:
        return None

    job_doc = db.collection("job_list").document(job_id).get()

    if not job_doc.exists:
        return None

    job = job_doc.to_dict()
    job["id"] = job_id
    job.setdefault("job_title", "Untitled Position")
    job.setdefault("location", "Not specified")
    job.setdefault("employment_type", "Not specified")
    job.setdefault("category", "General")

    company = _find_company(job.get("company_id"))

    if company:
        job["companyName"] = company.get("companyName", "Unknown")
        job["company_verified"] = company.get("verified", False)
    else:
        job["companyName"] = "Unknown"
        job["company_verified"] = False

    return job


def _build_answer_summary(application, questions):

    answers = application.get("answers", {}) or {}

    summary = []

    for question in questions:
        value = answers.get(question["id"])
        if value:
            summary.append({"label": question["label"], "value": value})

    return summary


def _get_resume_url(path):

    if not path:
        return None

    blob = bucket.blob(path)

    url = blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")

    return url


@router.get("/application", name="my_applications")
def my_applications(request: Request, status: str = "all"):
    applicant_id, applicant = _get_current_applicant(request)

    if not applicant_id:
        #     return RedirectResponse(url="/login?next=/application", status_code=302)
        applicant_id = "J000001"

    docs = (
    db.collection("application")
    .where(
        filter=FieldFilter(
            "job_seeker_id",
            "==",
            applicant_id
        )
    )
    .stream()
)

    application = []
    counts = {key: 0 for key in STATUS_META}

    for doc in docs:

        data = doc.to_dict()
        data["id"] = doc.id

        app_status = data.get("status", "draft")
        counts[app_status] = counts.get(app_status, 0) + 1

        job = _get_job_summary(data.get("job_id"))

        if not job:
            # Job was removed/unavailable — skip rather than show a broken card
            continue

        questions = _get_screening_questions(job)

        application.append(
            {
                "id": data["id"],
                "job": job,
                "status": app_status,
                "status_label": STATUS_META.get(app_status, {}).get("label", app_status.title()),
                "status_color": STATUS_META.get(app_status, {}).get("color", "muted"),
                "resume_name": data.get("resume_filename"),
                "cover_letter": data.get("cover_letter", ""),
                "answer_summary": _build_answer_summary(data, questions),
                "applied_on": _format_timestamp(data.get("created_at")),
                "updated_on": _format_timestamp(data.get("updated_on")),
            }
        )

    # Most recently touched application first
    application.sort(key=lambda a: a["updated_on"], reverse=True)

    if status != "all":
        application = [a for a in application if a["status"] == status]

    total_count = sum(counts.values())

    return templates.TemplateResponse(
        request=request,
        name="job_application.html",
        context={
            "request": request,
            "application": application,
            "counts": counts,
            "total_count": total_count,
            "active_filter": status,
            "filter_tabs": FILTER_TABS,
            "status_meta": STATUS_META,
        },
    )


@router.get("/application/{application_id}", name="my_applications_detail")
def my_applications_detail(request: Request, application_id: str):
    doc = db.collection("application").document(application_id).get()

    if not doc.exists:
        return RedirectResponse("/application", status_code=302)

    data = doc.to_dict()

    data["id"] = doc.id

    job = _get_job_summary(data.get("job_id"))

    questions = _get_screening_questions(job)
    current_status = data.get("status", "Submitted")

    application = {
        "id": data["id"],
        "job": job,
        "status": current_status,
        "status_label": STATUS_META.get(current_status, {}).get("label", current_status.title()),
        "status_color": STATUS_META.get(current_status, {}).get("color", "muted"),
        "resume_name": data.get("resume_filename"),
        "resume_url": _get_resume_url(data.get("resume_path")),
        "cover_letter": data.get("cover_letter", ""),
        "answer_summary": _build_answer_summary(data, questions),
        "applied_on": _format_timestamp(data.get("created_at")),
    }

    return templates.TemplateResponse(
        request=request,
        name="job_application_detail.html",
        context={"request": request, "application": application},
    )


@router.post("/application/{application_id}/cancel", name="withdraw_application")
def withdraw_application(application_id: str):

    doc_ref = db.collection("application").document(application_id)

    doc = doc_ref.get()

    if not doc.exists:

        return RedirectResponse("/application", status_code=302)

    data = doc.to_dict()

    if data.get("status") == "Submitted":

        doc_ref.update({"status": "Cancelled"})

    return RedirectResponse(f"/application/{application_id}", status_code=302)
