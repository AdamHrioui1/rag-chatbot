import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    
    def generate_embedding(self, text: str):
        
        embedding = self.model.encode(
            text,
            convert_to_numpy=True
        )

        logger.info("Embedding generated successfully.")

        return embedding
    
embedding_service = EmbeddingService()