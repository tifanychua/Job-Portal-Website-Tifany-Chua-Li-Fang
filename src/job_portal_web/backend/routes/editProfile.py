from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UI_DIR = BASE_DIR / "ui"

templates = Jinja2Templates(directory=str(UI_DIR))


@router.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile(request: Request):
    return templates.TemplateResponse(
        request=request, name="edit_jobSeeker_profile.html", context={}
    )
