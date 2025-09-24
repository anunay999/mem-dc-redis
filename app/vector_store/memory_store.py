from __future__ import annotations

from typing import Optional, List, Dict, Any

from utils.redis_client import redis_vector_store
from schemas import SearchResponseItem
import uuid as _uuid


def create_memory(snippet: str, memory_type: str = "generic", user_id: str | None = None) -> str:
    if not snippet or not snippet.strip():
        raise ValueError("snippet must be non-empty")
    from datetime import datetime, timezone

    mem_id = f"memories:{_uuid.uuid4().hex}"
    ids = redis_vector_store.add_texts(
        [snippet],
        [
            {
                "id": mem_id,
                "type": memory_type,
                "created_at": str(datetime.now(timezone.utc)),
                "userId": user_id or "unknown",
            }
        ],
    )
    return ids[0] if ids else ""


def search_memories(query: str, k: int = 5, memory_type: Optional[str] = None) -> List[SearchResponseItem]:
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    if memory_type:
        from redisvl.query.filter import Tag

        docs = redis_vector_store.similarity_search(query, k=k, filter=Tag("type") == memory_type)
    else:
        docs = redis_vector_store.similarity_search(query, k=k)

    results: List[SearchResponseItem] = []
    for d in docs:
        results.append(
            SearchResponseItem(
                id=d.metadata.get("id") if isinstance(d.metadata, dict) else None,
                type=d.metadata.get("type") if isinstance(d.metadata, dict) else None,
                created_at=d.metadata.get("created_at") if isinstance(d.metadata, dict) else None,
                userId=d.metadata.get("userId") if isinstance(d.metadata, dict) else None,
                snippet=d.page_content,
            )
        )
    return results
