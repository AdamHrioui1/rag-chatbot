import logging
import chromadb
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH
        )

        # Explicitly use cosine distance (0 = identical meaning, 2 = opposite)
        # instead of Chroma's raw L2 default, since our embeddings aren't
        # normalized - cosine gives a distance that's easier to reason
        # about and to calibrate SIMILARITY_THRESHOLD against.
        # Note: this only applies when the collection is first created -
        # it can't be changed on an existing collection.
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )


    def add_documents(
        self, 
        ids: list[str], 
        documents: list[str], 
        embeddings: list[list[float]], 
        metadatas: list[dict]
    ) -> None:
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )


    def reset(self):
        self.client.delete_collection("knowledge_base")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )


    def count(self):
        return self.collection.count()


    def delete(self, where: dict) -> None:
        """Delete every chunk matching a metadata filter, e.g.
        {"document_id": "..."} when a user deletes one document."""
        self.collection.delete(where=where)


    def search(self, query_embedding, top_k: int = 3, where: dict | None = None):
        """
        `where` is a Chroma metadata filter, e.g. {"user_id": "abc123"}.
        This is what makes retrieval user-scoped: Chroma only considers
        chunks whose metadata matches the filter, so a query embedding
        can never come back with another user's chunk, regardless of how
        similar it is.
        """
        logger.info(f"Searching top {top_k} documents.")

        query_kwargs = {
            "query_embeddings": [query_embedding.tolist()],
            "n_results": top_k,
        }
        if where:
            query_kwargs["where"] = where

        results = self.collection.query(**query_kwargs)

        search_results = []

        for i in range(len(results["ids"][0])):
            search_results.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        
        return search_results