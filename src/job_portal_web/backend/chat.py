from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from .database import db
from .encryption import encrypt_message, decrypt_message

router = APIRouter()


# ==========================
# Message Model
# ==========================


class Message(BaseModel):

    conversationId: str
    senderId: str
    senderType: str
    message: str


# ==========================
# Get Messages
# ==========================


@router.get("/api/messages/{conversation_id}")
def get_messages(conversation_id: str):

    messages = []

    docs = db.collection("messages").where("conversationId", "==", conversation_id).stream()

    for doc in docs:

        data = doc.to_dict()

        encrypted_text = data.get("message")

        decrypted_text = decrypt_message(encrypted_text)

        messages.append(
            {
                "id": doc.id,
                "senderId": data.get("senderId"),
                "senderType": data.get("senderType"),
                "message": decrypted_text,
                "time": data.get("time"),
            }
        )

    return messages


# ==========================
# Send Message
# ==========================


@router.post("/api/messages")
def send_message(message: Message):

    encrypted_text = encrypt_message(message.message)

    data = {
        "conversationId": message.conversationId,
        "senderId": message.senderId,
        "senderType": message.senderType,
        "message": encrypted_text,
        "time": datetime.now().isoformat(),
    }

    db.collection("messages").add(data)

    return {"message": "Message sent successfully"}


# ==========================
# Get Chat Information
# ==========================


@router.get("/api/chat/info/{employer_id}/{job_seeker_id}")
def get_chat_info(employer_id: str, job_seeker_id: str, senderType: str):

    # Job seeker chatting with employer
    if senderType == "job_seeker":

        company_doc = db.collection("company").document(employer_id).get()

        if company_doc.exists:

            company = company_doc.to_dict()

            return {
                "name": company.get("companyName", "Company"),
                "position": "Employer",
                "image": "company.png",
            }

    # Employer chatting with job seeker
    else:

        seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

        if seeker_doc.exists:

            seeker = seeker_doc.to_dict()

            return {
                "name": seeker.get("name", "Job Seeker"),
                "position": "Applicant",
                "image": "avatar.jpg",
            }

    return {"name": "Unknown User", "position": "", "image": "avatar.jpg"}