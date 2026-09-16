from app.db.mongo import document_repository
from app.services.embedding_service import embedding_service
from app.services.vector_store import VectorStore
from app.services.deepseek_service import DeepSeekService
from app.services.rag_service import RAGService
from app.services.retriever import Retriever
from app.services.document_service import DocumentService

vector_store = VectorStore()

retriever = Retriever(
    embedding_service,
    vector_store
)

deepseek_service = DeepSeekService()

rag_service = RAGService(
    retriever,
    deepseek_service,
    document_repository,
)

document_service = DocumentService(
    embedding_service,
    vector_store,
    document_repository,
)

def get_rag_service():
    return rag_service

def get_document_service():
    return document_service
