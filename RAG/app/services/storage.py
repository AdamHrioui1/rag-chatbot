import logging
import re
import uuid
from pathlib import Path

from app.core.config import settings
from app.services.extractors import get_extension

logger = logging.getLogger(__name__)

BASE_STORAGE_PATH = Path(settings.STORAGE_PATH)


def _safe_user_folder(user_id: str) -> Path:
    """
    Build the on-disk folder for a user, rejecting anything that isn't a
    plain alphanumeric id. The user_id comes from a verified JWT, but we
    validate it again here as defense-in-depth before it's used to build
    a filesystem path - a malformed/crafted id (e.g. containing "..")
    must never be able to escape the storage folder.
    """
    if not re.fullmatch(r"[a-zA-Z0-9]+", user_id):
        raise ValueError("Invalid user id")

    folder = BASE_STORAGE_PATH / user_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_file(user_id: str, original_filename: str, content: bytes) -> str:
    """
    Save uploaded file bytes to disk under a generated, random name -
    never under the name the user gave us. This avoids:
    - path traversal (a filename like "../../app/main.py")
    - overwriting another document if two uploads share a filename
    - executing anything: we only ever read these files back as bytes

    Returns the path relative to BASE_STORAGE_PATH, which is what gets
    stored in MongoDB.
    """
    folder = _safe_user_folder(user_id)
    extension = get_extension(original_filename)
    stored_name = f"{uuid.uuid4().hex}{extension}"

    file_path = folder / stored_name
    file_path.write_bytes(content)

    return f"{user_id}/{stored_name}"


def delete_file(relative_path: str) -> None:
    """Remove a stored file. Missing files are logged, not raised - by the
    time we're deleting metadata, a missing file on disk shouldn't block
    the rest of the cleanup."""
    file_path = BASE_STORAGE_PATH / relative_path

    try:
        file_path.unlink()
    except FileNotFoundError:
        logger.warning(f"File already missing on delete: {relative_path}")
    except OSError as e:
        logger.error(f"Failed to delete file {relative_path}: {e}")
