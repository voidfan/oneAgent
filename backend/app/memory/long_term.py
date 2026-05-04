"""Long-term memory - persistent knowledge using vector store."""
from typing import Optional

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class LongTermMemory:
    """Persistent memory using ChromaDB vector store for semantic search."""

    def __init__(self, collection_name: str = "agent_memory"):
        self.collection_name = collection_name
        self._collection = None
        self._client = None

    def _get_collection(self):
        """Lazy initialization of ChromaDB collection."""
        if self._collection is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                self._client = chromadb.Client(
                    ChromaSettings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory=settings.CHROMA_PERSIST_DIR,
                        anonymized_telemetry=False,
                    )
                )
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                logger.error("chroma_init_failed", error=str(e))
                raise
        return self._collection

    async def store(
        self,
        key: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Store content in long-term memory with vector embedding."""
        collection = self._get_collection()
        meta = metadata or {}
        meta["key"] = key

        collection.upsert(
            ids=[key],
            documents=[content],
            metadatas=[meta],
        )
        logger.info("memory_stored", key=key, collection=self.collection_name)
        return key

    async def retrieve(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """Retrieve relevant memories using semantic search."""
        collection = self._get_collection()

        query_params = {
            "query_texts": [query],
            "n_results": n_results,
        }
        if where:
            query_params["where"] = where

        results = collection.query(**query_params)

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "id": results["ids"][0][i] if results["ids"] else None,
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return memories

    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        try:
            collection = self._get_collection()
            collection.delete(ids=[key])
            return True
        except Exception as e:
            logger.error("memory_delete_failed", key=key, error=str(e))
            return False

    async def clear(self) -> None:
        """Clear all memories in this collection."""
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
            except Exception as e:
                logger.error("memory_clear_failed", error=str(e))
