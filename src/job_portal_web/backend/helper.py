from fastapi import Request

from .database import db


def parse_salary(value):

    if value in (None, ""):
        return 0

    if isinstance(value, str):
        value = value.replace(",", "").strip()

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def get_company(request: Request):

    company_id = request.session.get("company_id")

    if not company_id:
        return None

    doc = db.collection("company").document(company_id).get()

    if not doc.exists:
        return None

    company = doc.to_dict()

    # Add the Firebase UID as companyId
    company["companyId"] = company_id

    return company


def get_current_user(request: Request):

    if request.session.get("user_type") != "job_seeker":
        return None

    uid = request.session.get("applicant_id")

    if not uid:
        return None

    doc = db.collection("job_seeker").document(uid).get()

    if doc.exists:
        return doc.to_dict()

    return None
