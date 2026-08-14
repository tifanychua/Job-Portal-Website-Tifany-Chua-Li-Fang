import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from job_portal_web.backend.routes.education import router as education_router
from job_portal_web.backend.routes.experience import router as experience_router

from .admin_users import router as admin_users_router
from .applicant import router as applicant_router

# Routers
from .auth import router as auth_router
from .career_advice import router as career_advice_router
from .chat import router as chat_router
from .database import db
from .helper import get_company
from .homepage import router as home_router
from .interview import router as interview_router
from .job_application import router as job_application_router
from .job_apply import router as job_apply_router
from .job_information import router as job_information_router
from .jobs import router as jobs_router
from .messages import router as messages_router
from .notifications import get_unread_notifications_count
from .notifications import router as notifications_router
from .routes.admin import router as admin_router
from .routes.adminAnalytics import router as admin_analytics_router
from .routes.adminTransaction import router as admin_transaction_router
from .routes.companyBrowse import router as company_browse_router
from .routes.companyDetails import router as company_details_router
from .routes.companyProfile import router as companyProfile_router
from .routes.editCompanyProfile import router as editCompanyProfile_router
from .routes.editProfile import router as editProfile_router
from .routes.employer import router as employer_router
from .routes.employerApplication import router as employer_application_router
from .routes.employerCredit import router as employer_credit_router
from .routes.employerPlans import router as employer_plans_router
from .routes.employerTransactions import router as employer_transactions_router
from .routes.jobSeekerProfile import router as jobSeekerProfile_router
from .routes.payment import router as payment_router
from .routes.skill import router as skill_router
from .routes.stripePayment import router as stripe_payment_router
from .routes.writeCompanyReview import router as write_company_review_router
from .saved_job import router as saved_jobs_router

# ==================================================
# APP
# ==================================================

app = FastAPI()


# ==================================================
# SESSION
# ==================================================

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "jobconnect-secret-key"))


# ==================================================
# PATH
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UI_DIR = BASE_DIR / "ui"


# ==================================================
# TEMPLATE
# ==================================================

templates = Jinja2Templates(directory=str(UI_DIR))


# ==================================================
# GET CURRENT USER
# ==================================================


def get_current_user(request: Request):

    user_type = request.session.get("user_type")

    # Job seeker
    if user_type == "job_seeker":
        user_id = request.session.get("applicant_id")

        if user_id:
            doc = db.collection("job_seeker").document(user_id).get()

            if doc.exists:
                return doc.to_dict()

    # Employer
    elif user_type == "employer":
        company_id = request.session.get("company_id")

        if company_id:
            doc = db.collection("company").document(company_id).get()

            if doc.exists:
                return doc.to_dict()

    return None


# ==================================================
# STATIC
# ==================================================

app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


app.mount("/image", StaticFiles(directory=str(BASE_DIR / "image")), name="image")


app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")


app.mount("/css", StaticFiles(directory=str(BASE_DIR / "css")), name="css")


app.mount("/js", StaticFiles(directory=str(BASE_DIR / "js")), name="js")


# ==================================================
# ROUTERS
# ==================================================

app.include_router(home_router)

app.include_router(auth_router)

app.include_router(interview_router)

app.include_router(applicant_router)

app.include_router(chat_router)

app.include_router(messages_router)

app.include_router(jobs_router)

app.include_router(job_information_router)

app.include_router(job_apply_router)

app.include_router(job_application_router)

app.include_router(editProfile_router)

app.include_router(jobSeekerProfile_router)

app.include_router(employer_router)

app.include_router(employer_application_router)

app.include_router(admin_router)

app.include_router(education_router)

app.include_router(experience_router)

app.include_router(companyProfile_router)

app.include_router(skill_router)

app.include_router(editCompanyProfile_router)

# Career advice feature
app.include_router(career_advice_router)

app.include_router(education_router)

app.include_router(experience_router)

app.include_router(companyProfile_router)

app.include_router(skill_router)

app.include_router(editCompanyProfile_router)

app.include_router(admin_users_router)
app.include_router(saved_jobs_router)
app.include_router(employer_credit_router)

app.include_router(payment_router)

app.include_router(company_browse_router)

app.include_router(company_details_router)

app.include_router(write_company_review_router)

app.include_router(notifications_router)

app.include_router(admin_transaction_router)

app.include_router(employer_plans_router)

app.include_router(stripe_payment_router)

app.include_router(employer_transactions_router)

app.include_router(admin_analytics_router)
# ==================================================
# TEMPLATE HELPER
# ==================================================


def render_template(request: Request, template: str, context=None):

    if context is None:
        context = {}

    # Current user
    user = get_current_user(request)
    context["user"] = user

    # Employer information
    if request.session.get("user_type") == "employer":
        company = get_company(request)
        context["company"] = company

    # Live unread notification badge
    context.setdefault("unread_notifications_count", get_unread_notifications_count(request))

    return templates.TemplateResponse(request=request, name=template, context=context)


# ==================================================
# PAGE ROUTES
# ==================================================


@app.get("/home")
def home(request: Request):

    return render_template(request, "home.html")


# ==================================================
# MESSAGES PAGE
# ==================================================


@app.get("/messages")
def messages_page(request: Request):

    user_type = request.session.get("user_type")

    if not user_type:
        return RedirectResponse("/login", status_code=303)

    if user_type == "employer":
        user_id = request.session.get("company_id")

    elif user_type == "job_seeker":
        user_id = request.session.get("applicant_id")

    else:
        raise HTTPException(status_code=403, detail="Invalid user type")

    return render_template(
        request,
        "messages.html",
        {
            "active_page": "messages",
            "user_type": user_type,
            "userId": user_id,
            "userType": user_type,
        },
    )


# ==================================================
# CHAT PAGE
# ==================================================


@app.get("/chat")
def chat_page(request: Request):

    employer_id = request.query_params.get("employerId")

    job_seeker_id = request.query_params.get("jobSeekerId")

    sender_id = request.query_params.get("senderId")

    sender_type = request.query_params.get("senderType")

    # IMPORTANT:
    # Do not convert employer -> company
    # because template checks employer

    return render_template(
        request,
        "chat.html",
        {
            "user_type": sender_type,
            "employerId": employer_id,
            "jobSeekerId": job_seeker_id,
            "senderId": sender_id,
            "senderType": sender_type,
        },
    )


# ==================================================
# JOB SEEKER INTERVIEW PAGE
# ==================================================


@app.get("/my_interviews")
def my_interviews_page(request: Request):

    if request.session.get("user_type") != "job_seeker":
        return RedirectResponse("/login", status_code=303)

    return render_template(request, "applicant_interview.html", {"active_page": "interviews"})


@app.get("/my_interviews/detail/{interview_id}")
async def interview_detail_page(request: Request, interview_id: str):
    return render_template(
        request, "applicant_interview_detail.html", {"interview_id": interview_id}
    )


@app.get("/schedule_list")
def schedule_list_page(request: Request):

    if request.session.get("user_type") != "employer":
        return RedirectResponse("/login", status_code=303)

    return render_template(request, "schedule_list.html", {"active_page": "schedule_list"})


@app.get("/login")
def login_page(request: Request):
    return render_template(request, "login.html")


@app.get("/career-advice")
def view_career_advice(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="jobSeekerCareerAdvice.html",
        context={"request": request},
    )


@app.get("/about-us", response_class=HTMLResponse)
def about_us_page(request: Request):
    user = None
    unread_notifications_count = 0

    if request.session.get("user_type") == "job_seeker":
        applicant_id = request.session.get("applicant_id")

        if applicant_id:
            user_document = db.collection("job_seeker").document(str(applicant_id)).get()

            if user_document.exists:
                user = user_document.to_dict() or {}
                user["applicant_id"] = applicant_id

                unread_notifications_count = get_unread_notifications_count(request)

    return templates.TemplateResponse(
        request=request,
        name="aboutUs.html",
        context={
            "request": request,
            "user": user,
            "active_page": "about-us",
            "unread_notifications_count": (unread_notifications_count),
        },
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
