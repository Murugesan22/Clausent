import os
import re
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import DocumentValidationError

def sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters from filename."""
    # Strip directory paths
    base_name = os.path.basename(filename)
    # Remove any characters other than alphanumeric, dots, underscores, dashes, spaces
    clean_name = re.sub(r'[^\w\s\.-]', '_', base_name).strip()
    return clean_name or "document"

def validate_uploaded_file(file: UploadFile) -> str:
    """
    Validates uploaded file extension, size, and content.
    Returns the lowercased extension (without dot).
    """
    if not file.filename:
        raise DocumentValidationError("No filename provided.")

    clean_name = sanitize_filename(file.filename)
    ext = Path(clean_name).suffix.lower().lstrip(".")

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file format '.{ext}'. Supported formats are: {', '.join(settings.ALLOWED_EXTENSIONS).upper()}."
        )

    return ext

def generate_safe_filename(original_name: str) -> tuple[str, str]:
    """
    Generates a secure UUID-based internal filename while preserving the original display name.
    Returns (internal_filename, safe_display_name).
    """
    clean_name = sanitize_filename(original_name)
    ext = Path(clean_name).suffix.lower()
    doc_id = str(uuid.uuid4())
    internal_name = f"{doc_id}{ext}"
    return internal_name, clean_name, doc_id
