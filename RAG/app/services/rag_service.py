import logging
from app.db.mongo import DocumentRepository
from app.services.deepseek_service import DeepSeekService
from app.services.prompt_builder import PromptBuilder
from app.services.retriever import Retriever
from app.exceptions.custom_exceptions import DeepSeekException

logger = logging.getLogger(__name__)

NO_DOCUMENTS_MESSAGE = (
    "You haven't uploaded any documents yet. Upload a document from the "
    "'My Documents' page to start asking questions about it."
)

NOT_FOUND_MESSAGE = (
    "I couldn't find relevant information in your uploaded documents to "
    "answer this question."
)


class RAGService:
    def __init__(
        self,
        retriever: Retriever,
        deepseek_service: DeepSeekService,
        document_repository: DocumentRepository,
    ):
        self.retriever = retriever
        self.deepseek_service = deepseek_service
        self.document_repository = document_repository

    def ask(self, question: str, user_id: str) -> dict:
        logger.info(f"New question from user {user_id}: {question}")

        # Nothing to search yet - don't even try, and don't waste an LLM
        # call telling the user what we already know.
        if self.document_repository.count_ready_for_user(user_id) == 0:
            logger.info(f"User {user_id} has no ready documents.")
            return {"answer": NO_DOCUMENTS_MESSAGE, "sources": []}

        documents = self.retriever.retrieve(question, user_id)

        # No chunk was relevant enough. We deliberately do NOT call the
        # LLM in this case: without real context, the model is free to
        # fall back on its own general knowledge and "confidently"
        # answer from outside the user's documents, which is exactly the
        # kind of hallucination this app is meant to avoid.
        if not documents:
            logger.info("No relevant documents found in retrieval.")
            return {"answer": NOT_FOUND_MESSAGE, "sources": []}

        context = self._build_context(documents)
        logger.info(f"Context built from {len(documents)} chunks.")

        system_prompt, user_prompt = PromptBuilder.build(question, context)

        try:
            logger.info("Calling DeepSeek API...")
            answer = self.deepseek_service.generate_answer(system_prompt, user_prompt)
            logger.info("Answer generated successfully.")
        except Exception as e:
            logger.exception("DeepSeek request failed.")
            raise DeepSeekException("Unable to generate answer.") from e

        sources = []
        for doc in documents[:3]:  # Limit to top 3 sources shown to the user
            confidence = max(0, min(100, round((1 - doc["distance"]) * 100)))
            content = doc["document"]
            snippet = content[:500] + ("..." if len(content) > 500 else "")

            sources.append(
                {
                    "id": doc["id"],
                    "title": doc["metadata"].get("filename", "document"),
                    "snippets": snippet,
                    "distance": round(doc["distance"], 3),
                    "confidence": confidence,
                }
            )

        return {
            "answer": answer,
            "sources": sources,
        }

    def _build_context(self, documents):
        context_parts = []
        for i, doc in enumerate(documents, 1):
            filename = doc["metadata"].get("filename", "document")
            context_parts.append(f"[Document {i}: {filename}]\n{doc['document']}")

        return "\n\n---\n\n".join(context_parts)
