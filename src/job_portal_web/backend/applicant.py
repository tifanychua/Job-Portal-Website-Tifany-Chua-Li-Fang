from fastapi import APIRouter
from .database import db

router = APIRouter()


def get_skills(skill_ids):
    """
    Retrieve skill details based on skill document IDs
    """

    skills = []

    for skill_id in skill_ids:

        skill_doc = db.collection("skills").document(skill_id).get()

        if skill_doc.exists:

            skill = skill_doc.to_dict()

            skills.append({"id": skill_id, "name": skill.get("name")})

    return skills


# Get all shortlisted applicants
@router.get("/api/applicants/shortlisted")
def get_shortlisted_candidates():

    applicants = []

    docs = db.collection("applicants").where("status", "==", "Shortlisted").stream()

    for doc in docs:

        data = doc.to_dict()

        data["id"] = doc.id

        # Get skill IDs from applicant document
        skill_ids = data.get("skills", [])

        # Convert skill IDs to skill details
        data["skills"] = get_skills(skill_ids)

        applicants.append(data)

    return applicants


# Get one shortlisted applicant
@router.get("/api/applicants/shortlisted/{id}")
def get_single_candidate(id: str):

    doc = db.collection("applicants").document(id).get()

    if not doc.exists:

        return {"error": "Applicant not found"}

    data = doc.to_dict()

    data["id"] = id

    skill_ids = data.get("skills", [])

    data["skills"] = get_skills(skill_ids)

    return data
