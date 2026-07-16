from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from database import db
from encryption import encrypt_message, decrypt_message

router = APIRouter()


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
