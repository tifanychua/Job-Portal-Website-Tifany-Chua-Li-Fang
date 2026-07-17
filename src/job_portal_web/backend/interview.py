from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from .database import db
from .email_service import send_interview_email, send_employer_interview_notification

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
def cancel_interview(interview_id: str):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview_ref.update({"status": "Cancelled"})

    return {"message": "Interview cancelled successfully!"}


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
def update_interview(interview_id: str, interview: InterviewUpdate):

    interview_ref = db.collection("interviews").document(interview_id)

    doc = interview_ref.get()

    if not doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    interview_ref.update(interview.model_dump())

    return {"message": "Interview rescheduled successfully!"}


# ==================================================
# APPLICANT VIEW
# ==================================================


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
