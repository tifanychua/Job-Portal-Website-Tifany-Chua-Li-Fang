from typing import Optional
import base64
import json
from itsdangerous import TimestampSigner
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from fastapi.responses import RedirectResponse, HTMLResponse

from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, field_validator

from .database import db

from .email_service import (
    send_interview_email,
    send_interview_cancelled_email,
    send_interview_rescheduled_email,
    send_employer_interview_notification,  # Add this line
)

router = APIRouter()


BASE_DIR = Path(__file__).resolve().parent.parent


templates = Jinja2Templates(directory=str(BASE_DIR / "ui"))


# ==================================================
# MODEL
# ==================================================


class Interview(BaseModel):

    candidateId: str

    companyId: str

    candidateName: str = ""

    position: str = ""

    stage: str

    date: str

    time: str

    duration: str

    interviewType: str

    interviewer: str

    meetingLink: str = ""

    notes: str = ""

    status: str = "Scheduled"

    @field_validator("stage", "date", "time", "duration", "interviewType", "interviewer")
    def validate_fields(cls, value):

        if not value.strip():

            raise ValueError("Field cannot be empty")

        return value


# ==================================================
# CREATE INTERVIEW
# ==================================================


@router.post("/api/interviews")
async def create_interview(interview: Interview):

    try:

        print("========== CREATE INTERVIEW ==========")

        print("Received candidateId:", interview.candidateId)

        # ==========================================
        # FIND APPLICATION RECORD
        # ==========================================

        application_doc = db.collection("applications").document(interview.candidateId).get()

        real_candidate_id = None

        if application_doc.exists:

            application = application_doc.to_dict()

            print("Application data:", application)

            real_candidate_id = application.get("job_seeker_id")

        else:

            # fallback:
            # if frontend already sends job seeker id

            seeker_doc = db.collection("job_seeker").document(interview.candidateId).get()

            if seeker_doc.exists:

                real_candidate_id = interview.candidateId

        print("Real candidate ID:", real_candidate_id)

        if not real_candidate_id:

            raise Exception("Cannot find job seeker ID")

        # ==========================================
        # GET JOB SEEKER
        # ==========================================

        seeker_doc = db.collection("job_seeker").document(real_candidate_id).get()

        print("Candidate exists:", seeker_doc.exists)

        if not seeker_doc.exists:

            raise Exception("Candidate record not found")

        seeker = seeker_doc.to_dict()

        # ==========================================
        # GET COMPANY
        # ==========================================

        company_doc = db.collection("company").document(interview.companyId).get()

        print("Company exists:", company_doc.exists)

        if not company_doc.exists:

            raise Exception("Company record not found")

        company = company_doc.to_dict()

        # ==========================================
        # SAVE INTERVIEW
        # ==========================================

        interview_data = interview.model_dump()

        # replace application id
        # with real candidate id

        interview_data["candidateId"] = real_candidate_id

        interview_data["candidateName"] = seeker.get("name", "")

        interview_ref = db.collection("interviews").add(interview_data)

        print("Interview created:", interview_ref[1].id)

        # ==========================================
        # SEND EMAIL
        # ==========================================

        candidate_email = seeker.get("email")

        print("Sending email:", candidate_email)

        await send_interview_email(
            candidate_email,
            seeker.get("name"),
            Interview(**interview_data),
            company.get("address", ""),
        )

        return {"message": "Interview scheduled successfully"}

    except Exception as e:

        print("CREATE INTERVIEW ERROR:", e)

        raise HTTPException(status_code=500, detail=str(e))


# ==================================================
# GET ALL INTERVIEWS
# ==================================================


@router.get("/api/interviews")
def get_all_interviews():

    result = []

    docs = db.collection("interviews").stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        # company details

        company_id = data.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                company = company_doc.to_dict()

                data["companyName"] = company.get("companyName", "Company")

        # candidate details

        candidate_id = data.get("candidateId")

        if candidate_id:

            seeker_doc = db.collection("job_seeker").document(candidate_id).get()

            if seeker_doc.exists:

                seeker = seeker_doc.to_dict()

                data["candidateName"] = seeker.get("name", "Applicant")

        result.append(data)

    return result


# ==================================================
# GET SINGLE INTERVIEW
# ==================================================


@router.get("/api/interviews/{interview_id}")
def get_interview(interview_id: str, request: Request):

    user_type = request.session.get("user_type")

    if user_type not in ["job_seeker", "employer"]:

        raise HTTPException(status_code=403, detail="Access denied")

    doc = db.collection("interviews").document(interview_id).get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview = doc.to_dict()

    if user_type == "employer":

        company_id = request.session.get("company_id")

        print("SESSION COMPANY ID:", company_id)

        if interview.get("companyId") != company_id:

            raise HTTPException(status_code=403, detail="Not your interview")

    elif user_type == "job_seeker":

        applicant_id = request.session.get("applicant_id")

        if interview.get("candidateId") != applicant_id:

            raise HTTPException(status_code=403, detail="Not your interview")

    interview["id"] = doc.id

    return interview


# ==================================================
# CANCEL INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}/cancel")
async def cancel_interview(interview_id: str):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview = doc.to_dict()

    interview_ref.update({"status": "Cancelled", "applicantResponse": "Cancelled"})

    try:

        seeker_doc = db.collection("job_seeker").document(interview.get("candidateId")).get()

        if seeker_doc.exists:

            seeker = seeker_doc.to_dict()

            await send_interview_cancelled_email(
                seeker.get("email"), seeker.get("name"), interview.get("position")
            )

    except Exception as e:

        print("Cancel email error:", e)

    return {"message": "Interview cancelled successfully"}


# ==================================================
# UPDATE INTERVIEW MODEL
# ==================================================


class InterviewUpdate(BaseModel):

    stage: str

    date: str

    time: str

    duration: str

    interviewType: str

    interviewer: str

    meetingLink: str = ""

    notes: str = ""

    status: str = "Scheduled"

    @field_validator("stage", "date", "time", "duration", "interviewType", "interviewer")
    def validate_update(cls, value):

        if not value.strip():

            raise ValueError("Field cannot be empty")

        return value


# ==================================================
# UPDATE / RESCHEDULE INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}")
async def update_interview(interview_id: str, interview: InterviewUpdate):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Interview not found")

    old_data = doc.to_dict()

    updated_data = {
        **old_data,
        **interview.model_dump(),
        "status": "Rescheduled",
        "applicantResponse": "Pending",
    }

    # Update interview
    interview_ref.update(
        {
            **interview.model_dump(),
            "status": "Rescheduled",
            "applicantResponse": "Pending",
        }
    )

    try:

        # ======================================
        # Get Job Seeker
        # ======================================

        candidate_id = updated_data.get("candidateId")

        seeker_id = candidate_id

        # CandidateId may be application ID
        application_doc = db.collection("application").document(candidate_id).get()

        if application_doc.exists:

            application_data = application_doc.to_dict()

            seeker_id = application_data.get("jobSeekerId", candidate_id)

        seeker_doc = db.collection("job_seeker").document(seeker_id).get()

        if seeker_doc.exists:

            seeker = seeker_doc.to_dict()

            # ======================================
            # Get Company Address
            # ======================================

            company_address = ""

            company_doc = db.collection("company").document(updated_data.get("companyId")).get()

            if company_doc.exists:

                company = company_doc.to_dict()

                company_address = company.get("address", "")

            # ======================================
            # Send Email
            # ======================================

            await send_interview_rescheduled_email(
                seeker.get("email"), seeker.get("name"), Interview(**updated_data), company_address
            )

    except Exception as e:

        print("Reschedule email error:", e)

    return {"message": "Interview updated successfully"}


# ==================================================
# APPLICANT VIEW INTERVIEWS
# ==================================================


@router.get("/api/applicant/interviews")
def get_applicant_interviews(request: Request):

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:

        raise HTTPException(status_code=401, detail="Not logged in")

    result = []

    docs = db.collection("interviews").where("candidateId", "==", applicant_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        company_id = data.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                data["companyName"] = company_doc.to_dict().get("companyName", "Company")

        result.append(data)

    return result


# ==================================================
# APPLICANT FILTER INTERVIEW
# ==================================================


@router.get("/api/applicant/interviews/filter")
def filter_applicant_interviews(request: Request, status: Optional[str] = None):

    applicant_id = request.session.get("applicant_id")

    if not applicant_id:

        raise HTTPException(status_code=401, detail="Not logged in")

    result = []

    docs = db.collection("interviews").where("candidateId", "==", applicant_id).stream()

    for doc in docs:

        data = doc.to_dict()

        if status and data.get("status") != status:

            continue

        data["id"] = doc.id

        result.append(data)

    return result


# ==================================================
# APPLICANT SEARCH INTERVIEW
# ==================================================


@router.get("/employer/interviews/search")
async def search_interview_records(request: Request, keyword: str = ""):

    # ==========================================
    # GET COMPANY SESSION
    # ==========================================

    session_cookie = request.cookies.get("session")

    if not session_cookie:

        raise HTTPException(status_code=403, detail="Access denied")

    try:

        signer = TimestampSigner("jobconnect-secret-key")

        unsigned = signer.unsign(session_cookie)

        decoded = base64.b64decode(unsigned).decode()

        session_data = json.loads(decoded)

        company_id = session_data.get("company_id")

    except Exception:

        raise HTTPException(status_code=403, detail="Access denied")

    if not company_id:

        raise HTTPException(status_code=403, detail="Access denied")

    # ==========================================
    # SEARCH INTERVIEW RECORDS
    # ==========================================

    interviews = []

    docs = db.collection("interviews").where("companyId", "==", company_id).stream()

    keyword = keyword.lower()

    for doc in docs:

        data = doc.to_dict()

        candidate_name = data.get("candidateName", "").lower()

        position = data.get("position", "").lower()

        if keyword == "" or keyword in candidate_name or keyword in position:

            interviews.append({"id": doc.id, **data})

    return interviews


# ==================================================
# EMPLOYER VIEW INTERVIEWS
# ==================================================


@router.get("/employer/interviews")
def get_employer_interviews(request: Request, status: Optional[str] = None):

    print("==============================")
    print("SESSION:")
    print(request.session)
    print("==============================")

    company_id = request.session.get("company_id")

    print("LOGIN COMPANY ID:", company_id)

    docs = db.collection("interviews").where("companyId", "==", company_id).stream()

    result = []

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        candidate_id = data.get("candidateId")

        if candidate_id:

            seeker_doc = db.collection("job_seeker").document(candidate_id).get()

            if seeker_doc.exists:

                seeker = seeker_doc.to_dict()

                data["candidateName"] = seeker.get("name", "Applicant")

        result.append(data)

    return result


# ==================================================
# EMPLOYER SEARCH INTERVIEW
# ==================================================


@router.get("/employer/interviews/search")
def search_employer_interviews(request: Request, keyword: str = ""):

    if request.session.get("user_type") != "employer":

        raise HTTPException(status_code=403, detail="Access denied")

    company_id = request.session.get("company_id")

    if not company_id:

        raise HTTPException(status_code=401, detail="Not logged in")

    keyword = keyword.lower().strip()

    result = []

    docs = db.collection("interviews").where("companyId", "==", company_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        searchable_fields = [
            data.get("candidateName", ""),
            data.get("position", ""),
            data.get("stage", ""),
            data.get("status", ""),
        ]

        if keyword:

            matched = any(keyword in str(field).lower() for field in searchable_fields)

            if not matched:

                continue

        result.append(data)

    return result


# ==================================================
# GET CURRENT USER
# ==================================================


def get_current_user(request: Request):

    user_type = request.session.get("user_type")

    if user_type == "employer":

        company_id = request.session.get("company_id")

        if company_id:

            doc = db.collection("company").document(company_id).get()

            if doc.exists:

                return doc.to_dict()

    elif user_type == "job_seeker":

        applicant_id = request.session.get("applicant_id")

        if applicant_id:

            doc = db.collection("job_seeker").document(applicant_id).get()

            if doc.exists:

                return doc.to_dict()

    return None


# ==================================================
# SCHEDULE LIST PAGE
# ==================================================


@router.get("/schedule_list", response_class=HTMLResponse)
async def schedule_list(request: Request):

    user = get_current_user(request)

    if user is None:

        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request, name="schedule_list.html", context={"request": request, "company": user}
    )


# ==================================================
# APPLICANT ACCEPT INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}/accept")
async def accept_interview(interview_id: str):
    ref = db.collection("interviews").document(interview_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Interview not found")

    interview = doc.to_dict()

    ref.update({"status": "Accepted", "applicantResponse": "Accepted"})

    try:
        # Send email to employer (existing functionality)
        company_doc = db.collection("company").document(interview.get("companyId")).get()
        if company_doc.exists:
            company = company_doc.to_dict()
            await send_employer_interview_notification(
                company.get("email"),
                company.get("companyName", "Employer"),
                interview.get("candidateName", "Applicant"),
                interview.get("position"),
                "Accepted",
            )

        # ===== NEW: Send email to candidate =====
        candidate_id = interview.get("candidateId")
        if candidate_id:
            seeker_doc = db.collection("job_seeker").document(candidate_id).get()
            if seeker_doc.exists:
                seeker = seeker_doc.to_dict()

                # Import the send_interview_acceptance_email function or create one
                from .email_service import send_interview_acceptance_email

                await send_interview_acceptance_email(
                    seeker.get("email"),
                    seeker.get("name", "Applicant"),
                    interview.get("position"),
                    company.get("companyName", "Company"),
                    interview.get("date"),
                    interview.get("time"),
                    interview.get("meetingLink", "To be provided"),
                )

    except Exception as e:
        print("Accept email error:", e)

    return {"message": "Interview accepted"}


# ==================================================
# APPLICANT DECLINE INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}/decline")
async def decline_interview(interview_id: str):

    ref = db.collection("interviews").document(interview_id)

    doc = ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview = doc.to_dict()

    ref.update({"status": "Declined", "applicantResponse": "Declined"})

    try:

        company_doc = db.collection("company").document(interview.get("companyId")).get()

        if company_doc.exists:

            company = company_doc.to_dict()

            await send_employer_interview_notification(
                company.get("email"),
                company.get("companyName", "Employer"),
                interview.get("candidateName", "Applicant"),
                interview.get("position"),
                "Declined",
            )

    except Exception as e:

        print("Decline email error:", e)

    return {"message": "Interview declined"}


class RescheduleRequest(BaseModel):

    requestedDate: str

    requestedTime: str

    reason: str

    # ==================================================


# APPLICANT REQUEST RESCHEDULE
# ==================================================


@router.put("/api/interviews/{interview_id}/reschedule-request")
async def reschedule_request(interview_id: str, request_data: RescheduleRequest):

    ref = db.collection("interviews").document(interview_id)

    doc = ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview = doc.to_dict()

    ref.update(
        {
            "status": "Reschedule Requested",
            "applicantResponse": "Reschedule Requested",
            "requestedDate": request_data.requestedDate,
            "requestedTime": request_data.requestedTime,
            "rescheduleReason": request_data.reason,
        }
    )

    try:

        company_doc = db.collection("company").document(interview.get("companyId")).get()

        if company_doc.exists:

            company = company_doc.to_dict()

            await send_employer_interview_notification(
                company.get("email"),
                company.get("companyName", "Employer"),
                interview.get("candidateName", "Applicant"),
                interview.get("position"),
                "Reschedule Requested",
                request_data.reason,
                request_data.requestedDate,
                request_data.requestedTime,
            )

    except Exception as e:

        print("Reschedule email error:", e)

    return {"message": "Reschedule request sent"}


# ==================================================
# APPLICANT SEARCH INTERVIEW
# ==================================================


@router.get("/api/applicant/interviews/search")
def search_applicant_interviews(request: Request, application_id: str, keyword: str = ""):

    # Get applicant session
    applicant_id = request.session.get("applicant_id")

    # For testing allow application_id
    if not applicant_id:
        applicant_id = application_id

    if not applicant_id:

        raise HTTPException(status_code=401, detail="Not logged in")

    keyword = keyword.lower().strip()

    result = []

    docs = db.collection("interviews").where("candidateId", "==", applicant_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        searchable_fields = [
            data.get("candidateName", ""),
            data.get("position", ""),
            data.get("status", ""),
            data.get("stage", ""),
        ]

        if keyword:

            matched = any(keyword in str(field).lower() for field in searchable_fields)

            if not matched:

                continue

        result.append(data)

    if len(result) == 0:

        return {"message": "No interview records found"}

    return result


# ==================================================
# INTERVIEW MANAGEMENT PAGE
# ==================================================


@router.get("/interview_schedule", response_class=HTMLResponse)
async def interview_schedule(request: Request, applicationId: str):

    user = get_current_user(request)

    if user is None:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="interview_schedule.html",
        context={
            "request": request,
            "applicationId": applicationId,
            "companyId": request.session.get("company_id"),
            "company": user,
        },
    )
