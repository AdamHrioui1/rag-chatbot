import logging
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Explicit short timeouts so a MongoDB problem (network blocked, wrong
# URI, cluster paused, DNS issue with the mongodb+srv:// SRV lookup...)
# fails fast with a clear error instead of hanging the request forever -
# the driver's own defaults are generous enough to look like a hang.
_client = MongoClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
_db = _client[settings.MONGO_DB_NAME]
documents_collection = _db["documents"]


def _serialize(doc: dict) -> dict:
    """Convert Mongo's ObjectId to a plain string so it's JSON-serializable
    and safe to hand straight to a Pydantic response model."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


class DocumentRepository:
    """
    All MongoDB access for document metadata lives here, so the rest of
    the app never talks to pymongo directly. This is the single place
    that enforces "a document belongs to exactly one user".
    """

    def create(
        self,
        user_id: str,
        filename: str,
        stored_path: str,
        content_type: str,
        size_bytes: int,
        content_hash: str,
    ) -> dict:
        result = documents_collection.insert_one(
            {
                "user_id": user_id,
                "filename": filename,
                "stored_path": stored_path,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "content_hash": content_hash,
                "status": "processing",
                "chunk_count": 0,
                "error_message": None,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return self.get_by_id(str(result.inserted_id))

    def mark_ready(self, document_id: str, chunk_count: int) -> None:
        documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "ready", "chunk_count": chunk_count, "error_message": None}},
        )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        documents_collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "failed", "error_message": error_message}},
        )

    def get_by_id(self, document_id: str) -> dict | None:
        try:
            oid = ObjectId(document_id)
        except InvalidId:
            return None
        return _serialize(documents_collection.find_one({"_id": oid}))

    def get_by_id_for_user(self, document_id: str, user_id: str) -> dict | None:
        """
        Fetch a document only if it belongs to `user_id`. This is the
        authorization check every document read/delete route must use -
        we look up by (id AND user_id) together, rather than looking up
        by id alone and checking ownership afterwards, so there's no
        window where a document is returned before we know it's the
        caller's.
        """
        try:
            oid = ObjectId(document_id)
        except InvalidId:
            return None
        return _serialize(documents_collection.find_one({"_id": oid, "user_id": user_id}))

    def find_ready_duplicate(self, user_id: str, content_hash: str) -> dict | None:
        return _serialize(
            documents_collection.find_one(
                {"user_id": user_id, "content_hash": content_hash, "status": "ready"}
            )
        )

    def list_for_user(self, user_id: str) -> list[dict]:
        cursor = documents_collection.find({"user_id": user_id}).sort("created_at", -1)
        return [_serialize(doc) for doc in cursor]

    def count_ready_for_user(self, user_id: str) -> int:
        return documents_collection.count_documents({"user_id": user_id, "status": "ready"})

    def delete(self, document_id: str) -> None:
        documents_collection.delete_one({"_id": ObjectId(document_id)})


document_repository = DocumentRepository()
