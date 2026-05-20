from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename


def allowed_image_file(filename: str, allowed_extensions: set[str]) -> bool:
    """Return True when the file extension is allowed."""
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions


def build_unique_filename(original_filename: str) -> str:
    """Create a safe unique filename while keeping the original extension."""
    safe_name = secure_filename(original_filename)
    suffix = Path(safe_name).suffix.lower()
    stem = Path(safe_name).stem or "image"
    return f"{stem}_{uuid4().hex}{suffix}"
