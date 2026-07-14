from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore, storage

BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR / "firebase_key.json"

cred = credentials.Certificate(str(KEY_PATH))

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        cred, {"storageBucket": "job-portal-website-fc6fd.firebasestorage.app"}
    )
db = firestore.client()
bucket = storage.bucket()
