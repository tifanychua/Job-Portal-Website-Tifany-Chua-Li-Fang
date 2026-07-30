from datetime import datetime
from typing import Annotated
import re

from fastapi import (
    APIRouter,
    Request,
    Form,
    UploadFile,
    File,
    HTTPException
)
from fastapi.responses import (
    RedirectResponse,
    HTMLResponse,
    JSONResponse
)
from fastapi.templating import Jinja2Templates
from firebase_admin import firestore
from job_portal_web.backend.database import bucket
import uuid
router = APIRouter()

templates = Jinja2Templates(
    directory="src/job_portal_web/ui"
)

db = firestore.client()

# =====================================================
# Temporary Company ID
# =====================================================

COMPANY_ID = "8r1bqsSUA8SqEsjlUr1tFyLtaOW2"


# =====================================================
# Edit Company Profile
# =====================================================

@router.get(
    "/edit-company-profile",
    response_class=HTMLResponse
)
async def edit_company_profile(request: Request):

    company_doc = (
        db.collection("company")
        .document(COMPANY_ID)
        .get()
    )

    if company_doc.exists:
        company = company_doc.to_dict()
        company.setdefault("specialty_category_ids", [])
    else:
        company = {
            "specialty_category_ids": []
        }

    industries = [
        doc.to_dict()
        for doc in db.collection("industries")
        .order_by("industry_name")
        .stream()
    ]

    selected_industry = company.get("industry_id")

    categories = []

    docs = db.collection("skill_categories").stream()

    for doc in docs:

        category = doc.to_dict()

        if (
            not selected_industry
            or category.get("industry_id") == selected_industry
        ):
            categories.append(category)

    categories.sort(
        key=lambda x: x.get("category_name", "")
    )

    return templates.TemplateResponse(
        request=request,
        name="editCompanyProfile.html",
        context={
            "company": company,
            "industries": industries,
            "categories": categories
        }
    )


# =====================================================
# Get Specialties by Industry
# =====================================================

@router.get("/industry-specialties")
async def get_industry_specialties(industry_id: str):

    categories = []

    docs = db.collection("skill_categories").stream()

    for doc in docs:

        category = doc.to_dict()

        if category.get("industry_id") == industry_id:

            categories.append(category)

    categories.sort(
        key=lambda x: x.get("category_name", "")
    )

    return JSONResponse(categories)

# =====================================================
# Update Company Profile
# =====================================================
def return_error(
    request,
    company_data,
    industries,
    categories,
    message
):
    return templates.TemplateResponse(
        request=request,
        name="editCompanyProfile.html",
        context={
            "company": company_data,
            "industries": industries,
            "categories": categories,
            "error": message
        },
        status_code=400
    )

@router.post("/update-company-profile")
async def update_company_profile(

    request: Request,

    companyName: str = Form(...),
    registrationNumber: str = Form(...),
    businessEmail: str = Form(...),
    phone: str = Form(...),
    companyWebsite: str = Form(""),
    foundedYear: int = Form(...),
    companySize: str = Form(""),
    country: str = Form(""),
    companyType: str = Form(...),
    address: str = Form(...),
    address_line2: str = Form(""),
    city: str = Form(...),
    state: str = Form(...),
    postalCode: str = Form(...),
    industry_id: str = Form(...),
    specialty_category_ids: list[str] = Form(...),
    companyDescription: str = Form(...),
    logo: UploadFile | None = File(None)

):


    current_year = datetime.now().year

    industries = [
        doc.to_dict()
        for doc in db.collection("industries")
        .order_by("industry_name")
        .stream()
    ]

    categories = []

    docs = db.collection("skill_categories").stream()

    for doc in docs:

        category = doc.to_dict()

        if category.get("industry_id") == industry_id:
            categories.append(category)

    categories.sort(
        key=lambda x: x.get("category_name", "")
    )

    company = {
        "companyName": companyName,
        "registrationNumber": registrationNumber,
        "businessEmail": businessEmail,
        "phone": phone,
        "companyWebsite": companyWebsite,
        "foundedYear": foundedYear,
        "companySize": companySize,
        "companyType": companyType,
        "address": address,
        "address_line2": address_line2,
        "city": city,
        "state": state,
        "postalCode": postalCode,
        "country": country,
        "industry_id": industry_id,
        "specialty_category_ids": specialty_category_ids,
        "companyDescription": companyDescription
    }

    if not companySize:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Please select a company size."
        )

    if not country:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Please select a country."
        )

    if foundedYear < 1800 or foundedYear > current_year:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Invalid founded year."
        )

    if foundedYear < 1800 or foundedYear > current_year:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Invalid founded year."
        )

    phone_pattern = r"^\+60\s\d{1,2}-\d{7,8}$"

    if not re.match(phone_pattern, phone):
        return return_error(
            request,
            company,
            industries,
            categories,
            "Please enter a valid phone number. Example: +60 11-12345678."
        )

    specialty_category_ids = list(dict.fromkeys(specialty_category_ids))

    if len(specialty_category_ids) == 0:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Please select at least one company specialty."
        )

    if len(specialty_category_ids) > 6:
        return return_error(
            request,
            company,
            industries,
            categories,
            "Maximum 6 company specialties allowed."
        )

    company_data = {
        "companyName": companyName.strip(),
        "registrationNumber": registrationNumber.strip(),
        "businessEmail": businessEmail.strip(),
        "phone": phone.strip(),
        "companyWebsite": companyWebsite.strip(),
        "foundedYear": foundedYear,
        "companySize": companySize,
        "companyType": companyType,
        "address": address.strip(),
        "address_line2": address_line2.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "postalCode": postalCode,
        "country": country,
        "industry_id": industry_id,
        "specialty_category_ids": specialty_category_ids,
        "companyDescription": companyDescription.strip(),
        "updatedAt": firestore.SERVER_TIMESTAMP
    }

    if logo and logo.filename:

        allowed_types = [
            "image/png",
            "image/jpeg",
            "image/jpg"
        ]

        if logo.content_type not in allowed_types:
            return return_error(
                request,
                company,
                industries,
                categories,
                "Only PNG and JPG images are allowed."
            )

        extension = logo.filename.rsplit(".", 1)[-1]

        filename = (
            f"profile_images/"
            f"{COMPANY_ID}_{uuid.uuid4()}.{extension}"
        )

        blob = bucket.blob(filename)

        blob.upload_from_file(
            logo.file,
            content_type=logo.content_type
        )

        blob.make_public()

        company_data["logo"] = blob.public_url

    db.collection("company").document(COMPANY_ID).set(
        company_data,
        merge=True
    )

    return RedirectResponse(
        url="/company-profile",
        status_code=303
    )
