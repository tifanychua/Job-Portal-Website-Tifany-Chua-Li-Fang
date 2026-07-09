from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from interview import router as interview_router
from applicant import router as applicant_router

import os

app = FastAPI()


# ==========================
# PATH
# ==========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")


print("UI PATH:", UI_DIR)


# ==========================
# JINJA
# ==========================

templates = Jinja2Templates(directory=UI_DIR)


# ==========================
# STATIC
# ==========================

app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


# ==========================
# ROUTERS
# ==========================

app.include_router(interview_router)
app.include_router(applicant_router)


# ==========================
# PAGES
# ==========================


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


@app.get("/interview_schedule")
def schedule_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="interview_schedule.html", context={"active_page": "applicants"}
    )
