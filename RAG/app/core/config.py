import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        self.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL")
        self.TOP_K = int(os.getenv("TOP_K", 5))
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 1.3))
        self.CHROMA_PATH = os.getenv("CHROMA_PATH")

        # JWT settings - must match the MERN app's ACCESS_TOKEN_SECRET
        self.JWT_SECRET_KEY = os.getenv("ACCESS_TOKEN_SECRET")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

        # Query expansion (simple typo/synonym handling before retrieval)
        self.ENABLE_QUERY_EXPANSION = os.getenv("ENABLE_QUERY_EXPANSION", "true").lower() == "true"

        # MongoDB - same database the Node server uses, but a separate
        # `documents` collection so the two apps don't collide.
        self.MONGO_URI = os.getenv("MONGO_URI")
        self.MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "test")

        # CORS - the browser calls this API directly for document
        # upload/list/delete, so it needs to be allowed to do so.
        self.CORS_ORIGINS = [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ]

        # Document ingestion
        self.STORAGE_PATH = os.getenv("STORAGE_PATH", "storage")
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 150))
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 15))
        self.ALLOWED_EXTENSIONS = tuple(
            ext.strip().lower()
            for ext in os.getenv("ALLOWED_EXTENSIONS", ".pdf,.docx,.txt").split(",")
            if ext.strip()
        )

        if not self.JWT_SECRET_KEY:
            logger.error("ACCESS_TOKEN_SECRET is not set in environment variables!")
        else:
            logger.info(f"JWT_SECRET_KEY loaded (length: {len(self.JWT_SECRET_KEY)})")

        if not self.MONGO_URI:
            logger.error("MONGO_URI is not set in environment variables!")

settings = Settings()
