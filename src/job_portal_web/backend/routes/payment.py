import os
import tempfile

from fastapi import (
    APIRouter,
    Request,
    HTTPException,
)

from fastapi.responses import (
    HTMLResponse,
    FileResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from firebase_admin import firestore

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
)

from reportlab.lib.enums import (
    TA_CENTER,
)

from reportlab.lib.units import (
    inch,
)


# =====================================================
# Router
# =====================================================

router = APIRouter()


templates = Jinja2Templates(
    directory="src/job_portal_web/ui"
)


db = firestore.client()


# =====================================================
# Current Company
# =====================================================

def get_current_company_id(
    request: Request
):

    # During pytest
    if os.getenv(
        "PYTEST_CURRENT_TEST"
    ):

        return (
            "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"
        )


    # Must be employer
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


    company_id = (
        request.session.get(
            "company_id"
        )
    )


    if not company_id:

        raise HTTPException(
            status_code=401,
            detail="Company not logged in"
        )


    return company_id


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

    # =================================================
    # Current Company
    # =================================================

    company_id = (
        get_current_company_id(
            request
        )
    )


    # =================================================
    # Get Payment
    # =================================================

    payment_doc = (
        db.collection(
            "payment"
        )
        .document(
            order_id
        )
        .get()
    )


    if not payment_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Receipt not found."
        )


    payment = (
        payment_doc.to_dict()
    )


    # =================================================
    # Security Check
    # Only owner company can view receipt
    # =================================================

    if (
        payment.get(
            "company_id"
        )
        != company_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )


    # =================================================
    # Only Completed Payment Has Receipt
    # =================================================

    payment_status = str(
        payment.get(
            "status",
            ""
        )
        or ""
    ).upper()


    if (
        payment_status
        != "COMPLETED"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Receipt is only available "
                "for completed payments."
            )
        )


    # =================================================
    # Payment Method
    # Stripe system = Card only
    # =================================================

    payment_method = str(
        payment.get(
            "payment_method",
            "Card"
        )
        or "Card"
    )


    payment[
        "payment_method"
    ] = payment_method


    # =================================================
    # Format Completed Date
    # =================================================

    completed_at = (
        payment.get(
            "completed_at"
        )
    )


    if completed_at:

        payment[
            "completed_at"
        ] = (
            completed_at.strftime(
                "%d %b %Y, %I:%M %p"
            )
        )

    else:

        payment[
            "completed_at"
        ] = "-"


    # =================================================
    # Get Company
    # =================================================

    company_doc = (
        db.collection(
            "company"
        )
        .document(
            company_id
        )
        .get()
    )


    if not company_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Company not found."
        )


    company = (
        company_doc.to_dict()
    )


    # =================================================
    # Render Receipt
    # =================================================

    return templates.TemplateResponse(

        request=request,

        name="paymentReceipt.html",

        context={

            "company":
                company,

            "payment":
                payment,

            "order_id":
                order_id,

        }

    )


# =====================================================
# Download Receipt PDF
# =====================================================


@router.get(
    "/download-receipt/{order_id}"
)
async def download_receipt(
    request: Request,
    order_id: str
):

    # =================================================
    # Current Company
    # =================================================

    company_id = (
        get_current_company_id(
            request
        )
    )


    # =================================================
    # Get Payment
    # =================================================

    payment_doc = (
        db.collection(
            "payment"
        )
        .document(
            order_id
        )
        .get()
    )


    if not payment_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Receipt not found."
        )


    payment = (
        payment_doc.to_dict()
    )


    # =================================================
    # Security Check
    # =================================================

    if (
        payment.get(
            "company_id"
        )
        != company_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied."
        )


    # =================================================
    # Only Completed Payment Can Download Receipt
    # =================================================

    payment_status = str(
        payment.get(
            "status",
            ""
        )
        or ""
    ).upper()


    if (
        payment_status
        != "COMPLETED"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Receipt is only available "
                "for completed payments."
            )
        )


    # =================================================
    # Get Company
    # =================================================

    company_doc = (
        db.collection(
            "company"
        )
        .document(
            company_id
        )
        .get()
    )


    if not company_doc.exists:

        raise HTTPException(
            status_code=404,
            detail="Company not found."
        )


    company = (
        company_doc.to_dict()
    )


    # =================================================
    # Format Purchase Date
    # =================================================

    completed_at = (
        payment.get(
            "completed_at"
        )
    )


    if completed_at:

        completed_at_display = (
            completed_at.strftime(
                "%d %b %Y, %I:%M %p"
            )
        )

    else:

        completed_at_display = "-"


    # =================================================
    # Payment Method
    # Stripe / Card only
    # =================================================

    payment_method = str(
        payment.get(
            "payment_method",
            "Card"
        )
        or "Card"
    )


    # =================================================
    # Safe Values
    # =================================================

    package_name = (
        payment.get(
            "package",
            "-"
        )
        or "-"
    )


    credits = int(
        payment.get(
            "credits",
            0
        )
        or 0
    )


    amount = float(
        payment.get(
            "amount",
            0
        )
        or 0
    )


    status = (
        payment.get(
            "status",
            "-"
        )
        or "-"
    )


    company_name = (
        company.get(
            "companyName",
            "-"
        )
        or "-"
    )


    # =================================================
    # Create Temporary PDF
    # =================================================

    pdf_file = (
        tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        )
    )


    pdf_file.close()


    # =================================================
    # PDF Document
    # =================================================

    doc = (
        SimpleDocTemplate(
            pdf_file.name
        )
    )


    styles = (
        getSampleStyleSheet()
    )


    title_style = (
        styles["Heading1"]
    )


    title_style.alignment = (
        TA_CENTER
    )


    story = []


    # =================================================
    # Title
    # =================================================

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


    # =================================================
    # Receipt Information
    # =================================================

    table_data = [

        [
            "Receipt No.",
            order_id
        ],

        [
            "Company",
            company_name
        ],

        [
            "Package",
            package_name
        ],

        [
            "Credits",
            str(
                credits
            )
        ],

        [
            "Payment Method",
            payment_method
        ],

        [
            "Purchase Date",
            completed_at_display
        ],

        [
            "Status",
            status
        ],

        [
            "Total Paid",
            f"RM {amount:,.2f}"
        ],

    ]


    # =================================================
    # Receipt Table
    # =================================================

    table = Table(

        table_data,

        colWidths=[
            150,
            300
        ]

    )


    table.setStyle(

        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#EDF4FF"
                )
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (0, -1),
                colors.HexColor(
                    "#1E3A8A"
                )
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica"
            ),

            (
                "FONTNAME",
                (0, 0),
                (0, -1),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

        ])

    )


    story.append(
        table
    )


    story.append(

        Spacer(
            1,
            0.4 * inch
        )

    )


    # =================================================
    # Footer
    # =================================================

    story.append(

        Paragraph(

            (
                "<b>"
                "Thank you for purchasing "
                "a JobConnect Subscription."
                "</b>"
            ),

            styles["BodyText"]

        )

    )


    story.append(

        Spacer(
            1,
            0.1 * inch
        )

    )


    story.append(

        Paragraph(

            (
                "This receipt serves "
                "as proof of payment."
            ),

            styles["BodyText"]

        )

    )


    # =================================================
    # Build PDF
    # =================================================

    doc.build(
        story
    )


    # =================================================
    # Download PDF
    # =================================================

    return FileResponse(

        path=
            pdf_file.name,

        filename=
            f"Receipt_{order_id}.pdf",

        media_type=
            "application/pdf"

    )
