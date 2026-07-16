import os

import firebase_admin
from firebase_admin import credentials, firestore, storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


firebase_key_path = os.path.join(BASE_DIR, "firebase_key.json")


cred = credentials.Certificate(firebase_key_path)


if not firebase_admin._apps:

    firebase_admin.initialize_app(
        cred, {"storageBucket": "job-portal-website-fc6fd.firebasestorage.app"}
    )


db = firestore.client()


bucket = storage.bucket()
