import logging
import re
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class Retriever:

    def __init__(
        self, 
        embedding_service: EmbeddingService, 
        vector_store: VectorStore
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def _expand_query(self, question: str) -> list[str]:
        """Generate multiple query variations for better retrieval"""
        # Clean and normalize the question
        cleaned = question.lower().strip()
        
        # Common French spelling variations
        variations = [cleaned]
        
        # Fix common typos
        corrections = {
            "platform": "plateforme",
            "platforms": "plateformes",
            "interne": "internes",
            "principale": "principales",
        }
        
        for wrong, correct in corrections.items():
            if wrong in cleaned:
                variations.append(cleaned.replace(wrong, correct))
        
        # Remove extra spaces and fix punctuation
        variations = [re.sub(r'\s+', ' ', v).strip() for v in variations]
        
        # Remove duplicates
        return list(set(variations))

    def retrieve(self, question: str, user_id: str):
        logger.info(f"Searching ChromaDB for user {user_id}: {question}")

        # Expand query if enabled
        queries = [question]
        if settings.ENABLE_QUERY_EXPANSION:
            expanded = self._expand_query(question)
            queries = expanded
            logger.info(f"Expanded queries: {queries}")

        # Search with all query variations, always scoped to this user's
        # own documents - this is the isolation boundary. Every search
        # this Retriever ever does is filtered by user_id, so it's not
        # possible to accidentally retrieve another user's chunks.
        all_results = []
        seen_ids = set()

        for query in queries:
            query_embedding = self.embedding_service.generate_embedding(query)

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=settings.TOP_K,
                where={"user_id": user_id},
            )

            # Add unique results
            for result in results:
                doc_id = result["id"]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append(result)
        
        # Sort by distance (lower = more similar)
        all_results.sort(key=lambda x: x["distance"])

        # Drop anything past the similarity threshold. This is what makes
        # "I couldn't find that in your documents" possible: a document
        # that merely exists isn't enough, its best chunk has to actually
        # be relevant to the question.
        relevant_results = [
            r for r in all_results if r["distance"] <= settings.SIMILARITY_THRESHOLD
        ]

        if not relevant_results:
            logger.info("No chunks passed the similarity threshold.")
            return []

        logger.info(f"{len(relevant_results)} relevant chunks retrieved.")
        return relevant_results[:settings.TOP_K]

