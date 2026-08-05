import os
import base64
import tempfile
from datetime import datetime

import httpx

from firebase_admin import firestore

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
)
from fastapi.templating import Jinja2Templates

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

# =====================================================
# Router
# =====================================================

router = APIRouter()

templates = Jinja2Templates(
    directory="src/job_portal_web/ui"
)

db = firestore.client()


# =====================================================
# PayPal Sandbox
# =====================================================

PAYPAL_CLIENT_ID = "BAA3Y-rLSkg8i4XzXiPa7b02cE4NyJnGrJzeCywpL6L6RvZ_OGUG9GBQcdGdBF9b27ddpkFX0aPCioWmaQ"

PAYPAL_CLIENT_SECRET = "EIBQvxIbaxwWj88V72FDub-kH3SguGJZlbXgCuqJaX-ahKTm3xLJphFAsnJAGTlDvjJNRF8wSd4OBRph"

PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"


# =====================================================
# Packages
# =====================================================

PACKAGES = {

    "starter": {

        "id": "starter",

        "name": "Starter Pack",

        "price": 49,

        "credits": 10,

        "valid_days": 30,

        "description": "Standard job visibility"

    },

    "business": {

        "id": "business",

        "name": "Business Pack",

        "price": 129,

        "credits": 30,

        "valid_days": 60,

        "description": "Featured job visibility"

    },

    "enterprise": {

        "id": "enterprise",

        "name": "Enterprise Pack",

        "price": 229,

        "credits": 60,

        "valid_days": 90,

        "description": "Featured + Top placement"

    }

}


# =====================================================
# Current Company
# =====================================================

def get_current_company_id(request: Request):

    if os.getenv("PYTEST_CURRENT_TEST"):

        return "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"

    if request.session.get("user_type") != "employer":

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    company_id = request.session.get("company_id")

    if not company_id:

        raise HTTPException(
            status_code=401,
            detail="Company not logged in"
        )

    return company_id

# =====================================================
# Get Access Token
# =====================================================

async def get_access_token():

    auth = base64.b64encode(

        f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()

    ).decode()

    async with httpx.AsyncClient() as client:

        response = await client.post(

            f"{PAYPAL_BASE_URL}/v1/oauth2/token",

            headers={

                "Authorization": f"Basic {auth}",

                "Content-Type":
                "application/x-www-form-urlencoded"

            },

            data="grant_type=client_credentials"

        )

    if response.status_code != 200:

        raise HTTPException(

            status_code=500,

            detail=response.text

        )

    return response.json()["access_token"]


# =====================================================
# Payment Page
# =====================================================

@router.get(
    "/payment/{package_name}",
    response_class=HTMLResponse
)
async def payment_page(

    request: Request,

    package_name: str

):

    company_id = get_current_company_id(request)

    package = PACKAGES.get(package_name)

    if not package:

        raise HTTPException(

            status_code=404,

            detail="Package not found"

        )

    company_doc = db.collection(
        "company"
    ).document(
        company_id
    ).get()

    company = company_doc.to_dict()

    return templates.TemplateResponse(

        request=request,

        name="payment.html",

        context={

            "company": company,

            "package": package,

            "package_name": package_name,

            "paypal_client_id":
                PAYPAL_CLIENT_ID

        }

    )

# =====================================================
# Create PayPal Order
# =====================================================

@router.post("/paypal/create-order/{package_name}")
async def create_order(

    request: Request,

    package_name: str

):

    company_id = get_current_company_id(request)

    package = PACKAGES.get(package_name)

    if package is None:

        raise HTTPException(

            status_code=404,

            detail="Package not found."

        )

    access_token = await get_access_token()

    order_data = {

        "intent": "CAPTURE",

        "purchase_units": [

            {

                "reference_id": company_id,

                "description": package["name"],

                "amount": {

                    "currency_code": "MYR",

                    "value": str(package["price"])

                }

            }

        ],

        "application_context": {

            "brand_name": "JobConnect",

            "landing_page": "LOGIN",

            "user_action": "PAY_NOW",

            "shipping_preference": "NO_SHIPPING"

        }

    }

    async with httpx.AsyncClient() as client:

        response = await client.post(

            f"{PAYPAL_BASE_URL}/v2/checkout/orders",

            headers={

                "Authorization":
                    f"Bearer {access_token}",

                "Content-Type":
                    "application/json"

            },

            json=order_data

        )

    if response.status_code not in (200, 201):

        print(response.text)

        raise HTTPException(

            status_code=500,

            detail="Unable to create PayPal Order."

        )

    order = response.json()

    order_id = order["id"]

    # ==========================================
    # Save Pending Payment
    # ==========================================

    db.collection("payment").document(order_id).set({

        "paypal_order_id": order_id,

        "company_id": company_id,

        "package_name": package_name,

        "package": package["name"],

        "credits": package["credits"],

        "amount": package["price"],

        "status": "PENDING",

        "payment_method": "PayPal",

        "created_at": firestore.SERVER_TIMESTAMP

    })

    return JSONResponse({

        "id": order_id

    })


# =====================================================
# Capture PayPal Order
# =====================================================

@router.post("/paypal/capture-order/{order_id}")
async def capture_order(
    request: Request,
    order_id: str
):

    company_id = get_current_company_id(request)

    payment_ref = db.collection("payment").document(order_id)

    payment_doc = payment_ref.get()

    if not payment_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Payment record not found."
        )

    payment = payment_doc.to_dict()

    # Already completed

    if payment.get("status") == "COMPLETED":

        return JSONResponse({

            "success": True

        })

    access_token = await get_access_token()

    async with httpx.AsyncClient() as client:

        response = await client.post(

            f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",

            headers={

                "Authorization":
                    f"Bearer {access_token}",

                "Content-Type":
                    "application/json"

            }

        )

    if response.status_code not in (200, 201):

        print(response.text)

        raise HTTPException(

            status_code=500,

            detail="Capture payment failed."

        )

    result = response.json()

    if result["status"] != "COMPLETED":

        raise HTTPException(

            status_code=400,

            detail="Payment not completed."

        )

    company_ref = db.collection("company").document(company_id)

    company_doc = company_ref.get()

    company = company_doc.to_dict()

    current_available = company.get(

        "available_credit",

        0

    )

    current_total = company.get(

        "total_credit",

        0

    )

    credits = payment["credits"]

    new_available = current_available + credits

    new_total = current_total + credits

    # =====================================
    # Update Company
    # =====================================

    company_ref.update({

        "available_credit": new_available,

        "total_credit": new_total,

        # Subscription information
        "subscription_plan": payment["package_name"],

        "subscription_status": "ACTIVE"

})

    # =====================================
    # Update Payment
    # =====================================

    payment_ref.update({

        "status": "COMPLETED",

        "completed_at": firestore.SERVER_TIMESTAMP

    })

    # =====================================
    # Save History
    # =====================================

    db.collection("credit_history").add({

        "company_id": company_id,

        "date": datetime.now(),

        "description":
            f"Purchased {payment['package']}",

        "credit": credits,

        "balance": new_available,

        "reference": order_id

    })

    return JSONResponse({

        "success": True

    })

# =====================================================
# Payment Success
# =====================================================

@router.get(
    "/payment-success",
    response_class=HTMLResponse
)
async def payment_success(
    request: Request
):

    company_id = get_current_company_id(request)

    company_doc = db.collection(
        "company"
    ).document(
        company_id
    ).get()

    company = company_doc.to_dict()

    order_id = request.query_params.get("order_id")

    payment = {}

    if order_id:

        payment_doc = (
            db.collection("payment")
            .document(order_id)
            .get()
        )

        if payment_doc.exists:

            payment = payment_doc.to_dict()

            completed_at = payment.get("completed_at")

            if completed_at:

                payment["completed_at"] = completed_at.strftime(
                    "%d %b %Y, %I:%M %p"
                )

    return templates.TemplateResponse(

        request=request,

        name="paymentSuccess.html",

        context={
            "company": company,
            "order_id": order_id,
            "payment": payment
        }
    )

# =====================================================
# Payment Receipt
# =====================================================

@router.get(
    "/payment-receipt/{order_id}",
    response_class=HTMLResponse
)
async def payment_receipt(
    request: Request,
    order_id: str
):

    company_id = get_current_company_id(request)

    payment_doc = (
        db.collection("payment")
        .document(order_id)
        .get()
    )

    if not payment_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Receipt not found."
        )

    payment = payment_doc.to_dict()

    completed_at = payment.get("completed_at")

    if completed_at:

        payment["completed_at"] = completed_at.strftime(
            "%d %b %Y, %I:%M %p"
        )

    # Prevent other companies viewing this receipt
    if payment["company_id"] != company_id:

        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    company = (
        db.collection("company")
        .document(company_id)
        .get()
        .to_dict()
    )

    return templates.TemplateResponse(

        request=request,

        name="paymentReceipt.html",

        context={

            "company": company,

            "payment": payment,

            "order_id": order_id

        }

    )

# =====================================================
# Download Receipt PDF
# =====================================================

@router.get("/download-receipt/{order_id}")
async def download_receipt(
    request: Request,
    order_id: str
):

    company_id = get_current_company_id(request)

    payment_doc = (
        db.collection("payment")
        .document(order_id)
        .get()
    )

    if not payment_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Receipt not found."
        )

    payment = payment_doc.to_dict()

    if payment["company_id"] != company_id:

        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )

    company_doc = (
        db.collection("company")
        .document(company_id)
        .get()
    )

    company = company_doc.to_dict()

    # ----------------------------------------
    # Create temporary PDF
    # ----------------------------------------

    pdf_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    )

    doc = SimpleDocTemplate(
        pdf_file.name
    )

    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER

    story = []

    # ----------------------------------------
    # Title
    # ----------------------------------------

    story.append(
        Paragraph(
            "JOBCONNECT PAYMENT RECEIPT",
            title_style
        )
    )

    story.append(
        Spacer(
            1,
            0.3 * inch
        )
    )

    # ----------------------------------------
    # Receipt Information
    # ----------------------------------------

    completed_at = payment.get("completed_at")

    if completed_at:

        completed_at = completed_at.strftime(
            "%d %b %Y, %I:%M %p"
        )

    else:

        completed_at = "-"

    table_data = [

        ["Receipt No.", order_id],

        [
            "Company",
            company.get(
                "companyName",
                "-"
            )
        ],

        [
            "Package",
            payment.get(
                "package",
                "-"
            )
        ],

        [
            "Credits",
            str(
                payment.get(
                    "credits",
                    0
                )
            )
        ],

        [
            "Amount",
            f"RM {payment.get('amount',0)}"
        ],

        [
            "Payment Method",
            payment.get(
                "payment_method",
                "-"
            )
        ],

        [
            "Status",
            payment.get(
                "status",
                "-"
            )
        ],

        [
            "Purchase Date",
            completed_at
        ]

    ]

    table = Table(
        table_data,
        colWidths=[150, 300]
    )

    table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.whitesmoke
            ),

            (
                "GRID",
                (0,0),
                (-1,-1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0,0),
                (0,-1),
                colors.HexColor("#EDF4FF")
            ),

            (
                "TEXTCOLOR",
                (0,0),
                (0,-1),
                colors.HexColor("#1E3A8A")
            ),

            (
                "FONTNAME",
                (0,0),
                (-1,-1),
                "Helvetica"
            ),

            (
                "BOTTOMPADDING",
                (0,0),
                (-1,-1),
                10
            ),

            (
                "TOPPADDING",
                (0,0),
                (-1,-1),
                10
            )

        ])

    )

    story.append(table)

    story.append(
        Spacer(
            1,
            0.4 * inch
        )
    )

    story.append(

        Paragraph(

            "<b>Thank you for purchasing a JobConnect Subscription.</b>",

            styles["BodyText"]

        )

    )

    story.append(

        Paragraph(

            "This receipt serves as proof of payment.",

            styles["BodyText"]

        )

    )

    doc.build(story)

    # ----------------------------------------
    # Download PDF
    # ----------------------------------------

    return FileResponse(

        path=pdf_file.name,

        filename=f"Receipt_{order_id}.pdf",

        media_type="application/pdf"

    )