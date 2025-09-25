from __future__ import annotations

from typing import Optional, List, Dict, Any

from config import get_settings
from services import get_redis_memory_service, get_datacloud_service
from schemas import SearchResponseItem
from utils.sf_auth_client import AuthResult, SalesforceAuthClient
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

def create_memory(snippet: str, memory_type: str = "generic") -> Dict[str, Any]:
    if not snippet or not snippet.strip():
        raise ValueError("snippet must be non-empty")
    from datetime import datetime, timezone

    client = SalesforceAuthClient()
    logger.info("Fetching Salesforce tokens for memory creation")
    token = client.get_token()

    logger.info("Ingesting memory to Data Cloud and Redis")

    mem_id = ingest_memory_to_redis(snippet, memory_type, token.userId).split("::")[-1]

    logger.info(f"Redis response: {mem_id}")

    payload = {
        "data": [
            {
                "id": mem_id,
                "text": snippet,
                "userId": token.userId,
                "created_at": str(datetime.now(timezone.utc)),
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


def search_memories(query: str, k: int = 5, memory_type: Optional[str] = None) -> List[SearchResponseItem]:
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    logger.info(
        "Searching memories: query_len=%s k=%s type=%s",
        len(query),
        k,
        memory_type or "<any>",
    )

    # Use Redis Memory Service for search
    redis_service = get_redis_memory_service()
    docs = redis_service.search_memories(query, k=k)

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
                snippet=d.page_content,
                score=score,
            )
        )
    return results

def search_memories_dc(query: str, user_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for memories in Data Cloud using vector search.

    Args:
        query: Search query text
        user_id: User ID for filtering (currently not used in SQL but logged)
        limit: Maximum number of results to return

    Returns:
        List of dictionaries containing search results from Data Cloud

    Raises:
        ValueError: If query is empty
        Exception: If authentication or Data Cloud request fails
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    logger.info(
        "Searching Data Cloud memories: query_len=%s user_id=%s limit=%s",
        len(query),
        user_id or "<any>",
        limit
    )

    try:
        # Get Salesforce authentication token
        client = SalesforceAuthClient()
        logger.info("Fetching Salesforce tokens for Data Cloud search")
        token = client.get_token()

        # Use DataCloud service for search
        datacloud_service = get_datacloud_service()
        dc_response = datacloud_service.search_relevant_memories(
            user_id=user_id or "unknown",
            utterance=query,
            limit=limit,
            token=token
        )

        logger.info("Data Cloud search completed successfully")

        # Parse and structure the response
        results = []
        if isinstance(dc_response, dict) and "data" in dc_response:
            for row in dc_response.get("data", []):
                result = {
                    "record_id": row.get("RecordId__c"),
                    "score": row.get("score__c"),
                    "chunk": row.get("Chunk__c"),
                    "source_value": row.get("value__c")
                }
                results.append(result)
                logger.debug(f"Data Cloud result: score={result['score']} chunk={str(result['chunk'])[:50]}...")

        logger.info(f"Data Cloud search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error("Data Cloud search failed: %s", str(e))
        raise Exception(f"Data Cloud search error: {str(e)}")

def ingest_memory_to_redis(snippet: str, memory_type: str = "generic", user_id: str | None = None) -> str:
    """Ingest memory using Redis Memory Service."""
    logger.info(
        "Adding memory via Redis Memory Service: type=%s userId_set=%s",
        memory_type,
        bool(user_id),
    )
    redis_service = get_redis_memory_service()
    return redis_service.add_memory(snippet, memory_type, user_id)

def ingest_memory_to_datacloud(data: Dict[str, Any], connector: str, dlo: str, token: AuthResult) -> Dict[str, Any]:
    """Ingest a memory payload into Data Cloud using DataCloudService.

    This function is kept for backward compatibility.
    Consider using DataCloudService directly for new code.
    """
    datacloud_service = get_datacloud_service()
    return datacloud_service.ingest_memory(data, connector, dlo, token)
