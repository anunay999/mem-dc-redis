from __future__ import annotations

from typing import Optional, List, Dict, Any

from config import get_settings
from utils.redis_client import redis_vector_store
from schemas import SearchResponseItem
from utils.sf_auth_client import AuthResult, SalesforceAuthClient
import requests as _requests
import uuid as _uuid
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
    dc_response = ingest_memory_to_datacloud(payload, settings.dc_connector, settings.dc_dlo, token)

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

def ingest_memory_to_redis(snippet: str, memory_type: str = "generic", user_id: str | None = None) -> str:
    if not snippet or not snippet.strip():
        raise ValueError("snippet must be non-empty")
    from datetime import datetime, timezone

    mem_id = f"memories:{_uuid.uuid4().hex}"
    logger.info(
        "Adding text to Redis vector store: id=%s type=%s userId_set=%s",
        mem_id,
        memory_type,
        bool(user_id),
    )
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
    logger.info(f"Added to Redis with {ids[0] if ids else 'no ids'}")
    return ids[0] if ids else ""

def ingest_memory_to_datacloud(data: Dict[str, Any], connector: str, dlo: str, token: AuthResult) -> Dict[str, Any]:
    """Ingest a memory payload into Data Cloud using Salesforce OAuth token.

    - Fetches token and instance_url via SalesforceAuthClient
    - Builds ingestion URL as: https://{instance_url}/api/v1/ingest/sources/{connector}/{dlo}
    - Posts JSON payload and returns the parsed JSON response
    """
    if not connector or not connector.strip():
        raise ValueError("connector must be non-empty")
    if not dlo or not dlo.strip():
        raise ValueError("dlo must be non-empty")
    if not token or not token.instance_url:
        raise ValueError("token must be non-empty")

    # instance_url from token already contains scheme; remove scheme duplication if present
    # Prefer tenant-scoped URL if available
    instance = token.dcTenantUrl.rstrip("/")
    # Ensure we do not double-prefix scheme
    if instance.startswith("http://") or instance.startswith("https://"):
        base = instance
    else:
        base = f"https://{instance}"

    ingestion_endpoint = "api/v1/ingest/sources"
    url = f"{base}/{ingestion_endpoint}/{connector.strip()}/{dlo.strip()}"

    # Prefer tenant-scoped token if available
    bearer_token = token.dcTenantToken
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        logger.info(
            "POST Data Cloud ingest: url=%s connector=%s dlo=%s using_tenant_token=%s",
            url,
            connector,
            dlo,
            bool(token.dcTenantToken),
        )
        response = _requests.post(url, json=data, headers=headers, timeout=30)
        logger.info("Data Cloud ingest response: status=%s", response.status_code)
        response.raise_for_status()
        # Attempt to return JSON response; if none, return minimal dict
        try:
            return response.json()
        except Exception:
            return {"status_code": response.status_code, "text": response.text}
    except _requests.HTTPError as e:  # HTTP status errors
        status = e.response.status_code if e.response is not None else 0
        body = e.response.text if e.response is not None else str(e)
        raise _requests.HTTPError(f"HTTP error {status}: {body}", request=e.request, response=e.response)
    except _requests.RequestException as e:
        logger.error("Network error during Data Cloud ingest: %s", str(e))
        raise _requests.RequestException(f"Network error: {str(e)}")
