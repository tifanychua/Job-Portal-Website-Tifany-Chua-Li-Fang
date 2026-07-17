from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# ==============================
# Routers
# ==============================

from .interview import router as interview_router
from .applicant import router as applicant_router
from .chat import router as chat_router

from .jobs import router as jobs_router
from .homepage import router as home_router
from .job_information import router as job_information_router
from .job_apply import router as job_apply_router
from .job_application import router as job_application_router

from .routes.employer import router as employer_router
from .routes.employerApplication import router as employer_application_router
from .database import db

app = FastAPI()


# ==============================
# Session
# ==============================

app.add_middleware(SessionMiddleware, secret_key="jobconnect-secret-key")


# ==============================
# Base Directory
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent

UI_DIR = BASE_DIR / "ui"

IMAGE_DIR = BASE_DIR / "image"

print("UI PATH:", UI_DIR)


# ==============================
# Templates
# ==============================

templates = Jinja2Templates(directory=str(UI_DIR))


# ==============================
# Static Files
# ==============================

# CSS / JS / HTML static
# ==============================
# Static Files
# ==============================

# CSS / JS / HTML static
app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


# Images folder: /image/xxx.png
app.mount("/image", StaticFiles(directory=str(BASE_DIR / "image")), name="image")


# Images folder: /images/xxx.png
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")


# CSS folder
app.mount("/css", StaticFiles(directory=str(BASE_DIR / "css")), name="css")


# ==============================
# Include Routers
# ==============================

# General pages
app.include_router(home_router)

# Interview
app.include_router(interview_router)

# Applicant
app.include_router(applicant_router)

# Chat
app.include_router(chat_router)

# Jobs
app.include_router(jobs_router)

# Job information
app.include_router(job_information_router)

# Job application
app.include_router(job_apply_router)

app.include_router(job_application_router)


# Employer
app.include_router(employer_router)

app.include_router(employer_application_router)


# ==============================
# Page Routes
# ==============================


@app.get("/home")
def home(request: Request):

    return templates.TemplateResponse(request=request, name="home.html", context={})


@app.get("/schedule_list")
def schedule_list_page(request: Request):

    company_doc = db.collection("company").document("C000001").get()

    company = {}

    if company_doc.exists:
        company = company_doc.to_dict()

    return templates.TemplateResponse(
        request=request,
        name="schedule_list.html",
        context={"active_page": "interviews", "company": company},
    )


@app.get("/applicants")
def applicants_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="applicants.html", context={"active_page": "applicants"}
    )


@app.get("/chat")
def chat_page(request: Request):

    employerId = request.query_params.get("employerId")
    jobSeekerId = request.query_params.get("jobSeekerId")
    senderType = request.query_params.get("senderType")

    company = None
    job_seeker = None

    if senderType == "employer":

        user_type = "company"

        # Get company data
        company_doc = db.collection("company").document(employerId).get()

        if company_doc.exists:
            company = company_doc.to_dict()
        else:
            company = {"companyName": "Company", "companyLogo": "companyLogo.png"}

    else:

        user_type = "job_seeker"

        # Get job seeker data if header needs it
        applicant_doc = db.collection("job_seeker").document(jobSeekerId).get()

        if applicant_doc.exists:
            job_seeker = applicant_doc.to_dict()
        else:
            job_seeker = {"name": "User", "profileImage": "user.png"}

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "active_page": "chat",
            "employerId": employerId,
            "jobSeekerId": jobSeekerId,
            "user_type": user_type,
            # always send these
            "company": company,
            "job_seeker": job_seeker,
        },
    )


@app.get("/interview_schedule")
def schedule_page(request: Request):

    company_doc = db.collection("company").document("C000001").get()

    company = {}

    if company_doc.exists:
        company = company_doc.to_dict()

    return templates.TemplateResponse(
        request=request,
        name="interview_schedule.html",
        context={"active_page": "applicants", "company": company},
    )


@app.get("/my_interviews/{application_id}")
def my_interviews_page(request: Request, application_id: str):

    return templates.TemplateResponse(
        request=request,
        name="applicant_interview.html",
        context={"active_page": "interviews", "application_id": application_id},
    )


@app.get("/my_interviews/detail/{interview_id}")
def my_interview_detail_page(request: Request, interview_id: str):

    return templates.TemplateResponse(
        request=request,
        name="applicant_interview_detail.html",
        context={"active_page": "interviews", "interview_id": interview_id},
    )


@app.get("/messages")
def messages_page(request: Request):

    userId = request.query_params.get("userId")
    userType = request.query_params.get("userType")

    if userType == "employer":

        page_type = "company"

    else:

        page_type = "job_seeker"

    return templates.TemplateResponse(
        request=request,
        name="messages.html",
        context={
            "active_page": "messages",
            "user_type": page_type,
            "userId": userId,
            "userType": userType,
        },
    )


# ==============================
# Run
# ==============================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
