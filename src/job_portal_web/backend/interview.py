from fastapi import APIRouter
from pydantic import BaseModel
from .database import db
from .email_service import send_interview_email, send_employer_interview_notification
from fastapi import HTTPException

router = APIRouter()


# ==========================
# MODEL
# ==========================


class Interview(BaseModel):

    candidateId: str  # application document ID
    companyId: str

    candidateName: str
    position: str

    stage: str
    date: str
    time: str
    duration: str

    interviewType: str

    interviewer: str
    meetingLink: str

    notes: str

    status: str = "Scheduled"


# ==========================
# CREATE INTERVIEW
# ==========================


@router.post("/api/interviews")
async def save_interview(interview: Interview):

    # Save interview
    db.collection("interviews").add(interview.dict())

    # Get application
    application_doc = db.collection("application").document(interview.candidateId).get()

    # Get company
    company_doc = db.collection("company").document(interview.companyId).get()

    if application_doc.exists and company_doc.exists:

        application = application_doc.to_dict()

        job_seeker_id = application.get("job_seeker_id")

        seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

        if seeker_doc.exists:

            seeker = seeker_doc.to_dict()

            company = company_doc.to_dict()

            await send_interview_email(
                seeker.get("email"), seeker.get("name"), interview, company.get("address")
            )

    return {"message": "Interview scheduled successfully!"}


# ==========================
# GET ALL INTERVIEWS (EMPLOYER)
# ==========================


@router.get("/api/interviews")
def get_interviews():

    interviews = []

    docs = db.collection("interviews").stream()

    for doc in docs:

        data = doc.to_dict()

        company_name = "Company"

        company_id = data.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                company = company_doc.to_dict()

                company_name = company.get("companyName", "Company")

        interviews.append(
            {
                "id": doc.id,
                "companyName": company_name,
                "candidateName": data.get("candidateName"),
                "position": data.get("position"),
                "stage": data.get("stage"),
                "date": data.get("date"),
                "time": data.get("time"),
                "duration": data.get("duration"),
                "interviewType": data.get("interviewType"),
                "interviewer": data.get("interviewer"),
                "meetingLink": data.get("meetingLink"),
                "notes": data.get("notes"),
                "status": data.get("status", "Scheduled"),
            }
        )

    return interviews


# ==========================
# GET SINGLE INTERVIEW
# ==========================


@router.get("/api/interviews/{interview_id}")
def get_interview(interview_id: str):

    doc = db.collection("interviews").document(interview_id).get()

    if not doc.exists:

        return {"error": "Interview not found"}

    data = doc.to_dict()

    data["id"] = doc.id

    company_id = data.get("companyId")

    if company_id:

        company_doc = db.collection("company").document(company_id).get()

        if company_doc.exists:

            company = company_doc.to_dict()

            data["companyName"] = company.get("companyName", "Company")

    return data


# ==========================
# CANCEL INTERVIEW
# ==========================


@router.put("/api/interviews/{interview_id}/cancel")
def cancel_interview(interview_id: str):

    db.collection("interviews").document(interview_id).update({"status": "Cancelled"})

    return {"message": "Interview cancelled successfully!"}


# ==========================
# UPDATE / RESCHEDULE
# ==========================


class InterviewUpdate(BaseModel):

    stage: str
    date: str
    time: str
    duration: str

    interviewType: str

    interviewer: str
    meetingLink: str

    notes: str

    status: str


@router.put("/api/interviews/{interview_id}")
def update_interview(interview_id: str, interview: InterviewUpdate):

    db.collection("interviews").document(interview_id).update(
        {
            "stage": interview.stage,
            "date": interview.date,
            "time": interview.time,
            "duration": interview.duration,
            "interviewType": interview.interviewType,
            "interviewer": interview.interviewer,
            "meetingLink": interview.meetingLink,
            "notes": interview.notes,
            "status": interview.status,
        }
    )

    return {"message": "Interview rescheduled successfully!"}


# ==========================
# APPLICANT VIEW INTERVIEWS
# ==========================


@router.get("/api/applicant/interviews")
def get_applicant_interviews(application_id: str):

    interviews = []

    docs = db.collection("interviews").where("candidateId", "==", application_id).stream()

    for doc in docs:

        interview = doc.to_dict()
        interview["id"] = doc.id

        company_id = interview.get("companyId")

        if company_id:

            company_doc = db.collection("company").document(company_id).get()

            if company_doc.exists:

                company_data = company_doc.to_dict()

                interview["companyName"] = company_data.get("companyName", "Company")

        interviews.append(interview)

    return interviews


# ==========================
# ACCEPT INTERVIEW
# ==========================


@router.put("/api/interviews/{interview_id}/accept")
async def accept_interview(interview_id: str):

    # Check interview exists first
    interview_doc = db.collection("interviews").document(interview_id).get()

    if not interview_doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    # Update status
    db.collection("interviews").document(interview_id).update(
        {"status": "Accepted", "applicantResponse": "Accepted"}
    )

    await notify_employer(interview_id, "Accepted")

    return {"message": "Interview accepted"}


@router.put("/api/interviews/{interview_id}/decline")
async def decline_interview(interview_id: str):

    # Check interview exists
    interview_doc = db.collection("interviews").document(interview_id).get()

    if not interview_doc.exists:

        raise HTTPException(status_code=404, detail="Interview not found")

    # Update status
    db.collection("interviews").document(interview_id).update(
        {"status": "Declined", "applicantResponse": "Declined"}
    )

    try:

        await notify_employer(interview_id, "Declined")

    except Exception as e:

        print("Email notification failed:", e)

    return {"message": "Interview declined"}


# ==========================
# REQUEST RESCHEDULE
# ==========================


class RescheduleRequest(BaseModel):

    requestedDate: str

    requestedTime: str

    reason: str


@router.put("/api/interviews/{interview_id}/reschedule-request")
async def request_reschedule(interview_id: str, request: RescheduleRequest):

    db.collection("interviews").document(interview_id).set(
        {
            "status": "Reschedule Requested",
            "rescheduleReason": request.reason,
            "requestedDate": request.requestedDate,
            "requestedTime": request.requestedTime,
        },
        merge=True,
    )

    await notify_employer(interview_id, "Reschedule Requested", request.reason)

    return {"message": "Reschedule request sent"}


async def notify_employer(interview_id, status, reason=None):

    # Get interview
    interview_doc = db.collection("interviews").document(interview_id).get()

    if not interview_doc.exists:
        return

    interview = interview_doc.to_dict()

    # Get company
    company_doc = db.collection("company").document(interview["companyId"]).get()

    if not company_doc.exists:
        return

    company = company_doc.to_dict()

    # Get employer
    employer_id = company.get("employerId")

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