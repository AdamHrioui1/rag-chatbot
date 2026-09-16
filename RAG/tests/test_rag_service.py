import pytest
from unittest.mock import Mock
from app.services.rag_service import RAGService
from app.exceptions.custom_exceptions import DeepSeekException

USER_ID = "user123"


def make_service(retrieve_return, has_documents=True):
    retriever = Mock()
    deepseek_service = Mock()
    document_repository = Mock()

    retriever.retrieve.return_value = retrieve_return
    document_repository.count_ready_for_user.return_value = 1 if has_documents else 0

    rag_service = RAGService(retriever, deepseek_service, document_repository)
    return rag_service, retriever, deepseek_service, document_repository


def test_rag_service_return_answer_and_sources():
    rag_service, retriever, deepseek_service, _ = make_service(
        [
            {
                "id": "doc1",
                "document": "OCR is Optical Character Recognition.",
                "metadata": {"filename": "ocr.txt"},
                "distance": 0.3,
            }
        ]
    )
    deepseek_service.generate_answer.return_value = "OCR is Optical Character Recognition."

    response = rag_service.ask("What is OCR?", USER_ID)

    assert response["answer"] == "OCR is Optical Character Recognition."
    assert len(response["sources"]) == 1
    assert response["sources"][0]["id"] == "doc1"
    assert response["sources"][0]["title"] == "ocr.txt"

    retriever.retrieve.assert_called_once_with("What is OCR?", USER_ID)
    deepseek_service.generate_answer.assert_called_once()


def test_rag_service_no_documents_uploaded_never_calls_llm():
    """If the user hasn't uploaded anything yet, we shouldn't even try to
    retrieve or call the LLM - there's nothing to search."""
    rag_service, retriever, deepseek_service, _ = make_service([], has_documents=False)

    response = rag_service.ask("Who created Python?", USER_ID)

    assert "haven't uploaded any documents" in response["answer"]
    assert response["sources"] == []

    retriever.retrieve.assert_not_called()
    deepseek_service.generate_answer.assert_not_called()


def test_rag_service_no_relevant_chunks_never_calls_llm():
    """If the user has documents but none of them are relevant to this
    question, we must say so directly instead of asking the LLM to answer
    without real context (which risks it inventing an answer)."""
    rag_service, retriever, deepseek_service, _ = make_service([], has_documents=True)

    response = rag_service.ask("Who created Python?", USER_ID)

    assert "couldn't find relevant information" in response["answer"]
    assert response["sources"] == []

    retriever.retrieve.assert_called_once()
    deepseek_service.generate_answer.assert_not_called()


def test_confidence_score():
    rag_service, _, deepseek_service, _ = make_service(
        [
            {
                "id": "doc1",
                "document": "OCR is Optical Character Recognition.",
                "metadata": {"filename": "ocr.txt"},
                "distance": 0.25,
            }
        ]
    )
    deepseek_service.generate_answer.return_value = "answer"

    response = rag_service.ask("OCR", USER_ID)

    assert response["sources"][0]["confidence"] == 75


def test_snippet_is_capped_at_500_characters():
    rag_service, _, deepseek_service, _ = make_service(
        [
            {
                "id": "doc1",
                "document": "A" * 800,
                "metadata": {"filename": "big.txt"},
                "distance": 0.1,
            }
        ]
    )
    deepseek_service.generate_answer.return_value = "answer"

    response = rag_service.ask("OCR", USER_ID)

    assert len(response["sources"][0]["snippets"]) == 503  # 500 chars + "..."
    assert response["sources"][0]["snippets"].endswith("...")


def test_deepseek_failure_raises_when_documents_are_relevant():
    rag_service, _, deepseek_service, _ = make_service(
        [
            {
                "id": "doc1",
                "document": "OCR is Optical Character Recognition.",
                "metadata": {"filename": "ocr.txt"},
                "distance": 0.2,
            }
        ]
    )
    deepseek_service.generate_answer.side_effect = Exception("API Down")

    with pytest.raises(DeepSeekException):
        rag_service.ask("OCR", USER_ID)
