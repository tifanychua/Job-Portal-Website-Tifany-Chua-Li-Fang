from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from google.cloud.firestore_v1.base_query import FieldFilter

from .database import db

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")

templates = Jinja2Templates(directory=UI_DIR)


# =====================================================
# Notification type -> icon (Font Awesome, already loaded site-wide)
# =====================================================

TYPE_ICONS = {
    "application": "fa-file-circle-check",
    "interview": "fa-calendar-check",
    "message": "fa-comment-dots",
    "job_alert": "fa-briefcase",
    "system": "fa-bell",
}

TYPE_COLORS = {
    "application": "notif-blue",
    "interview": "notif-green",
    "message": "notif-purple",
    "job_alert": "notif-orange",
    "system": "notif-gray",
}


# =====================================================
# Helpers
# =====================================================


def _get_current_user(request: Request):
    """Works for both job seekers and employers — notifications page
    is shared between both account types."""

    user_type = request.session.get("user_type")

    if user_type == "job_seeker":
        uid = request.session.get("applicant_id")
        collection = "job_seeker"

    elif user_type == "employer":
        uid = request.session.get("company_id")
        collection = "company"

    else:
        return None, None, None

    if not uid:
        return None, None, None

    doc = db.collection(collection).document(uid).get()

    user = doc.to_dict() if doc.exists else None

    return uid, user_type, user


def _load_notifications(user_id):
    """Shared by both the job-seeker and employer notification pages —
    loads + normalizes every notification document for this user_id."""

    docs = (
        db.collection("notification")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .stream()
    )

    notifications = []

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        data.setdefault("is_read", False)
        data.setdefault("type", "system")
        data.setdefault("title", "Notification")
        data.setdefault("message", "")
        data.setdefault("link", "")

        data["icon"] = TYPE_ICONS.get(data["type"], "fa-bell")
        data["color_class"] = TYPE_COLORS.get(data["type"], "notif-gray")

        created_at = data.get("created_at")

        data["time_display"] = _format_relative(created_at)
        data["sort_key"] = created_at.isoformat() if hasattr(created_at, "isoformat") else ""

        notifications.append(data)

    notifications.sort(key=lambda n: n.get("sort_key", ""), reverse=True)

    return notifications


def _format_relative(ts):

    if not ts:
        return ""

    if hasattr(ts, "tzinfo") and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    diff = now - ts

    seconds = diff.total_seconds()

    if seconds < 60:
        return "Just now"

    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"

    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"

    if seconds < 604800:
        return f"{int(seconds // 86400)}d ago"

    return ts.strftime("%d %b %Y")




def get_unread_notifications_count(request):
    user_id, user_type, _ = _get_current_user(request)
    if not user_id:
        return 0
    docs = (
        db.collection("notification")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .where(filter=FieldFilter("is_read", "==", False))
        .stream()
    )
    return sum(1 for _ in docs)

# =====================================================
# PAGE — Notifications list
# =====================================================


@router.get("/notifications", name="notifications_page")
def notifications_page(request: Request):

    user_id, user_type, user = _get_current_user(request)

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    # Employers get their own dashboard-styled notifications page
    if user_type == "employer":
        return RedirectResponse("/employer-notifications", status_code=303)

    notifications = _load_notifications(user_id)

    unread_count = sum(1 for n in notifications if not n["is_read"])

    return templates.TemplateResponse(
        request=request,
        name="notifications.html",
        context={
            "user": user,
            "active_page": "notifications",
            "notifications": notifications,
            "total_notifications": len(notifications),
            "unread_count": unread_count,
            "unread_notifications_count": unread_count,
        },
    )


# =====================================================
# PAGE — Employer notifications list (dashboard-styled)
# =====================================================


@router.get("/employer-notifications", name="employer_notifications_page")
def employer_notifications_page(request: Request):

    if request.session.get("user_type") != "employer":
        return RedirectResponse("/login", status_code=303)

    user_id, user_type, user = _get_current_user(request)

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    notifications = _load_notifications(user_id)

    unread_count = sum(1 for n in notifications if not n["is_read"])

    return templates.TemplateResponse(
        request=request,
        name="employer_notification.html",
        context={
            "user": user,
            "company": user,
            "active_page": "notifications",
            "notifications": notifications,
            "total_notifications": len(notifications),
            "unread_count": unread_count,
            "unread_notifications_count": unread_count,
        },
    )


# =====================================================
# API — Mark single notification as read / unread
# =====================================================


@router.post("/api/notifications/{notification_id}/read", name="mark_notification_read")
def mark_notification_read(request: Request, notification_id: str):

    user_id, _, _ = _get_current_user(request)

    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})

    ref = db.collection("notification").document(notification_id)

    doc = ref.get()

    if not doc.exists or doc.to_dict().get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    ref.update({"is_read": True})

    return JSONResponse(content={"success": True})


@router.post("/api/notifications/{notification_id}/unread", name="mark_notification_unread")
def mark_notification_unread(request: Request, notification_id: str):

    user_id, _, _ = _get_current_user(request)

    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})

    ref = db.collection("notification").document(notification_id)

    doc = ref.get()

    if not doc.exists or doc.to_dict().get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    ref.update({"is_read": False})

    return JSONResponse(content={"success": True})


# =====================================================
# API — Mark all as read
# =====================================================


@router.post("/api/notifications/mark-all-read", name="mark_all_notifications_read")
def mark_all_notifications_read(request: Request):

    user_id, _, _ = _get_current_user(request)

    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})

    docs = (
        db.collection("notification")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .where(filter=FieldFilter("is_read", "==", False))
        .stream()
    )

    batch = db.batch()

    count = 0

    for doc in docs:

        batch.update(doc.reference, {"is_read": True})

        count += 1

    if count:
        batch.commit()

    return JSONResponse(content={"success": True, "updated": count})


# =====================================================
# API — Delete a notification
# =====================================================


@router.delete("/api/notifications/{notification_id}", name="delete_notification")
def delete_notification(request: Request, notification_id: str):

    user_id, _, _ = _get_current_user(request)

    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})

    ref = db.collection("notification").document(notification_id)

    doc = ref.get()

    if not doc.exists or doc.to_dict().get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")

    ref.delete()

    return JSONResponse(content={"success": True})
