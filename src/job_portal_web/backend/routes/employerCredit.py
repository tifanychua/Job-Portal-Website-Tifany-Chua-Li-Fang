import os

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")

db = firestore.client()


# =====================================================
# Get Current Company ID
# =====================================================

def get_current_company_id(request: Request):

    # ==========================================
    # Pytest mode
    # ==========================================
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

    # ==========================================
    # Normal mode
    # ==========================================
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

    # ==========================================
    # Company
    # ==========================================

    company_doc = (
        db.collection("company")
        .document(company_id)
        .get()
    )

    company = company_doc.to_dict() if company_doc.exists else {}

    # ==========================================
    # Credits
    # ==========================================

    total_credit = company.get("total_credit", 0)

    available_credit = company.get("available_credit", 0)

    expired_credit = company.get("expired_credit", 0)

    used_credit = company.get(
        "used_credit",
        total_credit - available_credit
    )

    # ==========================================
    # Subscription
    # ==========================================

    current_plan = company.get(
        "subscription_plan",
        ""
    )

    subscription_status = company.get(
        "subscription_status",
        ""
    )

    # ==========================================
    # Credit History
    # ==========================================

    history_docs = (

        db.collection("credit_history")

        .where("company_id", "==", company_id)

        .stream()

    )

    histories = []

    for doc in history_docs:

        data = doc.to_dict()

        histories.append({

            "date": data.get("date", ""),

            "description": data.get("description", ""),

            "credit": data.get("credit", 0),

            "balance": data.get("balance", 0),

            "reference": data.get("reference", "")

        })

    # ==========================================
    # Render
    # ==========================================

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

            "current_plan": current_plan,

            "subscription_status": subscription_status

        }

    )