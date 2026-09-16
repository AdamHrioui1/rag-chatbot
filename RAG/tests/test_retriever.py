import numpy as np
from unittest.mock import Mock
from app.services.retriever import Retriever

USER_ID = "user123"


def test_retriever_return_documents():
    embedding_service = Mock()
    vector_store = Mock()

    embedding_service.generate_embedding.return_value = np.array([0.1, 0.2, 0.3])
    vector_store.search.return_value = [
        {
            "id": "doc1",
            "document": "OCR information",
            "metadata": {"filename": "ocr.txt"},
            "distance": 0.35,
        }
    ]

    retriever = Retriever(embedding_service, vector_store)
    results = retriever.retrieve("What is OCR?", USER_ID)

    assert len(results) == 1
    assert results[0]["id"] == "doc1"

    embedding_service.generate_embedding.assert_called()
    vector_store.search.assert_called()

    # Every search must be scoped to the asking user - this is the
    # isolation guarantee. If this filter is ever dropped, this test
    # fails.
    _, kwargs = vector_store.search.call_args
    assert kwargs["where"] == {"user_id": USER_ID}


def test_retriever_empty_when_no_document():
    embedding_service = Mock()
    vector_store = Mock()

    embedding_service.generate_embedding.return_value = np.array([0.1])
    vector_store.search.return_value = []

    retriever = Retriever(embedding_service, vector_store)
    results = retriever.retrieve("Who created Python?", USER_ID)

    assert results == []


def test_retriever_filters_out_results_past_similarity_threshold():
    """A chunk that technically comes back from Chroma but is too
    dissimilar (distance above SIMILARITY_THRESHOLD) must not be treated
    as relevant - otherwise the LLM would get irrelevant context and
    might still try to answer from it."""
    embedding_service = Mock()
    vector_store = Mock()

    embedding_service.generate_embedding.return_value = np.array([0.1])
    vector_store.search.return_value = [
        {
            "id": "doc1",
            "document": "Unrelated content",
            "metadata": {"filename": "unrelated.txt"},
            "distance": 1.9,  # far above the default 1.3 threshold
        }
    ]

    retriever = Retriever(embedding_service, vector_store)
    results = retriever.retrieve("What is OCR?", USER_ID)

    assert results == []
