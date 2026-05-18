import os
import uuid
import logging

from django.core.files.storage import default_storage
from django.conf import settings

from core.services.firebase_admin import firebase_admin_missing_settings, get_firebase_admin_app

logger = logging.getLogger("core")


def tangred_private_media_backend() -> str:
    configured_backend = getattr(settings, "TANGRED_PRIVATE_MEDIA_BACKEND", "auto").strip().lower()
    if configured_backend in {"database", "local", "firebase"}:
        return configured_backend

    missing = firebase_admin_missing_settings()
    if not missing:
        return "firebase"
    return "database"


def save_session_photo(*, uploaded_file, session) -> dict:
    extension = os.path.splitext(uploaded_file.name or "")[1].lower() or ".jpg"
    file_name = f"tangred/{session.user_id}/{session.id}/{uuid.uuid4().hex}{extension}"
    content_type = getattr(uploaded_file, "content_type", "") or "application/octet-stream"
    size_bytes = getattr(uploaded_file, "size", 0) or 0
    backend = tangred_private_media_backend()

    if backend == "firebase":
        try:
            from firebase_admin import storage

            app = get_firebase_admin_app()
            bucket = storage.bucket(app=app)
            blob = bucket.blob(file_name)
            uploaded_file.seek(0)
            blob.cache_control = "private, max-age=0, no-transform"
            blob.upload_from_file(uploaded_file, content_type=content_type)
            return {
                "backend": "firebase",
                "storage_path": file_name,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "original_name": uploaded_file.name,
                "image_name": "",
                "binary_content": None,
            }
        except Exception as exc:
            logger.warning("Tangred photo upload fell back to database storage: %s", exc)
            uploaded_file.seek(0)
            backend = "database"

    if backend == "database":
        uploaded_file.seek(0)
        return {
            "backend": "database",
            "storage_path": file_name,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "original_name": uploaded_file.name,
            "image_name": "",
            "binary_content": uploaded_file.read(),
        }

    saved_name = default_storage.save(file_name, uploaded_file)
    return {
        "backend": "local",
        "storage_path": saved_name,
        "content_type": content_type,
        "size_bytes": size_bytes,
        "original_name": uploaded_file.name,
        "image_name": saved_name,
        "binary_content": None,
    }


def read_session_photo(photo) -> bytes:
    if photo.storage_backend == "firebase":
        try:
            from firebase_admin import storage

            app = get_firebase_admin_app()
            bucket = storage.bucket(app=app)
            blob = bucket.blob(photo.storage_path)
            return blob.download_as_bytes()
        except Exception as exc:
            logger.warning("Tangred photo read fell back to local storage: %s", exc)

    if photo.storage_backend == "database" and photo.binary_content is not None:
        return bytes(photo.binary_content)

    with default_storage.open(photo.storage_path or photo.image.name, "rb") as stored:
        return stored.read()
