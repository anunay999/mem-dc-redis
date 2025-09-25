"""Redis Memory Service - Manages all Redis vector store operations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from langchain.docstore.document import Document

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisMemoryService:
    """Service class for managing Redis vector store operations."""

    def __init__(self):
        """Initialize Redis client and vector store."""
        self._vector_store: Optional[RedisVectorStore] = None
        self._embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize embeddings and vector store."""
        try:
            logger.info("Initializing Redis Memory Service")

            # Initialize embeddings
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=settings.google_api_key,
            )

            # Initialize vector store
            redis_url = settings.redis_url
            logger.info("Connecting to Redis at: %s", redis_url.split('@')[-1] if '@' in redis_url else redis_url)

            self._vector_store = RedisVectorStore(
                embeddings=self._embeddings,
                config=RedisConfig(
                    index_name="memories",
                    redis_url=redis_url,
                    metadata_schema=[
                        {"name": "id", "type": "tag"},
                        {"name": "type", "type": "tag"},
                        {"name": "created_at", "type": "text"},
                        {"name": "userId", "type": "tag"},
                    ],
                ),
            )
            logger.info("Redis Memory Service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Redis Memory Service: %s", str(e))
            raise

    def add_memory(self, snippet: str, memory_type: str = "generic", user_id: Optional[str] = None) -> str:
        """Add a memory to the vector store.

        Args:
            snippet: The memory text content
            memory_type: Type/category of the memory
            user_id: User ID associated with the memory

        Returns:
            Generated memory ID

        Raises:
            ValueError: If snippet is empty
            RuntimeError: If vector store is not initialized
        """
        if not snippet or not snippet.strip():
            raise ValueError("snippet must be non-empty")

        if not self._vector_store:
            raise RuntimeError("Vector store not initialized")

        mem_id = f"memories:{uuid.uuid4().hex}"

        logger.info(
            "Adding memory to Redis: id=%s type=%s userId_set=%s",
            mem_id,
            memory_type,
            bool(user_id),
        )

        metadata = {
            "id": mem_id,
            "type": memory_type,
            "created_at": str(datetime.now(timezone.utc)),
            "userId": user_id or "unknown",
        }

        ids = self._vector_store.add_texts([snippet], [metadata])
        logger.info("Memory added to Redis with ID: %s", ids[0] if ids else "no ids")

        return ids[0] if ids else ""

    def search_memories(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Search for memories using semantic similarity.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of (Document, score) tuples

        Raises:
            ValueError: If query is empty
            RuntimeError: If vector store is not initialized
        """
        if not query or not query.strip():
            raise ValueError("query must be non-empty")

        if not self._vector_store:
            raise RuntimeError("Vector store not initialized")

        logger.info("Searching memories: query_len=%s k=%s", len(query), k)

        # TODO: Add memory type filtering when needed
        results = self._vector_store.similarity_search_with_score(query, k=k)

        logger.info("Search completed: %s results found", len(results))
        return results

    def get_memory_by_id(self, memory_id: str) -> Optional[Document]:
        """Get a specific memory by ID.

        Args:
            memory_id: The memory ID to retrieve

        Returns:
            Document if found, None otherwise
        """
        # This would require implementing a direct Redis lookup
        # For now, we can search with a unique term and filter by ID
        logger.info("Getting memory by ID: %s", memory_id)
        # TODO: Implement direct ID lookup if needed
        return None

    @property
    def is_initialized(self) -> bool:
        """Check if the service is properly initialized."""
        return self._vector_store is not None and self._embeddings is not None