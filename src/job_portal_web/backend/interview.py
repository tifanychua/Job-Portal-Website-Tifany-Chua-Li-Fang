from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from .database import db
from typing import Optional
from .email_service import (
    send_interview_email,
    send_employer_interview_notification,
    send_interview_cancelled_email,
    send_interview_rescheduled_email,
)

router = APIRouter()


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
    def validate_required_fields(cls, value):

        if not value.strip():
            raise ValueError("Field cannot be empty")

        return value


# ==================================================
# CREATE INTERVIEW
# ==================================================


@router.post("/api/interviews")
async def save_interview(interview: Interview):

    try:

        db.collection("interviews").add(interview.model_dump())

        application_doc = db.collection("application").document(interview.candidateId).get()

        company_doc = db.collection("company").document(interview.companyId).get()

        if application_doc.exists and company_doc.exists:

            application = application_doc.to_dict()

            job_seeker_id = application.get("job_seeker_id") or application.get("jobSeekerId")

            if job_seeker_id:

                seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

                if seeker_doc.exists:

                    seeker = seeker_doc.to_dict()

                    company = company_doc.to_dict()

                    await send_interview_email(
                        seeker.get("email"), seeker.get("name"), interview, company.get("address")
                    )

        return {"message": "Interview scheduled successfully!"}

    except Exception as e:

        print("Interview error:", e)

        raise HTTPException(status_code=500, detail=str(e))


# ==================================================
# GET ALL INTERVIEWS
# ==================================================


@router.get("/api/interviews")
def get_interviews():

    result = []

    docs = db.collection("interviews").stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        company_name = "Company"

        company_id = data.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                company = company_doc.to_dict()

                company_name = company.get("companyName", "Company")

        data["companyName"] = company_name

        result.append(data)

    return result


# ==================================================
# GET SINGLE INTERVIEW
# ==================================================


@router.get("/api/interviews/{interview_id}")
def get_interview(interview_id: str):

    doc = db.collection("interviews").document(interview_id).get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    data = doc.to_dict()

    data["id"] = doc.id

    return data


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

    # Update interview status
    interview_ref.update({"status": "Cancelled"})

    print("Interview cancelled:", interview_id)

    try:

        # Get application
        application_doc = db.collection("application").document(interview.get("candidateId")).get()

        print("Application exists:", application_doc.exists)

        if application_doc.exists:

            application = application_doc.to_dict()

            print("Application data:", application)

            job_seeker_id = application.get("job_seeker_id") or application.get("jobSeekerId")

            print("Job seeker ID:", job_seeker_id)

            if job_seeker_id:

                seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

                print("Seeker exists:", seeker_doc.exists)

                if seeker_doc.exists:

                    seeker = seeker_doc.to_dict()

                    print("Seeker data:", seeker)

                    print("Sending cancel email to:", seeker.get("email"))

                    await send_interview_cancelled_email(
                        seeker.get("email"), seeker.get("name"), interview.get("position")
                    )

                    print("Cancel email sent successfully")

    except Exception as e:

        print("Cancel email error:", e)

    return {"message": "Interview cancelled and email sent"}


# ==================================================
# UPDATE / RESCHEDULE INTERVIEW
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
    def validate_update_fields(cls, value):

        if not value.strip():

            raise ValueError("Field cannot be empty")

        return value


@router.put("/api/interviews/{interview_id}")
async def update_interview(interview_id: str, interview: InterviewUpdate):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    old_interview = doc.to_dict()

    # Update Firestore
    interview_ref.update(interview.model_dump())

    # Merge old + new data
    updated_interview = {**old_interview, **interview.model_dump()}

    try:

        # Find application
        application_doc = (
            db.collection("application").document(updated_interview.get("candidateId")).get()
        )

        print("Application exists:", application_doc.exists)

        if application_doc.exists:

            application = application_doc.to_dict()

            job_seeker_id = application.get("job_seeker_id") or application.get("jobSeekerId")

            print("Job seeker ID:", job_seeker_id)

            if job_seeker_id:

                seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

                print("Seeker exists:", seeker_doc.exists)

                if seeker_doc.exists:

                    seeker = seeker_doc.to_dict()

                    company_address = ""

                    company_doc = (
                        db.collection("company").document(updated_interview.get("companyId")).get()
                    )

                    if company_doc.exists:

                        company = company_doc.to_dict()

                        company_address = company.get("address", "")

                    print("Sending reschedule email to:", seeker.get("email"))

                    await send_interview_rescheduled_email(
                        seeker.get("email"),
                        seeker.get("name"),
                        Interview(**updated_interview),
                        company_address,
                    )

                    print("Reschedule email sent")

    except Exception as e:

        print("Reschedule email error:", e)

    return {"message": "Interview rescheduled successfully!"}


@router.get("/api/applicant/interviews")
def get_applicant_interviews(application_id: str):

    result = []

    docs = db.collection("interviews").where("candidateId", "==", application_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        company_name = "Company"

        company_id = data.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                company = company_doc.to_dict()

                company_name = company.get("companyName", "Company")

        data["companyName"] = company_name

        result.append(data)

    return result


# ==================================================
# ACCEPT INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}/accept")
async def accept_interview(interview_id: str):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview_ref.update({"status": "Accepted", "applicantResponse": "Accepted"})

    await notify_employer(interview_id, "Accepted")

    return {"message": "Interview accepted"}


# ==================================================
# DECLINE INTERVIEW
# ==================================================


@router.put("/api/interviews/{interview_id}/decline")
async def decline_interview(interview_id: str):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview_ref.update({"status": "Declined", "applicantResponse": "Declined"})

    await notify_employer(interview_id, "Declined")

    return {"message": "Interview declined"}


# ==================================================
# RESCHEDULE REQUEST
# ==================================================


class RescheduleRequest(BaseModel):

    requestedDate: str

    requestedTime: str

    reason: str

    @field_validator("requestedDate", "requestedTime", "reason")
    def validate_request_fields(cls, value):

        if not value.strip():

            raise ValueError("Field cannot be empty")

        return value


@router.put("/api/interviews/{interview_id}/reschedule-request")
async def request_reschedule(interview_id: str, request: RescheduleRequest):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview_ref.update(
        {
            "status": "Reschedule Requested",
            "rescheduleReason": request.reason,
            "requestedDate": request.requestedDate,
            "requestedTime": request.requestedTime,
        }
    )

    await notify_employer(interview_id, "Reschedule Requested", request.reason)

    return {"message": "Reschedule request sent"}


# ==================================================
# EMPLOYER NOTIFICATION
# ==================================================


async def notify_employer(interview_id, status, reason=None):

    doc = db.collection("interviews").document(interview_id).get()

    if not doc.exists:
        return

    interview = doc.to_dict()

    company_doc = db.collection("company").document(interview["companyId"]).get()

    if not company_doc.exists:
        return

    company = company_doc.to_dict()

    employer_id = company.get("employerId")

    if not employer_id:
        return

    employer_doc = db.collection("employers").document(employer_id).get()

    if not employer_doc.exists:
        return

    employer = employer_doc.to_dict()

    await send_employer_interview_notification(
        employer.get("email"),
        employer.get("name"),
        interview.get("candidateName"),
        interview.get("position"),
        status,
        reason,
        interview.get("requestedDate"),
        interview.get("requestedTime"),
    )


# ==================================================
# EMPLOYER VIEW INTERVIEW RECORDS WITH STATUS FILTER
# ==================================================


@router.get("/employer/interviews")
def get_employer_interviews(status: Optional[str] = None):

    result = []

    docs = db.collection("interviews").stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        # Filter by status

        if status:

            if data.get("status") != status:

                continue

        result.append(data)

    if status and len(result) == 0:

        return {"message": "No interview records found", "data": []}

    return result


# ==================================================
# EMPLOYER SEARCH INTERVIEW RECORDS
# ==================================================


@router.get("/employer/interviews/search")
def search_employer_interviews(keyword: str = ""):

    result = []

    docs = db.collection("interviews").stream()

    keyword = keyword.lower().strip()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        # If keyword exists, search relevant fields

        if keyword:

            searchable_fields = [
                data.get("candidateName", ""),
                data.get("position", ""),
                data.get("status", ""),
                data.get("candidateId", ""),
            ]

            matched = any(keyword in str(field).lower() for field in searchable_fields)

            if not matched:

                continue

        result.append(data)

    if keyword and len(result) == 0:

        return {"message": "No interview records found", "data": []}

    return result



# ==================================================
# JOB SEEKER FILTER INTERVIEW RECORDS BY STATUS
# ==================================================


@router.get("/api/applicant/interviews/filter")
def filter_applicant_interviews(application_id: str, status: Optional[str] = None):

    result = []

    docs = db.collection("interviews").where("candidateId", "==", application_id).stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        if status:

            if data.get("status") != status:

                continue

        result.append(data)

    if status and len(result) == 0:

        return {"message": "No interview records found", "data": []}

    return result


# ==================================================
# JOB SEEKER SEARCH INTERVIEW RECORDS
# ==================================================


@router.get("/api/applicant/interviews/search")
def search_applicant_interviews(application_id: str, keyword: str = ""):

    result = []

    docs = db.collection("interviews").where("candidateId", "==", application_id).stream()

    keyword = keyword.lower().strip()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        # Search all relevant fields

        if keyword:

            searchable_fields = [
                data.get("candidateName", ""),
                data.get("position", ""),
                data.get("status", ""),
                data.get("interviewer", ""),
                data.get("stage", ""),
            ]

            matched = any(keyword in str(field).lower() for field in searchable_fields)

            if not matched:

                continue

        result.append(data)

    # No result

    if keyword and len(result) == 0:

        return {"message": "No interview records found", "data": []}

    return result
