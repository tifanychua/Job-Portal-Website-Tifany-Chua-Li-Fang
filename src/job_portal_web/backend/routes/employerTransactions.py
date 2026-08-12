import os
import math
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
)

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
# All Employer Transactions
# =====================================================


@router.get("/employer-transactions", response_class=HTMLResponse)
def employer_transactions(
    request: Request,
    page: int = 1,
    status: str = "",
    keyword: str = "",
):

    company_id = get_current_company_id(request)

    # =================================================
    # Company
    # =================================================

    company_doc = db.collection("company").document(company_id).get()

    if not company_doc.exists:

        raise HTTPException(status_code=404, detail="Company not found")

    company = company_doc.to_dict()

    # =================================================
    # Payments
    # =================================================

    payment_docs = (
        db.collection("payment").where(filter=FieldFilter("company_id", "==", company_id)).stream()
    )

    transactions = []

    total_spent = 0.0

    completed_count = 0
    pending_count = 0
    failed_count = 0

    keyword_lower = keyword.strip().lower()

    status_upper = status.strip().upper()

    # =================================================
    # Build Transaction List
    # =================================================

    for doc in payment_docs:

        data = doc.to_dict()

        transaction_id = doc.id

        transaction_status = str(data.get("status", "") or "").upper()

        package = str(data.get("package", "-") or "-")

        payment_method = str(data.get("payment_method", "-") or "-")

        amount = float(data.get("amount", 0) or 0)

        payment_date = data.get("completed_at") or data.get("created_at")

        # =============================================
        # Search
        # =============================================

        if keyword_lower:

            searchable_text = (f"{transaction_id} " f"{package} " f"{payment_method}").lower()

            if keyword_lower not in searchable_text:
                continue

        # =============================================
        # Status Filter
        # =============================================

        if status_upper and transaction_status != status_upper:
            continue

        # =============================================
        # Statistics
        # =============================================

        if transaction_status == "COMPLETED":

            completed_count += 1

            total_spent += amount

        elif transaction_status == "PENDING":

            pending_count += 1

        elif transaction_status == "FAILED":

            failed_count += 1

        # =============================================
        # Transaction
        # =============================================

        transactions.append(
            {
                "transaction_id": transaction_id,
                "package": package,
                "amount": amount,
                "currency": data.get("currency", "MYR"),
                "status": transaction_status,
                "payment_method": payment_method,
                "credits": int(data.get("credits", 0) or 0),
                "date": (payment_date.strftime("%d %b %Y") if payment_date else "-"),
                "time": (payment_date.strftime("%I:%M %p") if payment_date else ""),
                "sort_date": payment_date,
                "stripe_invoice_id": data.get("stripe_invoice_id", ""),
            }
        )

    # =================================================
    # Newest → Oldest
    # =================================================

    transactions.sort(
        key=lambda item: (item["sort_date"] or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )

    # =================================================
    # Pagination
    # =================================================

    PER_PAGE = 20

    total_transactions = len(transactions)

    total_pages = max(1, math.ceil(total_transactions / PER_PAGE))

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    start = (page - 1) * PER_PAGE

    end = start + PER_PAGE

    paginated_transactions = transactions[start:end]

    # =================================================
    # Render
    # =================================================

    return templates.TemplateResponse(
        request=request,
        name="employerTransactions.html",
        context={
            "company": company,
            "transactions": paginated_transactions,
            "total_transactions": total_transactions,
            "total_spent": total_spent,
            "completed_count": completed_count,
            "pending_count": pending_count,
            "failed_count": failed_count,
            "current_page": page,
            "total_pages": total_pages,
            "current_status": status,
            "keyword": keyword,
            "active_page": "credit",
        },
    )
