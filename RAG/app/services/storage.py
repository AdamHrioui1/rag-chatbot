import logging
import re
import uuid

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.extractors import get_extension

logger = logging.getLogger(__name__)

# boto3 finds AWS credentials automatically, in this order:
#   1. AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY environment variables
#      (set in RAG/.env for local development)
#   2. The IAM Role attached to the EC2 instance, if running there
# The app never hardcodes a credential either way - locally it reads an
# explicit key pair scoped to this one bucket; on EC2 it uses the
# instance's role, which AWS rotates automatically behind the scenes.
_s3_client = boto3.client("s3", region_name=settings.AWS_REGION)


def _safe_user_id(user_id: str) -> str:
    """
    Reject anything that isn't a plain alphanumeric id before it's used
    to build an S3 key. The user_id comes from a verified JWT, but we
    validate it again here as defense-in-depth - a malformed/crafted id
    (e.g. containing "../" or "/") must never be able to escape the
    user's own prefix within the bucket.
    """
    if not re.fullmatch(r"[a-zA-Z0-9]+", user_id):
        raise ValueError("Invalid user id")
    return user_id


def save_file(user_id: str, original_filename: str, content: bytes) -> str:
    """
    Upload file bytes to S3 under a generated, random key - never under
    the name the user gave us. This avoids:
    - path traversal (a filename like "../../app/main.py")
    - overwriting another document if two uploads share a filename
    - executing anything: we only ever read these bytes back, never run them

    Returns the S3 object key, which is what gets stored in MongoDB.
    """
    user_id = _safe_user_id(user_id)
    extension = get_extension(original_filename)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    key = f"{user_id}/{stored_name}"

    _s3_client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=content,
    )

    return key


def delete_file(key: str) -> None:
    """Remove a stored object. S3's delete is idempotent - deleting a key
    that doesn't exist is not an error, so (unlike the old local-disk
    version) there's no separate "already missing" case to handle."""
    try:
        _s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
    except ClientError as e:
        logger.error(f"Failed to delete S3 object {key}: {e}")
