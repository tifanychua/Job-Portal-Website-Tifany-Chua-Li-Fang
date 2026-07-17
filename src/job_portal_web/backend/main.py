from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .interview import router as interview_router
from .applicant import router as applicant_router
from .chat import router as chat_router

import os

app = FastAPI()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")


print("UI PATH:", UI_DIR)

templates = Jinja2Templates(directory=UI_DIR)


app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

app.include_router(interview_router)
app.include_router(applicant_router)
app.include_router(chat_router)


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(request=request, name="home.html", context={})


@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.get("/schedule_list")
def schedule_list_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="schedule_list.html", context={"active_page": "interviews"}
    )


@app.get("/applicants")
def applicants_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="applicants.html", context={"active_page": "applicants"}
    )


@app.get("/chat")
def chat_page(request: Request, employerId: str, jobSeekerId: str):

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"active_page": "chat", "employerId": employerId, "jobSeekerId": jobSeekerId},
    )


@app.get("/interview_schedule")
def schedule_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="interview_schedule.html", context={"active_page": "applicants"}
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