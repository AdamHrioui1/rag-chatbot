import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.config import settings
from app.core.dependencies import get_document_service, get_rag_service
from app.core.auth_manual import verify_token_manual
from app.exceptions.custom_exceptions import RAGException
from app.models import (
    DocumentResponse,
    QuestionRequest,
    QuestionResponse,
    UploadResponse,
    UploadResult,
)
from app.services.document_service import DocumentService
from app.services.extractors import extract_files_from_zip, get_extension
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/chat', response_model=QuestionResponse)
def chat(
    request: Request,
    question_request: QuestionRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Chat endpoint - requires a valid JWT token from the MERN app.
    The question is only ever answered from the authenticated user's own
    documents (enforced inside RAGService/Retriever/VectorStore).
    """
    token_data = verify_token_manual(request)
    user_id = token_data.get('id')

    logger.info(f"Authenticated user {user_id} asking: {question_request.question[:50]}...")
    return rag_service.ask(question_request.question, user_id)


def _to_document_response(document: dict) -> DocumentResponse:
    created_at = document["created_at"]
    return DocumentResponse(
        id=document["id"],
        filename=document["filename"],
        content_type=document["content_type"],
        size_bytes=document["size_bytes"],
        status=document["status"],
        chunk_count=document["chunk_count"],
        error_message=document.get("error_message"),
        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
    )


def _process_one_file(
    document_service: DocumentService, user_id: str, filename: str, content: bytes
) -> UploadResult:
    try:
        outcome = document_service.process_upload(user_id, filename, content)
        return UploadResult(
            filename=filename,
            success=True,
            document=_to_document_response(outcome["document"]),
            message="This document was already uploaded previously." if outcome["duplicate"] else None,
        )
    except RAGException as e:
        return UploadResult(filename=filename, success=False, error=str(e))
    except Exception:
        # An infrastructure hiccup (Mongo/Chroma unavailable, disk full,
        # ...) on one file shouldn't fail the other files in the same
        # batch - report it as this file's failure instead.
        logger.exception(f"Unexpected error while processing {filename}")
        return UploadResult(
            filename=filename, success=False, error="Unexpected error while processing this file."
        )


@router.post('/documents/upload', response_model=UploadResponse)
def upload_documents(
    request: Request,
    files: list[UploadFile] = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Accepts one or more files in a single request. A .zip is expanded in
    memory (safely - see extractors.extract_files_from_zip) and each file
    inside it is processed the same way as a directly uploaded file.
    Each file's outcome is reported independently, so one bad file in a
    batch doesn't fail the whole upload.
    """
    token_data = verify_token_manual(request)
    user_id = token_data.get('id')

    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    results: list[UploadResult] = []

    for upload in files:
        filename = upload.filename or "unnamed"
        content = upload.file.read()

        if get_extension(filename) == ".zip":
            try:
                inner_files = extract_files_from_zip(content)
            except RAGException as e:
                results.append(UploadResult(filename=filename, success=False, error=str(e)))
                continue

            for inner_filename, inner_content in inner_files:
                results.append(
                    _process_one_file(document_service, user_id, inner_filename, inner_content)
                )
        else:
            results.append(_process_one_file(document_service, user_id, filename, content))

    logger.info(
        f"User {user_id} upload: {sum(r.success for r in results)}/{len(results)} file(s) succeeded."
    )
    return UploadResponse(results=results)


@router.get('/documents', response_model=list[DocumentResponse])
def list_documents(
    request: Request,
    document_service: DocumentService = Depends(get_document_service),
):
    token_data = verify_token_manual(request)
    user_id = token_data.get('id')

    documents = document_service.list_documents(user_id)
    return [_to_document_response(doc) for doc in documents]


@router.delete('/documents/{document_id}')
def delete_document(
    document_id: str,
    request: Request,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Deletes a document's vectors, file, and metadata. Ownership is
    checked inside document_service (by looking the document up as
    "this id AND this user_id" together) so a user can never delete
    someone else's document by guessing/changing an id in the request.
    """
    token_data = verify_token_manual(request)
    user_id = token_data.get('id')

    deleted = document_service.delete_document(document_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")

    return {"success": True, "message": "Document deleted successfully."}


@router.post('/internal/cleanup-stale-processing')
def cleanup_stale_processing(
    request: Request,
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Maintenance endpoint, not for end users - marks any document stuck in
    "processing" for too long (e.g. the server crashed mid-upload) as
    "failed", so it doesn't sit stuck in the UI forever. Meant to be
    called periodically by a scheduled Lambda function (EventBridge ->
    Lambda -> this endpoint).

    Authenticated by a shared secret rather than a user JWT, since
    there's no "user" behind this call - just our own scheduled job.
    """
    provided_secret = request.headers.get("X-Internal-Secret")
    if not provided_secret or provided_secret != settings.INTERNAL_TASK_SECRET:
        raise HTTPException(status_code=401, detail="Not authorized.")

    cleaned_up = document_service.cleanup_stale_processing()
    logger.info(f"Cleanup: marked {cleaned_up} stale 'processing' document(s) as failed.")
    return {"cleaned_up": cleaned_up}
