from __future__ import annotations

from typing import Optional, List, Dict, Any

from config import get_settings
from services import get_redis_memory_service, get_datacloud_service
from schemas import SearchResponseItem
from utils.sf_auth_client import AuthResult, SalesforceAuthClient
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

def create_memory(text: str, memory_type: str = "generic", memory_id: str | None = None, title: str | None = None) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("text must be non-empty")
    from datetime import datetime, timezone

    client = SalesforceAuthClient()
    logger.info("Fetching Salesforce tokens for memory creation")
    token = client.get_token()

    logger.info("Ingesting memory to Data Cloud and Redis (upsert: %s)", bool(memory_id))

    # Pass memory_id to ingest_memory_to_redis for upsert functionality
    returned_id = ingest_memory_to_redis(text, memory_type, token.userId, "active", memory_id, title)
    mem_id = returned_id.split("::")[-1]

    logger.info(f"Redis response: {mem_id}")

    payload = {
        "data": [
            {
                "id": mem_id,
                "text": text,
                "userId": token.userId,
                "created_at": str(datetime.now(timezone.utc)),
                "title": title,
            }
        ]
    }
    datacloud_service = get_datacloud_service()
    dc_response = datacloud_service.ingest_memory(payload, settings.dc_connector, settings.dc_dlo, token)

    logger.info(f"DC response: {dc_response}")
    logger.info(f"Redis response: {mem_id}")

    # Normalize dc_status to a string for API schema
    if isinstance(dc_response, dict):
        if "accepted" in dc_response:
            dc_status = "accepted" if dc_response.get("accepted") else "rejected"
        elif "status" in dc_response:
            dc_status = str(dc_response.get("status"))
        else:
            dc_status = "success"
    else:
        dc_status = str(dc_response)

    return {"dc_status": dc_status, "redis_status": mem_id}


def search_memories(
    query: str, 
    k: int = 5, 
    memory_type: Optional[str] = None, 
    status: Optional[str] = None, 
    user_id: Optional[str] = None
) -> List[SearchResponseItem]:
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    logger.info(
        "Searching memories: query_len=%s k=%s type=%s status=%s user_id=%s",
        len(query),
        k,
        memory_type or "<any>",
        status or "<any>",
        user_id or "<any>",
    )

    # Use Redis Memory Service for search with enhanced filtering
    redis_service = get_redis_memory_service()
    docs = redis_service.search_memories(
        query, 
        k=k, 
        status=status, 
        memory_type=memory_type, 
        user_id=user_id
    )

    logger.info(f"Search results with scores: {len(docs)} results")

    results: List[SearchResponseItem] = []
    for d, score in docs:
        logger.info(f"Search result: {d.page_content[:50]}... (score: {score:.4f})")
        results.append(
            SearchResponseItem(
                id=d.metadata.get("id") if isinstance(d.metadata, dict) else None,
                type=d.metadata.get("type") if isinstance(d.metadata, dict) else None,
                created_at=d.metadata.get("created_at") if isinstance(d.metadata, dict) else None,
                userId=d.metadata.get("userId") if isinstance(d.metadata, dict) else None,
                status=d.metadata.get("status") if isinstance(d.metadata, dict) else None,
                text=d.page_content,
                score=score,
                title=d.metadata.get("title") if isinstance(d.metadata, dict) else None,
            )
        )
    return results
    
def ingest_memory_to_redis(text: str, memory_type: str = "generic", user_id: str | None = None, status: str | None = None, memory_id: str | None = None, title: str | None = None) -> str:
    """Ingest memory using Redis Memory Service."""
    logger.info(
        "Adding memory via Redis Memory Service: type=%s userId_set=%s status=%s memory_id=%s title=%s",
        memory_type,
        bool(user_id),
        status,
        memory_id,
        title,
    )
    redis_service = get_redis_memory_service()
    return redis_service.add_memory(text, memory_type, user_id, status, memory_id, title)

def get_memory_by_id(memory_id: str) -> Optional[SearchResponseItem]:
    """Get a specific memory by ID.
    
    Args:
        memory_id: The memory ID to retrieve
        
    Returns:
        SearchResponseItem if found, None otherwise
        
    Raises:
        ValueError: If memory_id is empty
    """
    if not memory_id or not memory_id.strip():
        raise ValueError("memory_id must be non-empty")
    
    logger.info("Getting memory by ID: %s", memory_id)
    
    redis_service = get_redis_memory_service()
    document = redis_service.get_memory_by_id(memory_id)
    
    if document:
        logger.info("Memory found: %s", memory_id)
        return SearchResponseItem(
            id=document.metadata.get("id") if isinstance(document.metadata, dict) else None,
            type=document.metadata.get("type") if isinstance(document.metadata, dict) else None,
            created_at=document.metadata.get("created_at") if isinstance(document.metadata, dict) else None,
            userId=document.metadata.get("userId") if isinstance(document.metadata, dict) else None,
            status=document.metadata.get("status") if isinstance(document.metadata, dict) else None,
            text=document.page_content,
            score=None,  # No score for direct ID lookup
            title=document.metadata.get("title") if isinstance(document.metadata, dict) else None,
        )
    else:
        logger.info("Memory not found: %s", memory_id)
        return None


def delete_memory_by_id(memory_id: str) -> bool:
    """Delete a specific memory by ID.
    
    Args:
        memory_id: The memory ID to delete
        
    Returns:
        True if deleted successfully, False otherwise
        
    Raises:
        ValueError: If memory_id is empty
    """
    if not memory_id or not memory_id.strip():
        raise ValueError("memory_id must be non-empty")
    
    logger.info("Deleting memory by ID: %s", memory_id)
    
    redis_service = get_redis_memory_service()
    success = redis_service.delete_memory(memory_id)
    
    if success:
        logger.info("Memory deleted successfully: %s", memory_id)
    else:
        logger.warning("Memory deletion failed: %s", memory_id)
    
    return success


def ingest_memory_to_datacloud(data: Dict[str, Any], connector: str, dlo: str, token: AuthResult) -> Dict[str, Any]:
    """Ingest a memory payload into Data Cloud using DataCloudService.

    This function is kept for backward compatibility.
    Consider using DataCloudService directly for new code.
    """
    datacloud_service = get_datacloud_service()
    return datacloud_service.ingest_memory(data, connector, dlo, token)
