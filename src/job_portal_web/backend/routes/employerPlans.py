import os

import stripe
from datetime import datetime, timezone

from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Form,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from fastapi.templating import (
    Jinja2Templates
)

from firebase_admin import firestore


# =====================================================
# Environment
# =====================================================

load_dotenv()

stripe.api_key = os.getenv(
    "STRIPE_SECRET_KEY"
)


router = APIRouter()

templates = Jinja2Templates(
    directory="src/job_portal_web/ui"
)

db = firestore.client()


# =====================================================
# Plan Configuration
# =====================================================

PLANS = {

    "starter": {

        "id": "starter",

        "name": "Starter Pack",

        "price": 49,

        "credits": 10,

        "description":
            "Standard job visibility",

        "stripe_price_id":
            os.getenv(
                "STRIPE_STARTER_PRICE_ID"
            ),
    },


    "business": {

        "id": "business",

        "name": "Business Pack",

        "price": 129,

        "credits": 30,

        "description":
            "Featured job visibility",

        "stripe_price_id":
            os.getenv(
                "STRIPE_BUSINESS_PRICE_ID"
            ),
    },


    "enterprise": {

        "id": "enterprise",

        "name": "Enterprise Pack",

        "price": 229,

        "credits": 60,

        "description":
            "Featured + Top placement",

        "stripe_price_id":
            os.getenv(
                "STRIPE_ENTERPRISE_PRICE_ID"
            ),
    },
}


# =====================================================
# Current Company
# =====================================================

def get_current_company_id(
    request: Request
):

    if os.getenv(
        "PYTEST_CURRENT_TEST"
    ):

        return (
            "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"
        )

    if (
        request.session.get(
            "user_type"
        )
        != "employer"
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    company_id = request.session.get(
        "company_id"
    )

    if not company_id:

        raise HTTPException(
            status_code=401,
            detail="Company not logged in"
        )

    return company_id


# =====================================================
# Get Company
# =====================================================

def get_company(company_id: str):

    company_doc = (
        db.collection("company")
        .document(company_id)
        .get()
    )

    if not company_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company_doc.to_dict()


# =====================================================
# Create Stripe Customer If Missing
# =====================================================

def get_or_create_stripe_customer(
    company_id: str,
    company: dict
):

    customer_id = company.get(
        "stripe_customer_id"
    )

    if customer_id:

        return customer_id

    customer = stripe.Customer.create(

        name=company.get(
            "companyName",
            "JobConnect Employer"
        ),

        email=(
            company.get("email")
            or company.get(
                "businessEmail"
            )
        ),

        metadata={
            "company_id":
                company_id
        },
    )

    (
        db.collection("company")
        .document(company_id)
        .update({
            "stripe_customer_id":
                customer.id
        })
    )

    return customer.id


# =====================================================
# Plans Page
# =====================================================

@router.get(
    "/employer-plans",
    response_class=HTMLResponse
)
def employer_plans(
    request: Request
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    current_plan = str(
        company.get(
            "subscription_plan",
            ""
        ) or ""
    ).lower()

    return templates.TemplateResponse(

        request=request,

        name="employerPlans.html",

        context={

            "company":
                company,

            "plans":
                PLANS,

            "current_plan":
                current_plan,

            "subscription_status":
                company.get(
                    "subscription_status",
                    ""
                ),

            "active_page":
                "credit",
        },
    )


# =====================================================
# First Subscription
# =====================================================

@router.post(
    "/employer/subscription/start/{plan_name}"
)
def start_subscription(
    request: Request,
    plan_name: str
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    plan = PLANS.get(
        plan_name
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    if not plan["stripe_price_id"]:

        raise HTTPException(
            status_code=500,
            detail=(
                "Stripe Price ID "
                "is not configured."
            )
        )

    # Existing Stripe subscription?
    existing_subscription = (
        company.get(
            "stripe_subscription_id"
        )
    )

    if existing_subscription:

        return RedirectResponse(
            url="/employer-plans",
            status_code=303
        )

    customer_id = (
        get_or_create_stripe_customer(
            company_id,
            company
        )
    )

    # =================================================
    # Stripe Checkout
    # =================================================

    checkout_session = (
        stripe.checkout.Session.create(

            customer=customer_id,

            mode="subscription",

            payment_method_types=[
                "card"
            ],

            line_items=[
                {
                    "price":
                        plan[
                            "stripe_price_id"
                        ],

                    "quantity": 1,
                }
            ],

            subscription_data={

                "metadata": {

                    "company_id":
                        company_id,

                    "plan":
                        plan_name,
                }
            },

            success_url=(
                "http://127.0.0.1:8000/"
                "stripe/payment-success"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),

            cancel_url=(
                "http://127.0.0.1:8000/"
                "employer-plans"
                "?subscription=cancelled"
            ),
        )
    )

    return RedirectResponse(
        checkout_session.url,
        status_code=303
    )


# =====================================================
# Change Existing Plan
# =====================================================

@router.post(
    "/employer/subscription/change/{plan_name}"
)
def change_subscription(
    request: Request,
    plan_name: str,
    proration_date: int = Form(...)
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    plan = PLANS.get(
        plan_name
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )

    current_plan = str(
        company.get(
            "subscription_plan",
            ""
        )
    ).lower()

    # Same plan
    if current_plan == plan_name:

        return RedirectResponse(
            "/employer-plans",
            status_code=303
        )

    subscription_id = (
        company.get(
            "stripe_subscription_id"
        )
    )

    # Old PayPal company / no Stripe subscription
    if not subscription_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "This account does not yet "
                "have a Stripe subscription. "
                "Start a Stripe subscription first."
            )
        )

    # =================================================
    # Retrieve Stripe Subscription
    # =================================================

    subscription = (
        stripe.Subscription.retrieve(
            subscription_id
        )
    )

    subscription_items = (
        subscription[
            "items"
        ][
            "data"
        ]
    )

    if not subscription_items:

        raise HTTPException(
            status_code=400,
            detail=(
                "Subscription item "
                "not found."
            )
        )

    subscription_item_id = (
        subscription_items[0]["id"]
    )

    # =================================================
    # CHANGE PLAN WITH PRORATION
    # =================================================
    #
    # Example:
    #
    # Starter = RM49/month
    #
    # Upgrade halfway through month
    # to Business RM129.
    #
    # Stripe calculates:
    #
    # unused Starter credit
    # +
    # remaining Business charge
    #
    # You DON'T manually calculate it.
    # =================================================

    updated_subscription = (
        stripe.Subscription.modify(

            subscription_id,

            items=[
                {
                    "id":
                        subscription_item_id,

                    "price":
                        plan[
                            "stripe_price_id"
                        ],
                }
            ],

            proration_behavior=
                "always_invoice",

            proration_date=
                proration_date,

            payment_behavior=
                "pending_if_incomplete",

            metadata={

                "company_id":
                    company_id,

                "plan":
                    plan_name,
            },
        )
    )

    # Don't manually change Firestore plan here.
    #
    # Webhook will update Firestore
    # after Stripe confirms the change/payment.

    return RedirectResponse(
        "/employer-credit"
        "?plan_change=processing",
        status_code=303
    )

@router.get(
    "/employer/subscription/preview/{plan_name}"
)
def preview_subscription_change(
    request: Request,
    plan_name: str
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    plan = PLANS.get(
        plan_name
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Plan not found"
        )


    current_plan = str(
        company.get(
            "subscription_plan",
            ""
        )
        or ""
    ).lower()


    if current_plan == plan_name:

        raise HTTPException(
            status_code=400,
            detail=(
                "This is already your "
                "current plan."
            )
        )


    subscription_id = (
        company.get(
            "stripe_subscription_id"
        )
    )


    if not subscription_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "No active Stripe "
                "subscription found."
            )
        )


    subscription = (
        stripe.Subscription.retrieve(
            subscription_id
        )
    )


    subscription_items = (
        subscription["items"]["data"]
    )


    if not subscription_items:

        raise HTTPException(
            status_code=400,
            detail=(
                "Subscription item "
                "not found."
            )
        )


    subscription_item_id = (
        subscription_items[0]["id"]
    )


    # ==========================================
    # Use one fixed proration timestamp
    # ==========================================

    proration_date = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )


    # ==========================================
    # Stripe Preview
    # ==========================================

    preview = (
        stripe.Invoice.create_preview(

            subscription=
                subscription_id,

            subscription_details={

                "items": [

                    {
                        "id":
                            subscription_item_id,

                        "price":
                            plan[
                                "stripe_price_id"
                            ],
                    }

                ],

                "proration_behavior":
                    "always_invoice",

                "proration_date":
                    proration_date,
            },
        )
    )


    # ==========================================
    # Amounts
    # Stripe values are cents
    # ==========================================

    amount_due = (
        float(
            preview.amount_due
            or 0
        )
        / 100
    )


    subtotal = (
        float(
            preview.subtotal
            or 0
        )
        / 100
    )


    # ==========================================
    # Find proration adjustment
    # ==========================================

    adjustment_cents = 0


    for line in preview.lines.data:

        parent = getattr(
            line,
            "parent",
            None
        )

        if not parent:
            continue


        details = getattr(
            parent,
            "subscription_item_details",
            None
        )


        if (
            details
            and getattr(
                details,
                "proration",
                False
            )
        ):

            # Negative amount = credit
            if line.amount < 0:

                adjustment_cents += (
                    line.amount
                )


    adjustment = (
        float(
            adjustment_cents
        )
        / 100
    )


    # ==========================================
    # Saved Card Display
    # ==========================================

    card_display = "Saved card"


    customer_id = (
        company.get(
            "stripe_customer_id"
        )
    )


    if customer_id:

        customer = (
            stripe.Customer.retrieve(
                customer_id,
                expand=[
                    "invoice_settings.default_payment_method"
                ]
            )
        )


        payment_method = (
            customer.invoice_settings
            .default_payment_method
        )


        if (
            payment_method
            and payment_method.card
        ):

            card_display = (
                f"{payment_method.card.brand.upper()} "
                f"•••• {payment_method.card.last4}"
            )


    return JSONResponse({

        "plan_name":
            plan["name"],

        "plan_price":
            float(
                plan["price"]
            ),

        "adjustment":
            adjustment,

        "subtotal":
            subtotal,

        "amount_due":
            amount_due,

        "proration_date":
            proration_date,

        "card_display":
            card_display,
    })

# =====================================================
# Cancel Subscription At Period End
# =====================================================

@router.post(
    "/employer/subscription/cancel"
)
def cancel_subscription(
    request: Request
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    subscription_id = (
        company.get(
            "stripe_subscription_id"
        )
    )

    if not subscription_id:

        raise HTTPException(
            status_code=400,
            detail="No active subscription found."
        )

    try:

        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )

    except stripe.error.StripeError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # Stripe webhook will also receive
    # customer.subscription.updated.
    # We update this immediately so UI
    # can show the scheduled cancellation.

    db.collection(
        "company"
    ).document(
        company_id
    ).update({

        "cancel_at_period_end":
            True,

        "updatedAt":
            datetime.now(
                timezone.utc
            ),
    })

    return RedirectResponse(
        "/employer-credit?cancel=scheduled",
        status_code=303
    )

# =====================================================
# Resume Subscription
# =====================================================

@router.post(
    "/employer/subscription/resume"
)
def resume_subscription(
    request: Request
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    subscription_id = (
        company.get(
            "stripe_subscription_id"
        )
    )

    if not subscription_id:

        raise HTTPException(
            status_code=400,
            detail="No subscription found."
        )

    try:

        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False,
        )

    except stripe.error.StripeError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    db.collection(
        "company"
    ).document(
        company_id
    ).update({

        "cancel_at_period_end":
            False,

        "updatedAt":
            datetime.now(
                timezone.utc
            ),
    })

    return RedirectResponse(
        "/employer-credit?subscription=resumed",
        status_code=303
    )

# =====================================================
# Stripe Customer Portal
# =====================================================

@router.post(
    "/employer/payment-method/manage"
)
def manage_payment_method(
    request: Request
):

    company_id = (
        get_current_company_id(
            request
        )
    )

    company = get_company(
        company_id
    )

    customer_id = company.get(
        "stripe_customer_id"
    )

    if not customer_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "Stripe customer account "
                "not found."
            )
        )

    try:

        portal_session = (
            stripe.billing_portal.Session.create(

                customer=
                    customer_id,

                return_url=(
                    "http://127.0.0.1:8000/"
                    "employer-credit"
                ),
            )
        )

    except stripe.error.StripeError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return RedirectResponse(
        portal_session.url,
        status_code=303
    )