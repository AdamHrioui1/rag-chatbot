import hashlib
import logging

from app.core.config import settings
from app.db.mongo import DocumentRepository
from app.exceptions.custom_exceptions import (
    DocumentExtractionException,
    FileTooLargeException,
    RAGException,
    UnsupportedFileTypeException,
)
from app.services import extractors
from app.services import storage
from app.services.chunker import chunk_text
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

_CONTENT_TYPE_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


class DocumentService:
    """
    Orchestrates the full ingestion pipeline for one uploaded file:

        validate -> store on disk -> extract text -> clean -> chunk
            -> embed -> save vectors -> record metadata

    and the corresponding teardown for deletion. This is the one place
    that ties MongoDB (metadata), disk storage (raw files) and ChromaDB
    (vectors) together, so a document's lifecycle is managed in one spot
    instead of being spread across route handlers.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        document_repository: DocumentRepository,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.document_repository = document_repository

    def process_upload(self, user_id: str, filename: str, content: bytes) -> dict:
        """
        Handles one file. Returns a dict describing the outcome:
            {"document": {...}, "duplicate": bool}

        Raises RAGException subclasses for problems the caller should
        report back to the user (unsupported type, too large, corrupted,
        empty) - these are raised *before* any database record is
        created, so there is nothing to clean up on that path.
        """
        self._validate(filename, content)

        content_hash = hashlib.sha256(content).hexdigest()
        duplicate = self.document_repository.find_ready_duplicate(user_id, content_hash)
        if duplicate:
            return {"document": duplicate, "duplicate": True}

        extension = extractors.get_extension(filename)
        stored_path = storage.save_file(user_id, filename, content)

        document = self.document_repository.create(
            user_id=user_id,
            filename=filename,
            stored_path=stored_path,
            content_type=_CONTENT_TYPE_BY_EXTENSION.get(extension, "application/octet-stream"),
            size_bytes=len(content),
            content_hash=content_hash,
        )

        try:
            text = extractors.extract_text(filename, content)
            chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

            if not chunks:
                raise DocumentExtractionException("No extractable text found in this file.")

            embeddings = [
                self.embedding_service.generate_embedding(chunk).tolist() for chunk in chunks
            ]
            ids = [f"{document['id']}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "user_id": user_id,
                    "document_id": document["id"],
                    "filename": filename,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            # A single call: either the whole document's chunks are added,
            # or none are - there's no partially-indexed state to clean up.
            self.vector_store.add_documents(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            self.document_repository.mark_ready(document["id"], chunk_count=len(chunks))
            logger.info(f"Document {document['id']} indexed with {len(chunks)} chunks.")

            return {
                "document": self.document_repository.get_by_id(document["id"]),
                "duplicate": False,
            }

        except Exception as e:
            message = str(e) if isinstance(e, RAGException) else "Failed to process this document."
            self.document_repository.mark_failed(document["id"], message)
            logger.exception(f"Failed to process document {document['id']}: {filename}")
            raise

    def list_documents(self, user_id: str) -> list[dict]:
        return self.document_repository.list_for_user(user_id)

    def cleanup_stale_processing(self) -> int:
        """Marks documents stuck in "processing" for too long as
        "failed". See DocumentRepository.mark_stale_processing_as_failed
        for why this is needed."""
        return self.document_repository.mark_stale_processing_as_failed(
            older_than_minutes=settings.STALE_PROCESSING_MINUTES
        )

    def delete_document(self, document_id: str, user_id: str) -> dict | None:
        """
        Deletes a document's vectors, physical file, and metadata.
        Returns the deleted document's metadata, or None if no document
        with that id belongs to this user (the route turns that into a
        404 - it never reveals whether the document exists for someone
        else).
        """
        document = self.document_repository.get_by_id_for_user(document_id, user_id)
        if not document:
            return None

        # Remove vectors first so the document stops being searchable
        # immediately, even if a later step (file/db cleanup) has issues.
        try:
            self.vector_store.delete(where={"document_id": document_id})
        except Exception:
            logger.exception(f"Failed to delete vectors for document {document_id}")

        storage.delete_file(document["stored_path"])
        self.document_repository.delete(document_id)

        return document

    def _validate(self, filename: str, content: bytes) -> None:
        extension = extractors.get_extension(filename)
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeException(
                f"'{extension}' is not supported. "
                f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        if len(content) == 0:
            raise DocumentExtractionException("This file is empty.")

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeException(
                f"This file is larger than the {settings.MAX_FILE_SIZE_MB}MB limit."
            )
