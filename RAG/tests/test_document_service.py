from unittest.mock import Mock, patch

import numpy as np
import pytest

from app.exceptions.custom_exceptions import (
    FileTooLargeException,
    UnsupportedFileTypeException,
)
from app.services.document_service import DocumentService

USER_ID = "user123"


def make_service():
    embedding_service = Mock()
    embedding_service.generate_embedding.return_value = np.array([0.1, 0.2, 0.3])

    vector_store = Mock()
    document_repository = Mock()

    service = DocumentService(embedding_service, vector_store, document_repository)
    return service, embedding_service, vector_store, document_repository


@patch("app.services.document_service.storage.save_file", return_value="user123/fake.txt")
def test_process_upload_success_indexes_and_marks_ready(mock_save_file):
    service, embedding_service, vector_store, document_repository = make_service()

    document_repository.find_ready_duplicate.return_value = None
    document_repository.create.return_value = {"id": "doc1", "stored_path": "user123/fake.txt"}
    document_repository.get_by_id.return_value = {"id": "doc1", "status": "ready", "chunk_count": 1}

    result = service.process_upload(USER_ID, "notes.txt", b"Some real document content.")

    assert result["duplicate"] is False
    vector_store.add_documents.assert_called_once()
    document_repository.mark_ready.assert_called_once()

    # every chunk's metadata must carry the owning user_id - this is the
    # data that makes retrieval isolation possible downstream.
    _, kwargs = vector_store.add_documents.call_args
    assert all(m["user_id"] == USER_ID for m in kwargs["metadatas"])
    assert all(m["document_id"] == "doc1" for m in kwargs["metadatas"])


def test_process_upload_rejects_unsupported_extension_before_creating_record():
    service, _, vector_store, document_repository = make_service()

    with pytest.raises(UnsupportedFileTypeException):
        service.process_upload(USER_ID, "malware.exe", b"MZ")

    document_repository.create.assert_not_called()
    vector_store.add_documents.assert_not_called()


def test_process_upload_rejects_oversized_file():
    service, _, _, document_repository = make_service()

    from app.core.config import settings

    too_big = b"a" * (settings.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)

    with pytest.raises(FileTooLargeException):
        service.process_upload(USER_ID, "big.txt", too_big)

    document_repository.create.assert_not_called()


@patch("app.services.document_service.storage.save_file")
def test_process_upload_detects_duplicate_without_reprocessing(mock_save_file):
    service, embedding_service, vector_store, document_repository = make_service()

    existing = {"id": "existing-doc", "filename": "notes.txt", "status": "ready"}
    document_repository.find_ready_duplicate.return_value = existing

    result = service.process_upload(USER_ID, "notes.txt", b"Some real document content.")

    assert result["duplicate"] is True
    assert result["document"] == existing
    document_repository.create.assert_not_called()
    mock_save_file.assert_not_called()
    embedding_service.generate_embedding.assert_not_called()


def test_delete_document_returns_none_when_not_owned_by_caller():
    """A different user's document id must never be deletable, even if
    the caller somehow knows/guesses the id."""
    service, _, vector_store, document_repository = make_service()
    document_repository.get_by_id_for_user.return_value = None

    result = service.delete_document("someones-doc-id", USER_ID)

    assert result is None
    document_repository.get_by_id_for_user.assert_called_once_with("someones-doc-id", USER_ID)
    vector_store.delete.assert_not_called()
    document_repository.delete.assert_not_called()


@patch("app.services.document_service.storage.delete_file")
def test_delete_document_removes_vectors_file_and_metadata(mock_delete_file):
    service, _, vector_store, document_repository = make_service()
    document_repository.get_by_id_for_user.return_value = {
        "id": "doc1",
        "stored_path": "user123/fake.txt",
    }

    result = service.delete_document("doc1", USER_ID)

    assert result is not None
    vector_store.delete.assert_called_once_with(where={"document_id": "doc1"})
    mock_delete_file.assert_called_once_with("user123/fake.txt")
    document_repository.delete.assert_called_once_with("doc1")
