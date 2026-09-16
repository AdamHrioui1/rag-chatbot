from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """What the frontend sees for one document in the 'My Documents' list."""

    id: str
    filename: str
    content_type: str
    size_bytes: int
    status: str  # "processing" | "ready" | "failed"
    chunk_count: int
    error_message: str | None = None
    created_at: str


class UploadResult(BaseModel):
    """Per-file outcome of an upload request - lets the frontend show
    '3 uploaded, 1 failed: bad_file.exe not supported' instead of an
    all-or-nothing response."""

    filename: str
    success: bool
    document: DocumentResponse | None = None
    error: str | None = None
    message: str | None = None  # informational note, e.g. "already uploaded"


class UploadResponse(BaseModel):
    results: list[UploadResult]
