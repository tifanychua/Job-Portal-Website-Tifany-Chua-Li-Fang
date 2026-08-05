from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from firebase_admin import firestore

from ..helper import (
    get_company,
    get_unread_notification_count
)
from ..database import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "ui")
)


# ==========================================
# Notification Page
# ==========================================

@router.get("/notifications", response_class=HTMLResponse)
async def notification_page(request: Request):

    company = get_company(request)

    if company is None:

        return RedirectResponse("/login", status_code=303)

    unread_count = get_unread_notification_count(request)

    company_id = request.session.get("company_id")

    notification_docs = (

        db.collection("notification")

        .where("company_id", "==", company_id)

        .order_by("created_at", direction=firestore.Query.DESCENDING)

        .stream()

    )

    notifications = []

    unread_count = 0

    for doc in notification_docs:

        item = doc.to_dict()

        item["notification_id"] = doc.id

        if not item.get("is_read", False):

            unread_count += 1

        notifications.append(item)

    return templates.TemplateResponse(

        request=request,

        name="notification.html",

        context={

            "request": request,

            "company": company,

            "notifications": notifications,

            "unread_count": unread_count

        }

    )


# ==========================================
# Mark One Notification Read
# ==========================================

@router.get("/notification/read/{notification_id}")
async def mark_notification_read(

    request: Request,

    notification_id: str

):

    db.collection("notification").document(notification_id).update({

        "is_read": True

    })

    return RedirectResponse(

        "/notifications",

        status_code=303

    )


# ==========================================
# Mark All Read
# ==========================================

@router.get("/notification/read-all")
async def mark_all_read(request: Request):

    company_id = request.session.get("company_id")

    docs = (

        db.collection("notification")

        .where("company_id", "==", company_id)

        .where("is_read", "==", False)

        .stream()

    )

    for doc in docs:

        db.collection("notification").document(doc.id).update({

            "is_read": True

        })

    return RedirectResponse(

        "/notifications",

        status_code=303

    )


# ==========================================
# Delete Notification
# ==========================================

@router.get("/notification/delete/{notification_id}")
async def delete_notification(

    request: Request,

    notification_id: str

):

    db.collection("notification").document(

        notification_id

    ).delete()

    return RedirectResponse(

        "/notifications",

        status_code=303

    )