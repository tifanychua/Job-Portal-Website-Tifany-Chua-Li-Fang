from fastapi import APIRouter
from pydantic import BaseModel
from .database import db
from .email_service import send_interview_email

router = APIRouter()


class Interview(BaseModel):
    candidateId: str
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


@router.post("/api/interviews")
async def save_interview(interview: Interview):

    # Save interview
    db.collection("interviews").add(interview.dict())

    # Get applicant
    applicant_doc = db.collection("applicants").document(interview.candidateId).get()

    # Get company
    company_doc = db.collection("company").document(interview.companyId).get()

    if applicant_doc.exists and company_doc.exists:

        applicant = applicant_doc.to_dict()

        company = company_doc.to_dict()

        await send_interview_email(
            applicant.get("email"), applicant.get("name"), interview, company.get("address")
        )

    return {"message": "Interview scheduled successfully!"}


@router.get("/api/interviews")
def get_interviews():

    interviews = []

    docs = db.collection("interviews").stream()

    for doc in docs:

        data = doc.to_dict()

        interviews.append(
            {
                "id": doc.id,
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
            }
        )

    return interviews
