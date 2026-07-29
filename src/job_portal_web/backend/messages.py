from fastapi import APIRouter, Query

from .database import db
from .encryption import decrypt_message

router = APIRouter()


# ==========================
# Get Conversation List API
# ==========================


@router.get("/api/conversations")
def get_conversations(userId: str = Query(...), userType: str = Query(...)):

    conversations = []

    docs = db.collection("messages").order_by("time", direction="DESCENDING").stream()

    checked = set()

    for doc in docs:

        data = doc.to_dict()

        conversation_id = data.get("conversationId")

        if not conversation_id:
            continue

        if conversation_id in checked:
            continue

        checked.add(conversation_id)

        ids = conversation_id.split("_")

        if len(ids) != 2:
            continue

        employer_id = ids[0]

        job_seeker_id = ids[1]

        # ==========================
        # IMPORTANT FIX
        # ==========================

        if userType == "employer":

            if employer_id != userId:
                continue

        else:

            if job_seeker_id != userId:
                continue

        encrypted_message = data.get("message")

        try:

            last_message = decrypt_message(encrypted_message)

        except Exception:

            last_message = encrypted_message

        if userType == "employer":

            seeker_doc = db.collection("job_seeker").document(job_seeker_id).get()

            if seeker_doc.exists:

                name = seeker_doc.to_dict().get("name", "Job Seeker")

            else:

                name = "Job Seeker"

        else:

            company_doc = db.collection("company").document(employer_id).get()

            if company_doc.exists:

                name = company_doc.to_dict().get("companyName", "Company")

            else:

                name = "Company"

        conversations.append(
            {
                "conversationId": conversation_id,
                "name": name,
                "lastMessage": last_message,
                "time": data.get("time"),
                "employerId": employer_id,
                "jobSeekerId": job_seeker_id,
                "senderId": userId,
                "senderType": userType,
            }
        )

    return conversations
