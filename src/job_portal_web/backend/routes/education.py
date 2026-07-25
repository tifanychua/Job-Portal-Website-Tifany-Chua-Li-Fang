from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from job_portal_web.backend.database import db

import requests

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")


# ===========================================================
# MANAGE EDUCATION PAGE
# ===========================================================

@router.get("/manage-education")
async def manage_education(request: Request):

    applicant_id = "applicant001"

    education_list = []

    docs = (
        db.collection("education")
        .where("applicant_id", "==", applicant_id)
        .stream()
    )

    for doc in docs:

        data = doc.to_dict()
        data["id"] = doc.id

        education_list.append(data)

    return templates.TemplateResponse(
        request=request,
        name="manageEducation.html",
        context={
            "education_list": education_list
        }
    )


# ===========================================================
# ADD EDUCATION
# ===========================================================

@router.post("/add-education")
async def add_education(

    degree: str = Form(...),
    institution: str = Form(...),
    field_of_study: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    current_study: bool = Form(False),
    grade: str = Form(""),
    description: str = Form("")

):

    applicant_id = "applicant001"

    db.collection("education").add({

        "applicant_id": applicant_id,
        "qualification": degree,
        "institution": institution,
        "field_of_study": field_of_study,
        "start_date": start_date,
        "end_date": end_date,
        "current_study": current_study,
        "grade": grade,
        "description": description

    })

    return RedirectResponse(
        url="/manage-education",
        status_code=303
    )


# ===========================================================
# GET EDUCATION
# ===========================================================

@router.get("/education/{education_id}")
async def get_education(education_id: str):

    doc = db.collection("education").document(education_id).get()

    if not doc.exists:

        return JSONResponse(
            {
                "success": False,
                "message": "Education not found"
            },
            status_code=404
        )

    data = doc.to_dict()
    data["id"] = doc.id

    return JSONResponse(data)


# ===========================================================
# UPDATE EDUCATION
# ===========================================================

@router.post("/update-education")
async def update_education(

    education_id: str = Form(...),

    degree: str = Form(...),
    institution: str = Form(...),
    field_of_study: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    current_study: bool = Form(False),
    grade: str = Form(""),
    description: str = Form("")

):

    doc_ref = db.collection("education").document(education_id)

    if not doc_ref.get().exists:

        return JSONResponse(
            {
                "success": False,
                "message": "Education not found"
            },
            status_code=404
        )

    doc_ref.update({

        "qualification": degree,
        "institution": institution,
        "field_of_study": field_of_study,
        "start_date": start_date,
        "end_date": end_date,
        "current_study": current_study,
        "grade": grade,
        "description": description

    })

    return RedirectResponse(
        url="/manage-education",
        status_code=303
    )


# ===========================================================
# DELETE EDUCATION
# ===========================================================

@router.post("/delete-education/{education_id}")
async def delete_education(education_id: str):

    db.collection("education").document(education_id).delete()

    return RedirectResponse(
        url="/manage-education",
        status_code=303
    )


# ===========================================================
# UNIVERSITY SEARCH API
# ===========================================================

@router.get("/api/universities")
async def search_university(name: str):

    if not name:

        return JSONResponse([])

    try:

        response = requests.get(
            "http://universities.hipolabs.com/search",
            params={
                "name": name
            },
            timeout=10
        )

        response.raise_for_status()

        universities = response.json()

        result = []

        for university in universities:

            result.append({

                "name": university.get("name"),

                "country": university.get("country"),

                "website": (
                    university.get("web_pages")[0]
                    if university.get("web_pages")
                    else ""
                ),

                "domain": (
                    university.get("domains")[0]
                    if university.get("domains")
                    else ""
                )

            })

        return JSONResponse(result)

    except Exception as e:

        print(e)

        return JSONResponse([])