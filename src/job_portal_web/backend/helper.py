from .database import db


def get_company():

    company_id = "C000001"

    company_doc = db.collection("company").document(company_id).get()

    if company_doc.exists:
        return company_doc.to_dict()

    return {}
