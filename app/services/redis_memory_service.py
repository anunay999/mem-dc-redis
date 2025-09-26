"""Redis Memory Service - Manages all Redis vector store operations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore
from langchain_core.documents import Document
from redisvl.query.filter import Tag

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
                        {"name": "status", "type": "tag"},
                        {"name": "title", "type": "text"},
                    ],
                ),
            )
            logger.info("Redis Memory Service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Redis Memory Service: %s", str(e))
            raise

    def add_memory(self, text: str, memory_type: str = "generic", user_id: Optional[str] = None, status: Optional[str] = None, memory_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Add or update a memory in the vector store (upsert functionality).

        Args:
            text: The memory text content
            memory_type: Type/category of the memory
            user_id: User ID associated with the memory
            status: Status of the memory (e.g., "active", "archived", "deleted")
            memory_id: Optional specific memory ID. If provided, uses this ID; otherwise generates new UUID

        Returns:
            Memory ID (provided or generated)

        Raises:
            ValueError: If text is empty
            RuntimeError: If vector store is not initialized
        """
        if not text or not text.strip():
            raise ValueError("text must be non-empty")

        if not self._vector_store:
            raise RuntimeError("Vector store not initialized")

        # Use provided memory_id or generate new UUID
        if memory_id:
            # Ensure memory_id has proper prefix if not already present
            mem_id = memory_id
        else:
            mem_id = f"{uuid.uuid4().hex}"

        logger.info(
            "Adding/updating memory in Redis: id=%s type=%s userId_set=%s status=%s upsert=%s, title=%s",
            mem_id,
            memory_type,
            bool(user_id),
            status,
            bool(memory_id),
            title
        )

        metadata = {
            "id": mem_id,
            "type": memory_type,
            "created_at": str(datetime.now(timezone.utc)),
            "userId": user_id or "unknown",
            "status": status,
            "title": title,
        }

        # Check if memory already exists and delete it for proper upsert
        existing_memory = self._vector_store.get_by_ids([mem_id])
        if existing_memory:
            logger.info("Memory already exists in Redis: id=%s, deleting for upsert", mem_id)
            try:
                # Delete the existing memory to avoid duplicates
                self._vector_store.delete([mem_id])
                logger.info("Successfully deleted existing memory: %s", mem_id)
            except Exception as e:
                logger.warning("Failed to delete existing memory %s: %s", mem_id, str(e))
        else:
            logger.info("Memory does not exist in Redis: id=%s, creating new", mem_id)

        # Add the memory (this will be a fresh insert after deletion)
        ids = self._vector_store.add_texts([text], [metadata], ids=[mem_id])
        logger.info("Memory added/updated in Redis with ID: %s", ids[0] if ids else "no ids")

        return mem_id  # Return the original memory ID

    def search_memories(
        self, 
        query: str, 
        k: int = 5, 
        status: Optional[str] = None,
        memory_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Tuple[Document, float]]:
        """Search for memories using semantic similarity with optional filtering.

        Args:
            query: Search query text
            k: Number of results to return
            status: Optional status filter (e.g., "active", "archived")
            memory_type: Optional memory type filter (e.g., "note", "task", "idea")
            user_id: Optional user ID filter

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

        # Build filter conditions
        filter_conditions = []
        
        if status:
            filter_conditions.append(Tag("status") == status)
        
        if memory_type:
            filter_conditions.append(Tag("type") == memory_type)
            
        if user_id:
            filter_conditions.append(Tag("userId") == user_id)

        logger.info(
            "Searching memories: query_len=%s k=%s status=%s type=%s userId=%s filters=%s", 
            len(query), k, status or "<any>", memory_type or "<any>", user_id or "<any>", len(filter_conditions)
        )

        # Combine filters with logical AND if multiple filters exist
        if filter_conditions:
            if len(filter_conditions) == 1:
                filter_condition = filter_conditions[0]
            else:
                # Combine multiple filters with AND operator
                filter_condition = filter_conditions[0]
                for condition in filter_conditions[1:]:
                    filter_condition = filter_condition & condition
            
            logger.info("Filter condition: %s", filter_condition)
            results = self._vector_store.similarity_search_with_score(query, k=k, filter=filter_condition)
        else:
            results = self._vector_store.similarity_search_with_score(query, k=k)

        logger.info("Search completed: %s results found", len(results))
        return results

    def get_memory_by_id(self, memory_id: str) -> Optional[Document]:
        """Get a specific memory by ID.

        Args:
            memory_id: The memory ID to retrieve

        Returns:
            Document if found, None otherwise

        Raises:
            RuntimeError: If vector store is not initialized
        """
        if not self._vector_store:
            raise RuntimeError("Vector store not initialized")

        # Extract just the hex part of the ID for Redis lookup
        if memory_id.startswith("memories:"):
            # Extract just the hex part if full ID is provided
            mem_id = memory_id.split(":")[-1]
        else:
            # Use the ID as-is (assuming it's the hex part)
            mem_id = memory_id

        logger.info("Getting memory by ID: %s (original: %s)", mem_id, memory_id)
        
        try:
            # Use get_by_ids to fetch the document directly
            documents = self._vector_store.get_by_ids([mem_id])
            if documents and len(documents) > 0:
                logger.info("Memory found: %s", mem_id)
                return documents[0]
            else:
                logger.info("Memory not found: %s", mem_id)
                return None
        except Exception as e:
            logger.error("Error retrieving memory %s: %s", mem_id, str(e))
            return None

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID.

        Args:
            memory_id: The memory ID to delete

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            RuntimeError: If vector store is not initialized
        """
        if not self._vector_store:
            raise RuntimeError("Vector store not initialized")

        # Extract just the hex part of the ID for Redis lookup
        if memory_id.startswith("memories:"):
            # Extract just the hex part if full ID is provided
            mem_id = memory_id.split(":")[-1]
        else:
            # Use the ID as-is (assuming it's the hex part)
            mem_id = memory_id

        logger.info("Deleting memory by ID: %s (original: %s)", mem_id, memory_id)
        
        try:
            # Check if memory exists first
            existing_memory = self._vector_store.get_by_ids([mem_id])
            if not existing_memory:
                logger.info("Memory not found for deletion: %s", mem_id)
                return False

            # Delete the memory
            result = self._vector_store.delete([mem_id])
            if result:
                logger.info("Memory deleted successfully: %s", mem_id)
                return True
            else:
                logger.warning("Memory deletion failed: %s", mem_id)
                return False
        except Exception as e:
            logger.error("Error deleting memory %s: %s", mem_id, str(e))
            return False

    @property
    def is_initialized(self) -> bool:
        """Check if the service is properly initialized."""
        return self._vector_store is not None and self._embeddings is not None