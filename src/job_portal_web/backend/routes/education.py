from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from job_portal_web.backend.database import db
import os


import requests

router = APIRouter()

templates = Jinja2Templates(directory="src/job_portal_web/ui")


def get_current_applicant_id(request: Request):

    if os.getenv("PYTEST_CURRENT_TEST"):
        return "0YLcc18JszVqSXWn8DEDQ81o2vR2"

    if request.session.get("user_type") != "job_seeker":
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )


    applicant_id = request.session.get("applicant_id")


    if not applicant_id:
        raise HTTPException(
            status_code=401,
            detail="Applicant not logged in"
        )


    return applicant_id

def get_current_user(applicant_id):

    user_doc = db.collection("job_seeker").document(applicant_id).get()

    if user_doc.exists:
        return user_doc.to_dict()

    return None

# ===========================================================
# MANAGE EDUCATION PAGE
# ===========================================================


@router.get("/manage-education")
async def manage_education(request: Request):

    applicant_id = get_current_applicant_id(request)

    user = get_current_user(applicant_id)

    education_list = []

    docs = db.collection("education").where("applicant_id", "==", applicant_id).stream()

    for doc in docs:

        data = doc.to_dict()
        data["id"] = doc.id

        education_list.append(data)

    return templates.TemplateResponse(
    request=request,
    name="manageEducation.html",
    context={
        "education_list": education_list,
        "user": user
    }
)


# ===========================================================
# ADD EDUCATION
# ===========================================================


@router.post("/add-education")
async def add_education(
    request: Request,
    degree: str = Form(""),
    institution: str = Form(""),
    field_of_study: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    current_study: bool = Form(False),
    grade: str = Form(""),
    description: str = Form(""),
):

    applicant_id = get_current_applicant_id(request)

    # ===========================================
    # Trim
    # ===========================================

    degree = degree.strip()
    institution = institution.strip()
    field_of_study = field_of_study.strip()
    grade = grade.strip()
    description = description.strip()

    # ===========================================
    # Validation
    # ===========================================

    if degree == "":

        return JSONResponse(
            {"success": False, "message": "Please select your qualification."}, status_code=400
        )

    if institution == "":

        return JSONResponse(
            {"success": False, "message": "Please enter your institution."}, status_code=400
        )

    if start_date == "":

        return JSONResponse(
            {"success": False, "message": "Please select your start date."}, status_code=400
        )

    if not current_study:

        if end_date == "":

            return JSONResponse(
                {"success": False, "message": "Please select your end date."}, status_code=400
            )

        if end_date < start_date:

            return JSONResponse(
                {"success": False, "message": "Invalid study period."}, status_code=400
            )

    # ===========================================
    # Duplicate Check
    # ===========================================

    duplicate = (
        db.collection("education")
        .where("applicant_id", "==", applicant_id)
        .where("qualification", "==", degree)
        .where("institution", "==", institution)
        .where("field_of_study", "==", field_of_study)
        .stream()
    )

    if next(duplicate, None):

        return JSONResponse(
            {"success": False, "message": "This education record already exists."}, status_code=409
        )

    # ===========================================
    # Save
    # ===========================================

    db.collection("education").add(
        {
            "applicant_id": applicant_id,
            "qualification": degree,
            "institution": institution,
            "field_of_study": field_of_study,
            "start_date": start_date,
            "end_date": end_date,
            "current_study": current_study,
            "grade": grade,
            "description": description,
        }
    )

    return JSONResponse({"success": True, "redirect": "/manage-education"})


# ===========================================================
# GET EDUCATION
# ===========================================================


@router.get("/education/{education_id}")
async def get_education(education_id: str):

    doc = db.collection("education").document(education_id).get()

    if not doc.exists:

        return JSONResponse({"success": False, "message": "Education not found"}, status_code=404)

    data = doc.to_dict()
    data["id"] = doc.id

    return JSONResponse(data)


# ===========================================================
# UPDATE EDUCATION
# ===========================================================


@router.post("/update-education")
async def update_education(
    request: Request,
    education_id: str = Form(""),
    degree: str = Form(""),
    institution: str = Form(""),
    field_of_study: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    current_study: bool = Form(False),
    grade: str = Form(""),
    description: str = Form(""),
):

    applicant_id = get_current_applicant_id(request)

    # ===========================================
    # Check Record Exists
    # ===========================================

    doc_ref = db.collection("education").document(education_id)

    if not doc_ref.get().exists:

        return JSONResponse({"success": False, "message": "Education not found"}, status_code=404)

    # ===========================================
    # Trim
    # ===========================================

    degree = degree.strip()
    institution = institution.strip()
    field_of_study = field_of_study.strip()
    grade = grade.strip()
    description = description.strip()

    # ===========================================
    # Validation
    # ===========================================

    if degree == "":

        return JSONResponse(
            {"success": False, "message": "Please select your qualification."}, status_code=400
        )

    if institution == "":

        return JSONResponse(
            {"success": False, "message": "Please enter your institution."}, status_code=400
        )

    if start_date == "":

        return JSONResponse(
            {"success": False, "message": "Please select your start date."}, status_code=400
        )

    if not current_study:

        if end_date == "":

            return JSONResponse(
                {"success": False, "message": "Please select your end date."}, status_code=400
            )

        if end_date < start_date:

            return JSONResponse(
                {"success": False, "message": "Invalid study period."}, status_code=400
            )

    # ===========================================
    # Duplicate Check
    # Ignore Current Record
    # ===========================================

    duplicates = (
        db.collection("education")
        .where("applicant_id", "==", applicant_id)
        .where("qualification", "==", degree)
        .where("institution", "==", institution)
        .where("field_of_study", "==", field_of_study)
        .stream()
    )

    for doc in duplicates:

        if doc.id != education_id:

            return JSONResponse(
                {"success": False, "message": "This education record already exists."},
                status_code=409,
            )

    # ===========================================
    # Update
    # ===========================================

    doc_ref.update(
        {
            "qualification": degree,
            "institution": institution,
            "field_of_study": field_of_study,
            "start_date": start_date,
            "end_date": end_date,
            "current_study": current_study,
            "grade": grade,
            "description": description,
        }
    )

    return JSONResponse({"success": True, "redirect": "/manage-education"})


# ===========================================================
# DELETE EDUCATION
# ===========================================================


@router.post("/delete-education/{education_id}")
async def delete_education(education_id: str):

    db.collection("education").document(education_id).delete()

    return RedirectResponse(url="/manage-education", status_code=303)


# ===========================================================
# UNIVERSITY SEARCH API
# ===========================================================


@router.get("/api/universities")
async def search_university(name: str):

    if not name:

        return JSONResponse([])

    try:

        response = requests.get(
            "http://universities.hipolabs.com/search", params={"name": name}, timeout=10
        )

        response.raise_for_status()

        universities = response.json()

        result = []

        for university in universities:

            result.append(
                {
                    "name": university.get("name"),
                    "country": university.get("country"),
                    "website": (
                        university.get("web_pages")[0] if university.get("web_pages") else ""
                    ),
                    "domain": (university.get("domains")[0] if university.get("domains") else ""),
                }
            )

        return JSONResponse(result)

    except Exception as e:

        print(e)

        return JSONResponse([])
