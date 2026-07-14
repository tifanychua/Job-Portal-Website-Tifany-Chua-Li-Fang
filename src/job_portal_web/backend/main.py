from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from interview import router as interview_router
from applicant import router as applicant_router
from jobs import router as jobs_router
from homepage import router as home_router
from job_information import router as job_information_router
from job_apply import router as job_apply_router
from job_application import router as job_application_router

import os

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="jobconnect-secret-key")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UI_DIR = os.path.join(BASE_DIR, "ui")

print("UI PATH:", UI_DIR)


templates = Jinja2Templates(directory=UI_DIR)


app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

app.mount("/image", StaticFiles(directory="src/job_portal_web/image"), name="image")

app.include_router(home_router)
app.include_router(interview_router)
app.include_router(applicant_router)
app.include_router(jobs_router)
app.include_router(job_information_router)
app.include_router(job_apply_router)
app.include_router(job_application_router)


"""
@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={}
    )


@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


@app.get("/schedule_list")
def schedule_list_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="schedule_list.html",
        context={
            "active_page": "interviews"
        }
    )


@app.get("/applicants")
def applicants_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="applicants.html",
        context={
            "active_page": "applicants"
        }
    )


@app.get("/interview_schedule")
def schedule_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="interview_schedule.html",
        context={
            "active_page": "applicants"
        }
    )
"""

# print(app.routes)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
