from fastapi import Request

from .database import db


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

# ==========================================
# Get Unread Notification Count
# ==========================================

def get_unread_notification_count(request: Request):

    company_id = request.session.get("company_id")

    if not company_id:
        return 0

    docs = (
        db.collection("notification")
        .where("company_id", "==", company_id)
        .where("is_read", "==", False)
        .stream()
    )

    return sum(1 for _ in docs)

def get_notifications(request: Request):

    company_id = request.session.get("company_id")

    if not company_id:
        return []

    docs = (
        db.collection("notification")
        .where("company_id", "==", company_id)
        .order_by("created_at", direction="DESCENDING")
        .stream()
    )

    notifications = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        notifications.append(data)

    return notifications


def mark_notification_read(notification_id: str):

    db.collection("notification").document(notification_id).update({
        "is_read": True
    })


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
