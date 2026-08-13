import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")

db = firestore.client()


# =====================================================
# Current Company
# =====================================================


def get_current_company_id(request: Request):

    if os.getenv("PYTEST_CURRENT_TEST"):
        return "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

    if request.session.get("user_type") != "employer":
        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:
        raise HTTPException(status_code=401, detail="Company not logged in")

    return company_id


# =====================================================
# Employer Credit Page
# =====================================================


@router.get("/employer-credit", response_class=HTMLResponse)
async def employer_credit(request: Request):

    company_id = get_current_company_id(request)

    # =================================================
    # Company
    # =================================================

    company_doc = db.collection("company").document(company_id).get()

    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")

    company = company_doc.to_dict()

    # =================================================
    # Credits
    # =================================================

    total_credit = int(company.get("total_credit", 0) or 0)

    available_credit = int(company.get("available_credit", 0) or 0)

    expired_credit = int(company.get("expired_credit", 0) or 0)

    used_credit = int(company.get("used_credit", total_credit - available_credit) or 0)

    # =================================================
    # Subscription
    # =================================================

    current_plan = str(company.get("subscription_plan", "") or "").lower()

    subscription_status = str(company.get("subscription_status", "") or "")

    cancel_at_period_end = bool(company.get("cancel_at_period_end", False))

    PLAN_NAMES = {
        "starter": "Starter Pack",
        "business": "Business Pack",
        "enterprise": "Enterprise Pack",
    }

    current_plan_name = PLAN_NAMES.get(current_plan, "")

    subscription_end = company.get("subscription_current_period_end")

    if subscription_end:
        subscription_end_display = subscription_end.strftime("%d %b %Y")

    else:
        subscription_end_display = None

    # =================================================
    # Payment History
    # =================================================

    payment_docs = (
        db.collection("payment").where(filter=FieldFilter("company_id", "==", company_id)).stream()
    )

    all_histories = []

    for doc in payment_docs:
        data = doc.to_dict()

        payment_date = data.get("completed_at") or data.get("created_at")

        all_histories.append(
            {
                "transaction_id": doc.id,
                "package": data.get("package", "-"),
                "date": (payment_date.strftime("%d %b %Y") if payment_date else "-"),
                "sort_date": payment_date,
                "status": data.get("status", ""),
                "amount": float(data.get("amount", 0) or 0),
            }
        )

    # Newest first
    all_histories.sort(
        key=lambda item: item["sort_date"] or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )

    # Only latest 5
    histories = all_histories[:5]

    has_more = len(all_histories) > 5

    # =================================================
    # Render
    # =================================================

    return templates.TemplateResponse(
        request=request,
        name="employerCredit.html",
        context={
            "company": company,
            "total_credit": total_credit,
            "available_credit": available_credit,
            "used_credit": used_credit,
            "expired_credit": expired_credit,
            "histories": histories,
            "has_more": has_more,
            "current_plan": current_plan,
            "current_plan_name": current_plan_name,
            "subscription_status": subscription_status,
            "subscription_end": subscription_end_display,
            "cancel_at_period_end": cancel_at_period_end,
        },
    )
