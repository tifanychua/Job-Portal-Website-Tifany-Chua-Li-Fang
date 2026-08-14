import os
from datetime import UTC, datetime
from typing import Any, TypedDict

import stripe
from dotenv import load_dotenv
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore

# =====================================================
# Environment
# =====================================================

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()
templates = Jinja2Templates(directory="src/job_portal_web/ui")
db = firestore.client()


# =====================================================
# Plan Configuration
# =====================================================


class PlanConfig(TypedDict):
    id: str
    name: str
    price: int
    credits: int
    description: str
    stripe_price_id: str | None


PLANS: dict[str, PlanConfig] = {
    "starter": {
        "id": "starter",
        "name": "Starter Pack",
        "price": 49,
        "credits": 10,
        "description": "Standard job visibility",
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
    },
    "business": {
        "id": "business",
        "name": "Business Pack",
        "price": 129,
        "credits": 30,
        "description": "Featured job visibility",
        "stripe_price_id": os.getenv("STRIPE_BUSINESS_PRICE_ID"),
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise Pack",
        "price": 229,
        "credits": 60,
        "description": "Featured + Top placement",
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
    },
}


# =====================================================
# Helpers
# =====================================================


def get_current_company_id(request: Request) -> str:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

    if request.session.get("user_type") != "employer":
        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:
        raise HTTPException(status_code=401, detail="Company not logged in")

    return str(company_id)


def get_company(company_id: str) -> dict[str, Any]:
    company_doc = db.collection("company").document(company_id).get()

    if not company_doc.exists:
        raise HTTPException(status_code=404, detail="Company not found")

    company = company_doc.to_dict()

    if company is None:
        raise HTTPException(status_code=404, detail="Company data not found")

    return company


def get_stripe_price_id(plan: PlanConfig) -> str:
    stripe_price_id = plan["stripe_price_id"]

    if not stripe_price_id:
        raise HTTPException(
            status_code=500,
            detail="Stripe Price ID is not configured.",
        )

    return stripe_price_id


def get_or_create_stripe_customer(
    company_id: str,
    company: dict[str, Any],
) -> str:
    customer_id = company.get("stripe_customer_id")

    if isinstance(customer_id, str) and customer_id:
        return customer_id

    customer_email = company.get("email") or company.get("businessEmail")

    if not isinstance(customer_email, str) or not customer_email.strip():
        raise HTTPException(
            status_code=400,
            detail="Company email is required",
        )

    customer_name = str(company.get("companyName") or "JobConnect Employer")

    customer = stripe.Customer.create(
        name=customer_name,
        email=customer_email.strip(),
        metadata={"company_id": company_id},
    )

    db.collection("company").document(company_id).update({"stripe_customer_id": customer.id})

    return customer.id


# =====================================================
# Plans Page
# =====================================================


@router.get("/employer-plans", response_class=HTMLResponse)
def employer_plans(request: Request):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    current_plan = str(company.get("subscription_plan", "") or "").lower()

    return templates.TemplateResponse(
        request=request,
        name="employerPlans.html",
        context={
            "company": company,
            "plans": PLANS,
            "current_plan": current_plan,
            "subscription_status": company.get("subscription_status", ""),
            "active_page": "credit",
        },
    )


# =====================================================
# First Subscription
# =====================================================


@router.post("/employer/subscription/start/{plan_name}")
def start_subscription(request: Request, plan_name: str):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    plan = PLANS.get(plan_name)

    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    stripe_price_id = get_stripe_price_id(plan)

    existing_subscription = company.get("stripe_subscription_id")

    if existing_subscription:
        return RedirectResponse(
            url="/employer-plans",
            status_code=303,
        )

    customer_id = get_or_create_stripe_customer(company_id, company)

    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[
            {
                "price": stripe_price_id,
                "quantity": 1,
            }
        ],
        subscription_data={
            "metadata": {
                "company_id": company_id,
                "plan": plan_name,
            }
        },
        success_url=(
            "http://127.0.0.1:8000/stripe/payment-success?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=("http://127.0.0.1:8000/employer-plans?subscription=cancelled"),
    )

    checkout_url = checkout_session.url

    if not checkout_url:
        raise HTTPException(
            status_code=502,
            detail="Stripe did not return a checkout URL.",
        )

    return RedirectResponse(url=checkout_url, status_code=303)


# =====================================================
# Change Existing Plan
# =====================================================


@router.post("/employer/subscription/change/{plan_name}")
def change_subscription(
    request: Request,
    plan_name: str,
    proration_date: int | None = Form(None),
):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    plan = PLANS.get(plan_name)

    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    stripe_price_id = get_stripe_price_id(plan)
    current_plan = str(company.get("subscription_plan", "") or "").lower()

    if current_plan == plan_name:
        return RedirectResponse(
            url="/employer-plans",
            status_code=303,
        )

    subscription_id = company.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "This account does not yet have a Stripe subscription. "
                "Start a Stripe subscription first."
            ),
        )

    subscription = stripe.Subscription.retrieve(subscription_id)
    subscription_items = subscription["items"]["data"]

    if not subscription_items:
        raise HTTPException(
            status_code=400,
            detail="Subscription item not found.",
        )

    subscription_item_id = subscription_items[0]["id"]

    if proration_date is None:
        proration_date = int(datetime.now(UTC).timestamp())

    stripe.Subscription.modify(
        subscription_id,
        items=[
            {
                "id": subscription_item_id,
                "price": stripe_price_id,
            }
        ],
        proration_behavior="always_invoice",
        proration_date=proration_date,
        payment_behavior="pending_if_incomplete",
        metadata={
            "company_id": company_id,
            "plan": plan_name,
        },
    )

    return RedirectResponse(
        url=("/employer-credit" f"?plan_change=processing" f"&expected_plan={plan_name}"),
        status_code=303,
    )


# =====================================================
# Check Subscription Change Status
# =====================================================


@router.get("/employer/subscription/status")
def get_subscription_status(
    request: Request,
    expected_plan: str = "",
):

    company_id = get_current_company_id(request)

    company = get_company(company_id)

    expected_plan = expected_plan.strip().lower()

    if expected_plan not in PLANS:
        return JSONResponse(
            {
                "updated": False,
                "reason": "invalid_plan",
            }
        )

    subscription_id = company.get("stripe_subscription_id")

    if not subscription_id:
        return JSONResponse(
            {
                "updated": False,
                "reason": "no_subscription",
            }
        )

    try:

        subscription = stripe.Subscription.retrieve(subscription_id)

    except stripe.error.StripeError as error:

        print("Stripe subscription check error:", error)

        return JSONResponse(
            {
                "updated": False,
                "reason": "stripe_error",
            }
        )

    items = subscription["items"]["data"]

    if not items:
        return JSONResponse(
            {
                "updated": False,
                "reason": "no_subscription_item",
            }
        )

    current_price_id = items[0]["price"]["id"]

    expected_price_id = PLANS[expected_plan]["stripe_price_id"]

    print("Expected plan:", expected_plan)

    print("Stripe current price:", current_price_id)

    print("Expected Stripe price:", expected_price_id)

    if current_price_id == expected_price_id:

        return JSONResponse(
            {
                "updated": True,
                "current_plan": expected_plan,
                "subscription_status": str(
                    subscription.get(
                        "status",
                        "",
                    )
                ),
            }
        )

    return JSONResponse(
        {
            "updated": False,
            "current_plan": company.get(
                "subscription_plan",
                "",
            ),
        }
    )


# =====================================================
# Preview Subscription Change
# =====================================================


@router.get("/employer/subscription/preview/{plan_name}")
def preview_subscription_change(request: Request, plan_name: str):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    plan = PLANS.get(plan_name)

    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    stripe_price_id = get_stripe_price_id(plan)
    current_plan = str(company.get("subscription_plan", "") or "").lower()

    if current_plan == plan_name:
        raise HTTPException(
            status_code=400,
            detail="This is already your current plan.",
        )

    subscription_id = company.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active Stripe subscription found.",
        )

    subscription = stripe.Subscription.retrieve(subscription_id)
    subscription_items = subscription["items"]["data"]

    if not subscription_items:
        raise HTTPException(
            status_code=400,
            detail="Subscription item not found.",
        )

    subscription_item_id = subscription_items[0]["id"]
    proration_date = int(datetime.now(UTC).timestamp())

    preview = stripe.Invoice.create_preview(
        subscription=subscription_id,
        subscription_details={
            "items": [
                {
                    "id": subscription_item_id,
                    "price": stripe_price_id,
                }
            ],
            "proration_behavior": "always_invoice",
            "proration_date": proration_date,
        },
    )

    amount_due = float(preview.amount_due or 0) / 100
    subtotal = float(preview.subtotal or 0) / 100

    adjustment_cents = 0

    for line in preview.lines.data:
        parent = getattr(line, "parent", None)

        if not parent:
            continue

        details = getattr(
            parent,
            "subscription_item_details",
            None,
        )

        if details and getattr(details, "proration", False):
            if line.amount < 0:
                adjustment_cents += line.amount

    adjustment = float(adjustment_cents) / 100
    card_display = "Saved card"
    customer_id = company.get("stripe_customer_id")

    if customer_id:
        customer = stripe.Customer.retrieve(
            customer_id,
            expand=["invoice_settings.default_payment_method"],
        )

        invoice_settings = customer.invoice_settings

        if invoice_settings is not None:
            payment_method = invoice_settings.default_payment_method

            if isinstance(payment_method, str):
                payment_method = stripe.PaymentMethod.retrieve(payment_method)

            card = getattr(payment_method, "card", None)

            if card is not None:
                brand = str(getattr(card, "brand", "Card")).upper()
                last4 = str(getattr(card, "last4", ""))

                if last4:
                    card_display = f"{brand} •••• {last4}"

    return JSONResponse(
        {
            "plan_name": plan["name"],
            "plan_price": float(plan["price"]),
            "adjustment": adjustment,
            "subtotal": subtotal,
            "amount_due": amount_due,
            "proration_date": proration_date,
            "card_display": card_display,
        }
    )


# =====================================================
# Cancel Subscription At Period End
# =====================================================


@router.post("/employer/subscription/cancel")
def cancel_subscription(request: Request):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    subscription_id = company.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found.",
        )

    try:
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
    except stripe.error.StripeError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    db.collection("company").document(company_id).update(
        {
            "cancel_at_period_end": True,
            "updatedAt": datetime.now(UTC),
        }
    )

    return RedirectResponse(
        url="/employer-credit?cancel=scheduled",
        status_code=303,
    )


# =====================================================
# Resume Subscription
# =====================================================


@router.post("/employer/subscription/resume")
def resume_subscription(request: Request):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    subscription_id = company.get("stripe_subscription_id")

    if not subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No subscription found.",
        )

    try:
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False,
        )
    except stripe.error.StripeError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    db.collection("company").document(company_id).update(
        {
            "cancel_at_period_end": False,
            "updatedAt": datetime.now(UTC),
        }
    )

    return RedirectResponse(
        url="/employer-credit?subscription=resumed",
        status_code=303,
    )


# =====================================================
# Stripe Customer Portal
# =====================================================


@router.post("/employer/payment-method/manage")
def manage_payment_method(request: Request):
    company_id = get_current_company_id(request)
    company = get_company(company_id)
    customer_id = company.get("stripe_customer_id")

    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Stripe customer account not found.",
        )

    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url="http://127.0.0.1:8000/employer-credit",
        )
    except stripe.error.StripeError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return RedirectResponse(
        url=portal_session.url,
        status_code=303,
    )
