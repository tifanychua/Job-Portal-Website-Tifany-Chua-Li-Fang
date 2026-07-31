from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .database import db
from .encryption import decrypt_message

router = APIRouter()


# ==========================
# Get Conversation List API
# ==========================


@router.get("/api/conversations")
def get_conversations(request: Request):

    conversations = []

    # ==========================
    # Get logged-in user
    # ==========================

    user_type = request.session.get("user_type")
    print("USER TYPE:", user_type)
    print("SESSION:", request.session)
    if not user_type:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    if user_type == "employer":
        user_id = request.session.get("company_id")

    elif user_type == "job_seeker":
        user_id = request.session.get("applicant_id")

    else:
        return JSONResponse({"error": "Invalid user type"}, status_code=403)

    if not user_id:
        return JSONResponse({"error": "User ID missing"}, status_code=401)

    # ==========================
    # Get messages
    # ==========================

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
        # Check ownership
        # ==========================

        if user_type == "employer":

            if employer_id != user_id:
                continue

        else:

            if job_seeker_id != user_id:
                continue

        # ==========================
        # Decrypt message
        # ==========================

        encrypted_message = data.get("message")

        try:
            last_message = decrypt_message(encrypted_message)

        except Exception:
            last_message = encrypted_message

        # ==========================
        # Get other person's name
        # ==========================

        if user_type == "employer":

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
                "senderId": user_id,
                "senderType": user_type,
            }
        )

    return conversations
