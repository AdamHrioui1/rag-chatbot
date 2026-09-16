import jwt
from unittest.mock import Mock
from app.main import app
from app.core.config import settings
from app.core.dependencies import get_rag_service, get_document_service
from fastapi.testclient import TestClient
from app.exceptions.custom_exceptions import DeepSeekException, UnsupportedFileTypeException

client = TestClient(app)


def auth_header(user_id: str = "user123"):
    token = jwt.encode({"id": user_id}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def fake_rag_service():
    rag_service = Mock()
    rag_service.ask.return_value = {
        "answer": "OCR is Optical Character Recognition",
        "sources": [],
    }
    return rag_service


app.dependency_overrides[get_rag_service] = fake_rag_service


def test_chat_success():
    response = client.post(
        "/chat", json={"question": "What is OCR"}, headers=auth_header()
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "OCR is Optical Character Recognition"
    assert body["sources"] == []


def test_chat_requires_authentication():
    response = client.post("/chat", json={"question": "What is OCR"})
    assert response.status_code == 401


def test_chat_validation():
    response = client.post("/chat", json={}, headers=auth_header())
    assert response.status_code == 422


def test_chat_empty_question():
    response = client.post("/chat", json={"question": ""}, headers=auth_header())
    assert response.status_code == 422


def test_chat_deepseek_failure():
    def fake_error_service():
        service = Mock()
        service.ask.side_effect = DeepSeekException("DeepSeek unavailable")
        return service

    app.dependency_overrides[get_rag_service] = fake_error_service

    response = client.post("/chat", json={"question": "Hello"}, headers=auth_header())

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["message"] == "DeepSeek unavailable"

    app.dependency_overrides[get_rag_service] = fake_rag_service


# --- Document endpoints ---


def test_upload_requires_authentication():
    response = client.post(
        "/documents/upload",
        files={"files": ("a.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 401


def test_list_documents_returns_only_the_caller_documents():
    service = Mock()
    service.list_documents.return_value = [
        {
            "id": "doc1",
            "filename": "a.txt",
            "content_type": "text/plain",
            "size_bytes": 5,
            "status": "ready",
            "chunk_count": 1,
            "error_message": None,
            "created_at": "2024-01-01T00:00:00+00:00",
        }
    ]
    app.dependency_overrides[get_document_service] = lambda: service

    response = client.get("/documents", headers=auth_header("user123"))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["filename"] == "a.txt"
    service.list_documents.assert_called_once_with("user123")

    del app.dependency_overrides[get_document_service]


def test_delete_document_not_owned_returns_404():
    """The service returns None when the document doesn't belong to the
    caller - the route must turn that into a 404, not a 403, so it
    doesn't confirm whether the id exists for someone else."""
    service = Mock()
    service.delete_document.return_value = None
    app.dependency_overrides[get_document_service] = lambda: service

    response = client.delete("/documents/someoneelses-doc", headers=auth_header("user123"))

    assert response.status_code == 404
    service.delete_document.assert_called_once_with("someoneelses-doc", "user123")

    del app.dependency_overrides[get_document_service]


def test_delete_document_success():
    service = Mock()
    service.delete_document.return_value = {"id": "doc1"}
    app.dependency_overrides[get_document_service] = lambda: service

    response = client.delete("/documents/doc1", headers=auth_header("user123"))

    assert response.status_code == 200
    assert response.json()["success"] is True

    del app.dependency_overrides[get_document_service]


def test_upload_reports_per_file_failure_without_500():
    """An unsupported file type is a normal, expected outcome - it should
    come back as a 200 with success=False for that file, not an HTTP
    error, so a batch upload can report partial success."""
    service = Mock()
    service.process_upload.side_effect = UnsupportedFileTypeException(
        "'.exe' is not supported."
    )
    app.dependency_overrides[get_document_service] = lambda: service

    response = client.post(
        "/documents/upload",
        files={"files": ("virus.exe", b"MZ", "application/octet-stream")},
        headers=auth_header("user123"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["success"] is False
    assert "not supported" in body["results"][0]["error"]

    del app.dependency_overrides[get_document_service]


# --- Internal maintenance endpoint (called by the scheduled Lambda) ---


def test_cleanup_stale_processing_requires_the_shared_secret():
    response = client.post("/internal/cleanup-stale-processing")
    assert response.status_code == 401


def test_cleanup_stale_processing_rejects_wrong_secret():
    response = client.post(
        "/internal/cleanup-stale-processing",
        headers={"X-Internal-Secret": "wrong-secret"},
    )
    assert response.status_code == 401


def test_cleanup_stale_processing_succeeds_with_correct_secret():
    service = Mock()
    service.cleanup_stale_processing.return_value = 3
    app.dependency_overrides[get_document_service] = lambda: service

    response = client.post(
        "/internal/cleanup-stale-processing",
        headers={"X-Internal-Secret": settings.INTERNAL_TASK_SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"cleaned_up": 3}

    del app.dependency_overrides[get_document_service]
