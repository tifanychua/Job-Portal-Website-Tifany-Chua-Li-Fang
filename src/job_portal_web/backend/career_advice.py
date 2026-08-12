from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from firebase_admin import storage
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from job_portal_web.backend.database import db

router = APIRouter()

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
TEMPLATE_DIRECTORY = PROJECT_DIRECTORY / "ui"
templates = Jinja2Templates(directory=str(TEMPLATE_DIRECTORY))

COLLECTION_NAME = "career_advice"
SAVED_COLLECTION_NAME = "saved_career_advice"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class CareerAdvicePayload(BaseModel):
    title: str = ""
    category: str = ""
    summary: str = ""
    content: str = ""
    imageUrl: str = ""
    action: Literal["draft", "publish"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_admin(request: Request) -> bool:
    role = request.session.get("user_type") or request.session.get("userType")
    return str(role or "").lower() == "admin"


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Administrator access is required.")


def admin_id(request: Request):
    return (
        request.session.get("admin_id")
        or request.session.get("user_id")
        or request.session.get("userId")
    )


def is_job_seeker(request: Request) -> bool:
    role = request.session.get("user_type") or request.session.get("userType")
    normalized_role = str(role or "").strip().lower().replace("-", "_").replace(" ", "_")
    return normalized_role in {"job_seeker", "jobseeker"}


def job_seeker_id(request: Request):
    if not is_job_seeker(request):
        return None

    return (
        request.session.get("applicant_id")
        or request.session.get("job_seeker_id")
        or request.session.get("user_id")
        or request.session.get("userId")
    )


def get_current_job_seeker(request: Request):
    """Get the logged-in job seeker's Firestore profile for the shared header."""
    seeker_id = job_seeker_id(request)
    if not seeker_id:
        return None

    seeker_document = db.collection("job_seeker").document(str(seeker_id)).get()

    if not seeker_document.exists:
        return None

    user = seeker_document.to_dict() or {}
    user["id"] = seeker_document.id
    return user


def require_job_seeker(request: Request) -> str:
    seeker_id = job_seeker_id(request)
    if not seeker_id:
        raise HTTPException(
            status_code=401,
            detail="Please log in as a job seeker to save career advice.",
        )
    return str(seeker_id)


def saved_article_document_id(seeker_id: str, post_id: str) -> str:
    value = f"{seeker_id}:{post_id}".encode("utf-8")
    return sha256(value).hexdigest()


def get_saved_article_reference(seeker_id: str, post_id: str):
    document_id = saved_article_document_id(seeker_id, post_id)
    return db.collection(SAVED_COLLECTION_NAME).document(document_id)


def get_saved_article_ids(seeker_id: str | None) -> set[str]:
    if not seeker_id:
        return set()

    snapshots = (
        db.collection(SAVED_COLLECTION_NAME).where("jobSeekerId", "==", str(seeker_id)).stream()
    )

    saved_ids = set()
    for snapshot in snapshots:
        record = snapshot.to_dict() or {}
        career_advice_id = record.get("careerAdviceId")
        if career_advice_id:
            saved_ids.add(str(career_advice_id))

    return saved_ids


def clean_payload(payload: CareerAdvicePayload) -> dict:
    return {
        "title": payload.title.strip(),
        "category": payload.category.strip(),
        "summary": payload.summary.strip(),
        "content": payload.content.strip(),
        "imageUrl": payload.imageUrl.strip(),
    }


def validate_post(data: dict, publishing: bool) -> None:
    errors = []

    if not data["title"]:
        errors.append("Title is required.")
    elif len(data["title"]) > 150:
        errors.append("Title cannot exceed 150 characters.")

    if len(data["category"]) > 80:
        errors.append("Category cannot exceed 80 characters.")

    if len(data["summary"]) > 300:
        errors.append("Summary cannot exceed 300 characters.")

    image_url = data.get("imageUrl", "")
    if image_url and not image_url.startswith("https://firebasestorage.googleapis.com/"):
        errors.append("The cover image URL is invalid.")

    if publishing:
        if not data["category"]:
            errors.append("Category is required before publishing.")
        if not data["summary"]:
            errors.append("Summary is required before publishing.")
        if not data["content"]:
            errors.append("Content is required before publishing.")
        elif len(data["content"]) < 50:
            errors.append("Content must contain at least 50 characters.")

    if errors:
        raise HTTPException(status_code=422, detail=errors)


def snapshot_to_dict(snapshot) -> dict:
    post = snapshot.to_dict() or {}
    post["id"] = snapshot.id
    return post


def timestamp_number(value) -> float:
    try:
        return value.timestamp()
    except (AttributeError, TypeError, ValueError):
        return 0.0


def get_post_snapshot(post_id: str):
    snapshot = db.collection(COLLECTION_NAME).document(post_id).get()
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Career advice post not found.")
    return snapshot


@router.get(
    "/admin/career-advice",
    response_class=HTMLResponse,
)
def admin_career_advice_page(
    request: Request,
):
    if not is_admin(request):

        return RedirectResponse(
            "/login/admin",
            status_code=303,
        )

    snapshots = db.collection(COLLECTION_NAME).stream()

    all_posts = [snapshot_to_dict(snapshot) for snapshot in snapshots]

    # Main admin page only displays published posts.
    published_posts = [post for post in all_posts if post.get("status") == "Published"]

    # Used for the Saved Drafts counter.
    draft_posts = [post for post in all_posts if post.get("status") == "Draft"]

    published_posts.sort(
        key=lambda post: timestamp_number(post.get("publicationDate")),
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="careerAdvice.html",
        context={
            "posts": published_posts,
            "draft_count": len(draft_posts),
            "active_page": "career_advice",
        },
    )


@router.get(
    "/admin/career-advice/drafts",
    response_class=HTMLResponse,
)
def saved_career_advice_drafts_page(
    request: Request,
):
    if not is_admin(request):

        return RedirectResponse(
            "/login/admin",
            status_code=303,
        )

    snapshots = db.collection(COLLECTION_NAME).stream()

    drafts = []

    for snapshot in snapshots:

        post = snapshot_to_dict(snapshot)

        if post.get("status") == "Draft":

            drafts.append(post)

    drafts.sort(
        key=lambda post: timestamp_number(post.get("updatedAt")),
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="careerAdviceDrafts.html",
        context={
            "drafts": drafts,
            "active_page": "career_advice",
        },
    )


@router.delete("/api/admin/career-advice/{post_id}")
def delete_career_advice_post(
    post_id: str,
    request: Request,
):
    require_admin(request)

    snapshot = get_post_snapshot(post_id)

    post = snapshot.to_dict() or {}

    image_url = str(post.get("imageUrl", "")).strip()

    # Delete the Firestore post.
    snapshot.reference.delete()

    # Delete the cover image from Firebase Storage.
    if image_url:

        try:

            from urllib.parse import (
                unquote,
                urlparse,
            )

            parsed_url = urlparse(image_url)

            if "/o/" in parsed_url.path:

                encoded_storage_path = parsed_url.path.split(
                    "/o/",
                    1,
                )[1]

                storage_path = unquote(encoded_storage_path)

                storage.bucket().blob(storage_path).delete()

        except Exception as error:

            # The post is already deleted.
            # Only report the failed image cleanup in the log.
            print(
                "Career advice image cleanup error:",
                error,
            )

    return {
        "success": True,
        "message": ("Career advice post deleted successfully."),
    }


@router.get("/admin/career-advice/create", response_class=HTMLResponse)
def create_career_advice_page(request: Request):
    if not is_admin(request):
        return RedirectResponse("/login/admin", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="careerAdviceForm.html",
        context={"post": None, "active_page": "career_advice"},
    )


@router.get("/admin/career-advice/{post_id}/edit", response_class=HTMLResponse)
def edit_career_advice_page(request: Request, post_id: str):
    if not is_admin(request):
        return RedirectResponse("/login", status_code=303)

    post = snapshot_to_dict(get_post_snapshot(post_id))
    return templates.TemplateResponse(
        request=request,
        name="careerAdviceForm.html",
        context={"post": post, "active_page": "career_advice"},
    )


@router.post("/api/admin/career-advice/upload-image")
async def upload_career_advice_image(
    request: Request,
    image: UploadFile = File(...),
):
    require_admin(request)

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=422,
            detail="Only JPG, PNG and WebP images are allowed.",
        )

    image_bytes = await image.read()
    await image.close()

    if not image_bytes:
        raise HTTPException(status_code=422, detail="The selected image is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=422, detail="Image size cannot exceed 5 MB.")

    try:
        uploaded_image = Image.open(BytesIO(image_bytes))
        uploaded_image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=422, detail="The file is not a valid image.")

    extension = ALLOWED_IMAGE_TYPES[image.content_type]
    storage_path = f"career_advice_images/{uuid4()}.{extension}"
    download_token = str(uuid4())

    bucket = storage.bucket()
    blob = bucket.blob(storage_path)
    blob.metadata = {"firebaseStorageDownloadTokens": download_token}
    blob.upload_from_string(image_bytes, content_type=image.content_type)

    encoded_path = quote(storage_path, safe="")
    image_url = (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/"
        f"{encoded_path}?alt=media&token={download_token}"
    )

    return {"success": True, "imageUrl": image_url}


@router.post("/api/admin/career-advice")
def create_career_advice(
    payload: CareerAdvicePayload,
    request: Request,
):
    require_admin(request)
    data = clean_payload(payload)
    publishing = payload.action == "publish"
    validate_post(data, publishing)

    current_time = now_utc()
    document = db.collection(COLLECTION_NAME).document()
    record = {
        **data,
        "status": "Published" if publishing else "Draft",
        "createdAt": current_time,
        "updatedAt": current_time,
        "publicationDate": current_time if publishing else None,
        "createdBy": admin_id(request),
        "updatedBy": admin_id(request),
    }
    document.set(record)

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "id": document.id,
            "status": record["status"],
            "message": (
                "Career advice post published successfully."
                if publishing
                else "Career advice draft saved successfully."
            ),
        },
    )


@router.put("/api/admin/career-advice/{post_id}")
def update_career_advice(
    post_id: str,
    payload: CareerAdvicePayload,
    request: Request,
):
    require_admin(request)

    # Retrieve the existing post.
    snapshot = get_post_snapshot(post_id)

    existing_post = snapshot.to_dict() or {}

    # Clean the submitted values.
    data = clean_payload(payload)

    publishing = payload.action == "publish"

    # A published post cannot return to Draft.
    if existing_post.get("status") == "Published" and payload.action == "draft":
        raise HTTPException(
            status_code=409,
            detail=("A published post cannot be changed " "back to Draft."),
        )

    # Validate all required publication fields.
    validate_post(
        data,
        publishing,
    )

    current_time = now_utc()

    update_data = {
        **data,
        "status": ("Published" if publishing else "Draft"),
        "updatedAt": current_time,
        "updatedBy": admin_id(request),
    }

    # Record publication date only the first time
    # that the post is published.
    if publishing and not existing_post.get("publicationDate"):
        update_data["publicationDate"] = current_time

    snapshot.reference.update(update_data)

    return {
        "success": True,
        "status": update_data["status"],
        "message": (
            "Career advice post updated successfully."
            if existing_post.get("status") == "Published"
            else (
                "Career advice post published successfully."
                if publishing
                else "Career advice draft updated successfully."
            )
        ),
    }


@router.post("/api/admin/career-advice/{post_id}/publish")
def publish_career_advice_draft(post_id: str, request: Request):
    require_admin(request)
    snapshot = get_post_snapshot(post_id)
    post = snapshot.to_dict() or {}

    if post.get("status") == "Published":
        raise HTTPException(status_code=409, detail="This post is already published.")

    post_data = {
        "title": str(post.get("title", "")).strip(),
        "category": str(post.get("category", "")).strip(),
        "summary": str(post.get("summary", "")).strip(),
        "content": str(post.get("content", "")).strip(),
        "imageUrl": str(post.get("imageUrl", "")).strip(),
    }
    validate_post(post_data, publishing=True)

    current_time = now_utc()
    snapshot.reference.update(
        {
            "status": "Published",
            "publicationDate": current_time,
            "updatedAt": current_time,
            "updatedBy": admin_id(request),
        }
    )
    return {"success": True, "message": "Draft published successfully."}


@router.post("/api/career-advice/{post_id}/save")
def save_career_advice(post_id: str, request: Request):
    seeker_id = require_job_seeker(request)
    post_snapshot = get_post_snapshot(post_id)
    post = post_snapshot.to_dict() or {}

    if post.get("status") != "Published":
        raise HTTPException(
            status_code=404,
            detail="Career advice post not found.",
        )

    saved_reference = get_saved_article_reference(seeker_id, post_id)
    if saved_reference.get().exists:
        return {
            "success": True,
            "saved": True,
            "message": "Career advice is already saved.",
        }

    saved_reference.set(
        {
            "jobSeekerId": seeker_id,
            "careerAdviceId": post_id,
            "savedAt": now_utc(),
        }
    )

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "saved": True,
            "message": "Career advice saved successfully.",
        },
    )


@router.delete("/api/career-advice/{post_id}/save")
def remove_saved_career_advice(post_id: str, request: Request):
    seeker_id = require_job_seeker(request)
    saved_reference = get_saved_article_reference(seeker_id, post_id)

    # Firestore delete is idempotent, so repeated requests remain safe.
    saved_reference.delete()

    return {
        "success": True,
        "saved": False,
        "message": "Career advice removed from saved articles.",
    }


@router.get("/career-advice", response_class=HTMLResponse)
def published_career_advice_page(request: Request):
    user = get_current_job_seeker(request)

    snapshots = db.collection(COLLECTION_NAME).where("status", "==", "Published").stream()
    posts = [snapshot_to_dict(snapshot) for snapshot in snapshots]
    posts.sort(
        key=lambda post: timestamp_number(post.get("publicationDate")),
        reverse=True,
    )

    saved_ids = get_saved_article_ids(job_seeker_id(request))
    for post in posts:
        post["is_saved"] = post["id"] in saved_ids

    return templates.TemplateResponse(
        request=request,
        name="jobSeekerCareerAdvice.html",
        context={
            "user": user,
            "posts": posts,
            "active_page": "career_advice",
        },
    )


@router.get("/job-seeker/career-advice/{post_id}")
def job_seeker_view_career_advice(
    request: Request,
    post_id: str,
):
    user = get_current_job_seeker(request)

    post_document = db.collection("career_advice").document(post_id).get()

    if not post_document.exists:
        raise HTTPException(
            status_code=404,
            detail="Career advice not found",
        )

    post = post_document.to_dict()
    post["id"] = post_document.id

    # Job seekers should only access published articles
    if post.get("status") != "Published":
        raise HTTPException(
            status_code=404,
            detail="Career advice not found",
        )

    seeker_id = job_seeker_id(request)
    post["is_saved"] = bool(
        seeker_id and get_saved_article_reference(str(seeker_id), post_id).get().exists
    )

    return templates.TemplateResponse(
        request=request,
        name="jobSeekerCareerAdviceDetails.html",
        context={
            "user": user,
            "post": post,
            "active_page": "career_advice",
        },
    )


@router.get("/career-advice/{post_id}", response_class=HTMLResponse)
def career_advice_details_page(request: Request, post_id: str):
    user = get_current_job_seeker(request)

    post = snapshot_to_dict(get_post_snapshot(post_id))
    if post.get("status") != "Published":
        raise HTTPException(status_code=404, detail="Career advice post not found.")

    seeker_id = job_seeker_id(request)
    post["is_saved"] = bool(
        seeker_id and get_saved_article_reference(str(seeker_id), post_id).get().exists
    )

    return templates.TemplateResponse(
        request=request,
        name="careerAdviceDetails.html",
        context={
            "user": user,
            "post": post,
            "active_page": "career_advice",
        },
    )
