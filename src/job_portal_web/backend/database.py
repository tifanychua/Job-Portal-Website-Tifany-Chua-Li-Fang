from pathlib import Path
import json
import os

import firebase_admin

from firebase_admin import credentials, firestore, storage, auth

# ==================================================
# Firebase Configuration
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

KEY_PATH = BASE_DIR / "firebase_key.json"

STORAGE_BUCKET = "job-portal-website-fc6fd.firebasestorage.app"


# ==================================================
# Firebase Credentials
# ==================================================

firebase_key = os.getenv("FIREBASE_KEY")

if firebase_key:
    # GitHub Actions / Production
    firebase_credentials = json.loads(firebase_key)

    cred = credentials.Certificate(firebase_credentials)

elif KEY_PATH.exists():
    # Local development
    cred = credentials.Certificate(str(KEY_PATH))

else:
    raise FileNotFoundError(
        "Firebase credentials not found. "
        "Please provide firebase_key.json locally "
        "or set FIREBASE_KEY environment variable."
    )


# ==================================================
# Initialize Firebase
# ==================================================

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        cred,
        {"storageBucket": STORAGE_BUCKET},
    )


# ==================================================
# Firestore Database
# ==================================================

db = firestore.client()


# ==================================================
# Firebase Storage Bucket
# ==================================================

bucket = storage.bucket()

firebase_auth = auth
