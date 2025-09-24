from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
import logging
from pydantic import BaseModel, Field

from config import get_settings
from vector_store import create_memory, search_memories
from schemas import CreateMemoryRequest, CreateMemoryResponse, SearchResponseItem, HealthResponse


## Models are now centralized in schemas.py


app = FastAPI(title="Memory DC Redis API", version="0.1.0")
logger = logging.getLogger(__name__)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    logger.info("/health requested")
    return HealthResponse(status="ok", redis_host=settings.redis_host)


@app.post("/memories:create", response_model=CreateMemoryResponse)
def create(req: CreateMemoryRequest) -> CreateMemoryResponse:
    try:
        logger.info(
            "/memories:create called: text_len=%s type=%s",
            len(req.text) if req.text else 0,
            req.type,
        )
        response = create_memory(snippet=req.text, memory_type=req.type)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to create memory")
        logger.info("/memories:create success: id=%s", response)
        return CreateMemoryResponse(dc_status=response["dc_status"], redis_status=response["redis_status"])
    except ValueError as ve:  # validation from vector_store
        logger.warning("/memories:create validation error: %s", str(ve))
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as err:  # noqa: BLE001
        logger.error("/memories:create failed: %s", str(err))
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/memories:search", response_model=List[SearchResponseItem])
def search(
    query: str = Query(..., min_length=1, description="Search query text"),
    k: int = Query(5, ge=1, le=20, description="Top K results"),
    type: Optional[str] = Query(None, description="Optional type filter"),
) -> List[SearchResponseItem]:
    try:
        logger.info(
            "/memories:search called: query_len=%s k=%s type=%s",
            len(query),
            k,
            type or "<any>",
        )
        results = search_memories(query=query, k=k, memory_type=type)
        logger.info("/memories:search success: results=%s", len(results))
        return results
    except ValueError as ve:
        logger.warning("/memories:search validation error: %s", str(ve))
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as err:  # noqa: BLE001
        logger.error("/memories:search failed: %s", str(err))
        raise HTTPException(status_code=500, detail=str(err)) from err


# Optional: development entrypoint
def get_app() -> FastAPI:
    return app


