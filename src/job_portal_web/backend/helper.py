from .database import db
from fastapi import Request


def get_company(request: Request):

    company_id = request.session.get("company_id")
    print("company_id:", company_id)

    if not company_id:
        print("No company_id in session")
        return None

    doc = db.collection("company").document(company_id).get()

    print("exists:", doc.exists)

    if doc.exists:
        print(doc.to_dict())

    return doc.to_dict() if doc.exists else None


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
