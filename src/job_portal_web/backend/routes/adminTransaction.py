from datetime import datetime, timezone
import math
from fastapi.responses import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from ..database import db

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")


# =====================================================
# Transaction Management
# =====================================================

@router.get("/admin/transactions")
def transaction_management(
    request: Request,
    status: str = "",
    payment_method: str = "",
    keyword: str = "",
    page: int = 1,
):

    PER_PAGE = 20

    all_transactions = []

    # Automatically changes every year
    current_year = datetime.now(timezone.utc).year

    # Clean filter values
    keyword_lower = keyword.strip().lower()
    status_filter = status.strip().upper()
    payment_method_filter = payment_method.strip().lower()

    # =====================================================
    # Get ALL payments
    # =====================================================

    docs = db.collection("payment").stream()

    for doc in docs:

        data = doc.to_dict()

        data["transaction_id"] = doc.id

        # =================================================
        # Get company information
        # =================================================

        company_name = ""
        company_email = ""

        company_id = data.get("company_id")

        if company_id:

            company_doc = (
                db.collection("company")
                .document(company_id)
                .get()
            )

            if company_doc.exists:

                company_data = company_doc.to_dict()

                company_name = company_data.get(
                    "companyName",
                    ""
                )

                company_email = company_data.get(
                    "email",
                    ""
                )

        data["company_name"] = company_name
        data["company_email"] = company_email

        # =================================================
        # STATUS FILTER
        # =================================================

        payment_status = str(
            data.get("status", "")
        ).strip().upper()

        if status_filter:

            if payment_status != status_filter:
                continue

        # =================================================
        # PAYMENT METHOD FILTER
        # =================================================

        stored_payment_method = str(
            data.get("payment_method", "")
        ).strip().lower()

        if payment_method_filter:

            if stored_payment_method != payment_method_filter:
                continue

        # =================================================
        # SEARCH
        # =================================================

        if keyword_lower:

            transaction_id = doc.id.lower()

            paypal_order_id = str(
                data.get("paypal_order_id", "")
            ).lower()

            package_name = str(
                data.get("package_name", "")
            ).lower()

            if (
                keyword_lower not in transaction_id
                and keyword_lower not in paypal_order_id
                and keyword_lower not in company_name.lower()
                and keyword_lower not in company_email.lower()
                and keyword_lower not in package_name
            ):
                continue

        # =================================================
        # Date
        # =================================================

        payment_date = (
            data.get("completed_at")
            or data.get("created_at")
        )

        data["display_date"] = payment_date

        all_transactions.append(data)

    # =====================================================
    # Sort newest -> oldest
    # =====================================================

    all_transactions.sort(
        key=lambda transaction: (
            transaction.get("display_date")
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True,
    )

    # =====================================================
    # SUMMARY COUNTS
    # Based on current filtered results
    # =====================================================

    total_revenue = 0
    successful = 0
    pending = 0
    refunded = 0
    failed = 0

    for transaction in all_transactions:

        payment_status = str(
            transaction.get("status", "")
        ).strip().upper()

        amount = float(
            transaction.get("amount", 0) or 0
        )

        payment_date = transaction.get("display_date")

        if payment_status == "COMPLETED":

            successful += 1

            # Only revenue from current year
            if payment_date and payment_date.year == current_year:
                total_revenue += amount

        elif payment_status == "PENDING":
            pending += 1

        elif payment_status == "REFUNDED":
            refunded += 1

        elif payment_status == "FAILED":
            failed += 1

    # =====================================================
    # Pagination
    # =====================================================

    total_transactions = len(all_transactions)

    total_pages = max(
        1,
        math.ceil(total_transactions / PER_PAGE)
    )

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    start = (page - 1) * PER_PAGE

    end = start + PER_PAGE

    transactions = all_transactions[start:end]

    # =====================================================
    # Render
    # =====================================================

    return templates.TemplateResponse(
        request=request,
        name="adminTransactions.html",
        context={
            "active_page": "transactions",

            "transactions": transactions,

            "total_transactions": total_transactions,
            "total_revenue": total_revenue,

            "successful": successful,
            "pending": pending,
            "refunded": refunded,
            "failed": failed,

            "current_year": current_year,

            "current_status": status,
            "current_payment_method": payment_method,
            "keyword": keyword,

            "current_page": page,
            "total_pages": total_pages,
            "per_page": PER_PAGE,
        },
    )

# =====================================================
# Transaction Report Page
# =====================================================

@router.get("/admin/transactions/report")
def transaction_report_page(
    request: Request,
    from_date: str = "",
    to_date: str = "",
    status: str = "",
    payment_method: str = "",
):

    transactions = []

    docs = db.collection("payment").stream()

    total_revenue = 0
    successful = 0
    pending = 0
    failed = 0

    for doc in docs:

        data = doc.to_dict()

        data["transaction_id"] = doc.id

        # -----------------------------------------
        # Company
        # -----------------------------------------
        company_name = ""

        company_id = data.get("company_id")

        if company_id:

            company_doc = (
                db.collection("company")
                .document(company_id)
                .get()
            )

            if company_doc.exists:

                company_name = (
                    company_doc.to_dict()
                    .get("companyName", "")
                )

        data["company_name"] = company_name

        # -----------------------------------------
        # Status
        # -----------------------------------------
        payment_status = str(
            data.get("status", "")
        ).upper()

        if status and payment_status != status.upper():
            continue

        # -----------------------------------------
        # Payment method
        # -----------------------------------------
        stored_method = str(
            data.get("payment_method", "")
        ).upper()

        if (
            payment_method
            and stored_method != payment_method.upper()
        ):
            continue

        # -----------------------------------------
        # Date
        # -----------------------------------------
        payment_date = (
            data.get("completed_at")
            or data.get("created_at")
        )

        data["display_date"] = payment_date

        if payment_date:

            payment_date_string = (
                payment_date.strftime("%Y-%m-%d")
            )

            if (
                from_date
                and payment_date_string < from_date
            ):
                continue

            if (
                to_date
                and payment_date_string > to_date
            ):
                continue

        # -----------------------------------------
        # Summary
        # -----------------------------------------
        amount = float(
            data.get("amount", 0) or 0
        )

        if payment_status == "COMPLETED":
            successful += 1
            total_revenue += amount

        elif payment_status == "PENDING":
            pending += 1

        elif payment_status == "FAILED":
            failed += 1

        transactions.append(data)

    # Newest first
    transactions.sort(
        key=lambda x: (
            x.get("display_date")
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="adminTransactionReport.html",
        context={
            "active_page": "transactions",

            "transactions": transactions,

            "total_transactions": len(transactions),
            "total_revenue": total_revenue,
            "successful": successful,
            "pending": pending,
            "failed": failed,

            "from_date": from_date,
            "to_date": to_date,
            "current_status": status,
            "current_payment_method": payment_method,
        },
    )

# =====================================================
# Download Transaction Report PDF
# =====================================================

@router.get("/admin/transactions/report/download")
def download_transaction_report(
    from_date: str = "",
    to_date: str = "",
    status: str = "",
    payment_method: str = "",
):

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        HRFlowable
    )

    import os

    # =====================================================
    # LOAD TRANSACTIONS
    # =====================================================

    transactions = []

    total_revenue = 0

    docs = db.collection("payment").stream()

    for doc in docs:

        data = doc.to_dict()

        transaction_id = doc.id

        # =================================================
        # COMPANY
        # =================================================

        company_name = "-"

        company_id = data.get("company_id")

        if company_id:

            company_doc = (
                db.collection("company")
                .document(company_id)
                .get()
            )

            if company_doc.exists:

                company_data = company_doc.to_dict()

                company_name = company_data.get(
                    "companyName",
                    "-"
                )

        # =================================================
        # STATUS
        # =================================================

        payment_status = str(
            data.get("status", "")
        ).strip().upper()

        if status:

            if payment_status != status.strip().upper():
                continue

        # =================================================
        # PAYMENT METHOD
        # =================================================

        method = str(
            data.get("payment_method", "-")
        ).strip()

        if payment_method:

            if method.upper() != payment_method.strip().upper():
                continue

        # =================================================
        # PAYMENT DATE
        # =================================================

        payment_date = (
            data.get("completed_at")
            or data.get("created_at")
        )

        if payment_date:

            payment_date_string = payment_date.strftime(
                "%Y-%m-%d"
            )

            if from_date and payment_date_string < from_date:
                continue

            if to_date and payment_date_string > to_date:
                continue

        # =================================================
        # AMOUNT
        # =================================================

        amount = float(
            data.get("amount", 0) or 0
        )

        if payment_status == "COMPLETED":
            total_revenue += amount

        # =================================================
        # SAVE TRANSACTION
        # =================================================

        transactions.append({
            "transaction_id": transaction_id,
            "company_name": company_name,
            "package": data.get("package", "-"),
            "payment_method": method,
            "amount": amount,
            "status": payment_status,
            "payment_date": payment_date,
            "date_display": (
                payment_date.strftime("%d %b %Y")
                if payment_date
                else "-"
            ),
        })

    # =====================================================
    # SORT NEWEST -> OLDEST
    # =====================================================

    transactions.sort(
        key=lambda transaction: (
            transaction["payment_date"]
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True
    )

    # =====================================================
    # REPORT PERIOD
    # =====================================================

    def format_date(date_string):

        if not date_string:
            return None

        try:

            return datetime.strptime(
                date_string,
                "%Y-%m-%d"
            ).strftime("%d %b %Y")

        except ValueError:

            return date_string

    formatted_from = format_date(from_date)
    formatted_to = format_date(to_date)

    if formatted_from and formatted_to:

        report_period = (
            f"{formatted_from} - {formatted_to}"
        )

    elif formatted_from:

        report_period = (
            f"{formatted_from} - Present"
        )

    elif formatted_to:

        report_period = (
            f"Beginning - {formatted_to}"
        )

    else:

        report_period = "All Dates"

    # =====================================================
    # FILTER DISPLAY VALUES
    # =====================================================

    status_display = (
        status.title()
        if status
        else "All Status"
    )

    payment_method_display = (
        payment_method
        if payment_method
        else "All Payment Methods"
    )

    generated_date = datetime.now().strftime(
        "%d %b %Y"
    )

    generated_time = datetime.now().strftime(
        "%I:%M %p"
    )

    # =====================================================
    # FILE
    # =====================================================

    output_dir = "generated_reports"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    filename = (
        "JobConnect_Transaction_Report_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    filepath = os.path.join(
        output_dir,
        filename
    )

    # =====================================================
    # PDF
    # =====================================================

    pdf = SimpleDocTemplate(
        filepath,

        pagesize=landscape(A4),

        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # STYLES
    # =====================================================

    company_style = ParagraphStyle(
        "CompanyName",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=19,

        leading=23,

        textColor=colors.HexColor("#1F2937"),

        spaceAfter=2,
    )

    report_title_style = ParagraphStyle(
        "ReportTitle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=14,

        leading=18,

        textColor=colors.HexColor("#374151"),
    )

    small_gray_style = ParagraphStyle(
        "SmallGray",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=8,

        leading=11,

        textColor=colors.HexColor("#6B7280"),
    )

    metadata_label_style = ParagraphStyle(
        "MetadataLabel",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8.5,

        leading=11,

        textColor=colors.HexColor("#6B7280"),
    )

    metadata_value_style = ParagraphStyle(
        "MetadataValue",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=9,

        leading=12,

        textColor=colors.HexColor("#111827"),
    )

    section_title_style = ParagraphStyle(
        "SectionTitle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=11,

        leading=14,

        textColor=colors.HexColor("#1F2937"),

        spaceAfter=7,
    )

    table_text_style = ParagraphStyle(
        "TableText",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7.5,

        leading=10,

        textColor=colors.HexColor("#374151"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=7.5,

        leading=10,

        textColor=colors.white,
    )

    # =====================================================
    # PAGE FOOTER
    # =====================================================

    def add_page_number(canvas, document):

        canvas.saveState()

        page_number = canvas.getPageNumber()

        width, height = landscape(A4)

        # Footer line
        canvas.setStrokeColor(
            colors.HexColor("#E5E7EB")
        )

        canvas.setLineWidth(0.5)

        canvas.line(
            18 * mm,
            13 * mm,
            width - 18 * mm,
            13 * mm
        )

        # Left footer
        canvas.setFont(
            "Helvetica",
            7.5
        )

        canvas.setFillColor(
            colors.HexColor("#6B7280")
        )

        canvas.drawString(
            18 * mm,
            8 * mm,
            "JobConnect Administration - Confidential"
        )

        # Right footer
        canvas.drawRightString(
            width - 18 * mm,
            8 * mm,
            f"Page {page_number}"
        )

        canvas.restoreState()

    # =====================================================
    # CONTENT
    # =====================================================

    elements = []

    # =====================================================
    # HEADER
    # =====================================================

    left_header = [
        Paragraph(
            "JobConnect",
            company_style
        ),

        Paragraph(
            "ADMIN TRANSACTION REPORT",
            report_title_style
        ),
    ]

    right_header = [
        Paragraph(
            "Generated",
            metadata_label_style
        ),

        Paragraph(
            f"{generated_date}<br/>{generated_time}",
            metadata_value_style
        ),
    ]

    header_table = Table(
        [
            [
                left_header,
                right_header
            ]
        ],
        colWidths=[
            190 * mm,
            55 * mm
        ]
    )

    header_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "RIGHT"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
        ])
    )

    elements.append(header_table)

    elements.append(
        Spacer(1, 7)
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#CBD5E1"),
            spaceAfter=12,
        )
    )

    # =====================================================
    # REPORT INFORMATION
    # =====================================================

    elements.append(
        Paragraph(
            "Report Information",
            section_title_style
        )
    )

    report_info = [
        [
            Paragraph(
                "Report Period",
                metadata_label_style
            ),

            Paragraph(
                report_period,
                metadata_value_style
            ),

            Paragraph(
                "Status",
                metadata_label_style
            ),

            Paragraph(
                status_display,
                metadata_value_style
            ),
        ],

        [
            Paragraph(
                "Payment Method",
                metadata_label_style
            ),

            Paragraph(
                payment_method_display,
                metadata_value_style
            ),

            Paragraph(
                "Prepared By",
                metadata_label_style
            ),

            Paragraph(
                "JobConnect Administration",
                metadata_value_style
            ),
        ],
    ]

    info_table = Table(
        report_info,

        colWidths=[
            33 * mm,
            72 * mm,
            35 * mm,
            75 * mm,
        ]
    )

    info_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#F8FAFC")
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#E5E7EB")
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#E5E7EB")
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
        ])
    )

    elements.append(info_table)

    elements.append(
        Spacer(1, 14)
    )

    # =====================================================
    # REPORT SUMMARY
    # =====================================================

    elements.append(
        Paragraph(
            "Report Summary",
            section_title_style
        )
    )

    summary_table = Table(
        [
            [
                Paragraph(
                    "Total Transactions",
                    metadata_label_style
                ),

                Paragraph(
                    str(len(transactions)),
                    metadata_value_style
                ),

                Paragraph(
                    "Total Revenue",
                    metadata_label_style
                ),

                Paragraph(
                    f"RM {total_revenue:,.2f}",
                    metadata_value_style
                ),
            ]
        ],

        colWidths=[
            38 * mm,
            28 * mm,
            35 * mm,
            40 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor("#CBD5E1")
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.white
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
        ])
    )

    elements.append(summary_table)

    elements.append(
        Spacer(1, 17)
    )

    # =====================================================
    # TRANSACTION DETAILS
    # =====================================================

    elements.append(
        Paragraph(
            "Transaction Details",
            section_title_style
        )
    )

    # =====================================================
    # TABLE HEADER
    # =====================================================

    table_data = [
        [
            Paragraph(
                "Transaction ID",
                table_header_style
            ),

            Paragraph(
                "Company",
                table_header_style
            ),

            Paragraph(
                "Package",
                table_header_style
            ),

            Paragraph(
                "Payment Method",
                table_header_style
            ),

            Paragraph(
                "Amount",
                table_header_style
            ),

            Paragraph(
                "Status",
                table_header_style
            ),

            Paragraph(
                "Date",
                table_header_style
            ),
        ]
    ]

    # =====================================================
    # TABLE DATA
    # =====================================================

    if transactions:

        for transaction in transactions:

            status_text = (
                transaction["status"]
                .replace("_", " ")
                .title()
            )

            table_data.append([
                Paragraph(
                    transaction["transaction_id"],
                    table_text_style
                ),

                Paragraph(
                    transaction["company_name"],
                    table_text_style
                ),

                Paragraph(
                    str(transaction["package"]),
                    table_text_style
                ),

                Paragraph(
                    transaction["payment_method"],
                    table_text_style
                ),

                Paragraph(
                    f'RM {transaction["amount"]:,.2f}',
                    table_text_style
                ),

                Paragraph(
                    status_text,
                    table_text_style
                ),

                Paragraph(
                    transaction["date_display"],
                    table_text_style
                ),
            ])

    else:

        table_data.append([
            Paragraph(
                "No transactions found for the selected report criteria.",
                table_text_style
            ),
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    transaction_table = Table(
        table_data,

        repeatRows=1,

        colWidths=[
            42 * mm,
            43 * mm,
            33 * mm,
            33 * mm,
            26 * mm,
            26 * mm,
            28 * mm,
        ],
    )

    table_styles = [

        # Header
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#1F4E78")
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),

        # Border
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.HexColor("#D1D5DB")
        ),

        # Padding
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            7
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            7
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            7
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            7
        ),

        # Header separator
        (
            "LINEBELOW",
            (0, 0),
            (-1, 0),
            0.8,
            colors.HexColor("#163A5C")
        ),
    ]

    # Alternating rows
    for row_number in range(
        1,
        len(table_data)
    ):

        if row_number % 2 == 0:

            table_styles.append(
                (
                    "BACKGROUND",
                    (0, row_number),
                    (-1, row_number),
                    colors.HexColor("#F8FAFC")
                )
            )

        else:

            table_styles.append(
                (
                    "BACKGROUND",
                    (0, row_number),
                    (-1, row_number),
                    colors.white
                )
            )

    # No transactions row
    if not transactions:

        table_styles.append(
            (
                "SPAN",
                (0, 1),
                (-1, 1)
            )
        )

        table_styles.append(
            (
                "ALIGN",
                (0, 1),
                (-1, 1),
                "CENTER"
            )
        )

    transaction_table.setStyle(
        TableStyle(table_styles)
    )

    elements.append(transaction_table)

    # =====================================================
    # END OF REPORT
    # =====================================================

    elements.append(
        Spacer(1, 18)
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=colors.HexColor("#D1D5DB"),
            spaceAfter=7,
        )
    )

    elements.append(
        Paragraph(
            "End of Report",
            small_gray_style
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    pdf.build(
        elements,

        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    # =====================================================
    # DOWNLOAD
    # =====================================================

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf",
    )