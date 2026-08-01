from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .database import db
from firebase_admin import auth, firestore
from pydantic import BaseModel
from urllib.parse import quote
from .email_service import send_password_reset_email
import os

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_DIR = os.path.join(BASE_DIR, "ui")
templates = Jinja2Templates(directory=UI_DIR)


# Roles that are allowed to self-register / use forgot-password.
# Admin is deliberately excluded — admin accounts are provisioned manually.
SELF_SERVICE_ROLES = {"job_seeker", "employer"}

# role -> Firestore collection name
ROLE_COLLECTION = {
    "job_seeker": "job_seeker",
    "employer": "company",
    "admin": "admin",
}


class LoginToken(BaseModel):
    token: str


class JobSeekerRegisterRequest(BaseModel):
    token: str
    name: str
    phone: str


class EmployerRegisterRequest(BaseModel):
    token: str

    companyName: str
    registrationNumber: str
    businessEmail: str

    phone: str
    industry: str
    companySize: str
    companyWebsite: str
    companyDescription: str

    address: str
    city: str
    state: str
    postalCode: str
    country: str

    contactFullName: str
    contactJobTitle: str
    contactDepartment: str
    contactEmail: str
    contactPhone: str
    altPhone: Optional[str] = ""

    preferredContactMethod: str
    bestTimeToContact: str
    correspondenceAddress: str


RESET_TOKEN_TTL_MINUTES = 30

ROLE_LABEL = {
    "job_seeker": "Job Seeker",
    "employer": "Employer",
    "admin": "Admin",
}


# ==============================
# Helpers
# ==============================


def _find_user_by_email(collection_name, email):
    """Return (doc_id, data_dict) for the first user with this email, or (None, None)."""
    if not email:
        return None, None

    matches = (
        db.collection(collection_name).where("email", "==", email.strip().lower()).limit(1).stream()
    )
    for doc in matches:
        return doc.id, doc.to_dict()

    return None, None


def _now_utc():
    return datetime.now(timezone.utc)


# ==============================
# LOGIN  (job_seeker / employer / admin)
# ==============================


@router.get("/login")
def login_page(request: Request):
    error = request.query_params.get("error")
    reset_success = request.query_params.get("reset") == "success"
    registered = request.query_params.get("registered") == "success"
    role = request.query_params.get("role", "job_seeker")
    if role not in ROLE_LABEL:
        role = "job_seeker"

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": error,
            "reset_success": reset_success,
            "registered": registered,
            "role": role,
            "role_label": ROLE_LABEL[role],
        },
    )


@router.post("/firebase-login")
async def firebase_login(request: Request, data: LoginToken):

    # Verify Firebase ID token
    try:
        decoded = auth.verify_id_token(data.token)
        uid = decoded["uid"]

    except Exception as e:
        return JSONResponse(status_code=401, content={"error": str(e)})

    # Job Seeker
    job = db.collection("job_seeker").document(uid).get()

    if job.exists:
        request.session["user_type"] = "job_seeker"
        request.session["applicant_id"] = uid
        return {"redirect": "/"}

    # Employer
    company = db.collection("company").document(uid).get()

    if company.exists:
        company_data = company.to_dict()
        status = company_data.get("status")

        if status in ["Pending", "Active"]:
            request.session["user_type"] = "employer"
            request.session["company_id"] = uid
            return {"redirect": "/manage-jobs"}

        elif status == "Rejected":
            return JSONResponse(
                {
                    "error": "Your company registration has been rejected. Please contact the administrator for assistance."
                },
                status_code=403,
            )

        elif status == "Deactive":
            return JSONResponse(
                {
                    "error": "Your company account has been deactivated. Please contact the administrator."
                },
                status_code=403,
            )

        else:
            return JSONResponse(
                {"error": "Your company account is not permitted to log in."},
                status_code=403,
            )

    # User exists in Firebase Authentication but not in Firestore
    return JSONResponse(
        {
            "error": "No account information was found. Please complete your registration or contact support."
        },
        status_code=404,
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ==============================
# REGISTER  (job_seeker / employer only — NOT admin)
# ==============================


@router.get("/register")
def register_page(request: Request):
    error = request.query_params.get("error")
    default_role = request.query_params.get("role", "job_seeker")

    # Employer registration is now its own multi-step wizard.
    if default_role == "employer":
        return RedirectResponse(url="/register/employer", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": error, "default_role": default_role},
    )


@router.post("/firebase-register/job-seeker")
async def firebase_register_job_seeker(data: JobSeekerRegisterRequest):

    try:

        decoded = auth.verify_id_token(data.token)

        uid = decoded["uid"]
        email = decoded["email"]

        db.collection("job_seeker").document(uid).set(
            {
                "uid": uid,
                "name": data.name,
                "email": email,
                "phone": data.phone,
                "profileImage": "",
                "status": "Active",
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
        )

        return {"success": True}

    except Exception as e:

        return JSONResponse(status_code=401, content={"error": str(e)})


@router.post("/firebase-register/employer")
async def firebase_register_employer(data: EmployerRegisterRequest):

    try:

        decoded = auth.verify_id_token(data.token)

        uid = decoded["uid"]

        email = decoded["email"]

        company_data = {
            "uid": uid,
            "email": email,
            "companyName": data.companyName,
            "registrationNumber": data.registrationNumber,
            "businessEmail": data.businessEmail,
            "phone": data.phone,
            "industry": data.industry,
            "companySize": data.companySize,
            "companyWebsite": data.companyWebsite,
            "companyDescription": data.companyDescription,
            "address": data.address,
            "city": data.city,
            "state": data.state,
            "postalCode": data.postalCode,
            "country": data.country,
            "contactPerson": {
                "fullName": data.contactFullName,
                "jobTitle": data.contactJobTitle,
                "department": data.contactDepartment,
                "email": data.contactEmail,
                "phone": data.contactPhone,
                "altPhone": data.altPhone,
                "preferredContactMethod": data.preferredContactMethod,
                "bestTimeToContact": data.bestTimeToContact,
                "correspondenceAddress": data.correspondenceAddress,
            },
            "logo": "companyLogo.png",
            "status": "Pending",
            "createdAt": firestore.SERVER_TIMESTAMP,
        }

        db.collection("company").document(uid).set(company_data)

        return {"success": True}

    except Exception as e:

        return JSONResponse(status_code=401, content={"error": str(e)})


# ==============================
# FORGOT PASSWORD  (job_seeker / employer only — NOT admin)
# ==============================


@router.get("/forgot-password")
def forgot_password_page(request: Request):
    sent = request.query_params.get("sent") == "1"
    default_role = request.query_params.get("role", "job_seeker")
    email = request.query_params.get("email", "")

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "sent": sent,
            "default_role": default_role,
            "email": email,
        },
    )


@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    role: str = Form(...),
    email: str = Form(...),
):
    if role not in SELF_SERVICE_ROLES:
        return RedirectResponse(
            url="/forgot-password?error=invalid_role",
            status_code=303,
        )

    try:
        reset_link = auth.generate_password_reset_link(email)

        display_name = "User"

        collection_name = ROLE_COLLECTION[role]

        docs = db.collection(collection_name).where("email", "==", email).limit(1).stream()

        for doc in docs:
            data = doc.to_dict()
            display_name = data.get("name") or data.get("companyName") or "User"
            break

        await send_password_reset_email(
            email=email,
            name=display_name,
            reset_link=reset_link,
        )

    except Exception as e:
        print("Forgot Password Error:", repr(e))

    return RedirectResponse(
        url=f"/forgot-password?sent=1&role={role}&email={quote(email)}",
        status_code=303,
    )


# ==============================
# EMPLOYER REGISTRATION WIZARD (4-step: company info / contact person /
# account details / review & submit) — richer data model than the
# simple job-seeker registration above.
# ==============================


@router.get("/register/employer")
def register_employer_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        request=request,
        name="employer_registration.html",
        context={"error": error},
    )


@router.get("/login/admin")
def register_admin_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": error},
    )


@router.post("/admin/firebase-login")
async def admin_firebase_login(request: Request, data: LoginToken):

    try:
        decoded = auth.verify_id_token(data.token)
        uid = decoded["uid"]

    except Exception:

        return JSONResponse({"error": "Invalid Token"}, status_code=401)

    admin = db.collection("admin").document(uid).get()

    if not admin.exists:

        return JSONResponse({"error": "Access denied."}, status_code=403)

    request.session["user_type"] = "admin"
    request.session["admin_id"] = uid

    return {"redirect": "/admin/company-requests"}


@router.get("/admin/dashboard")
def admin_dashboard(request: Request):

    if request.session.get("user_type") != "admin":
        return RedirectResponse("/login/admin", status_code=303)

    admin_id = request.session.get("admin_id")

    admin_doc = db.collection("admin").document(admin_id).get()
    admin_data = admin_doc.to_dict() if admin_doc.exists else {}

    return templates.TemplateResponse(
        request=request, name="admin_dashboard.html", context={"admin": admin_data}
    )
