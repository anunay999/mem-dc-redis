from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
import logging

from config import get_settings
from vector_store import create_memory, search_memories, get_memory_by_id, delete_memory_by_id
from schemas import CreateMemoryRequest, CreateMemoryResponse, SearchResponseItem, HealthResponse


## Models are now centralized in schemas.py


app = FastAPI(title="Memory DC Redis API", version="0.1.0")
logger = logging.getLogger(__name__)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    logger.info("/health requested")
    return HealthResponse(status="ok")


@app.post("/memories:create", response_model=CreateMemoryResponse)
def create(req: CreateMemoryRequest) -> CreateMemoryResponse:
    try:
        logger.info(
            "/memories:create called: text_len=%s type=%s memory_id=%s status=%s title=%s",
            len(req.text) if req.text else 0,
            req.type,
            req.memory_id,
            req.status,
            req.title,
        )
        response = create_memory(text=req.text, memory_type=req.type, memory_id=req.memory_id, title=req.title, status=req.status)
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
    type: Optional[str] = Query(None, description="Optional memory type filter (e.g., task, idea, note)"),
    status: Optional[str] = Query(None, description="Optional status filter (e.g., active, archived)"),
    user_id: Optional[str] = Query(None, description="Optional user ID filter"),
) -> List[SearchResponseItem]:
    try:
        logger.info(
            "/memories:search called: query_len=%s k=%s type=%s status=%s user_id=%s",
            len(query),
            k,
            type or "<any>",
            status or "<any>",
            user_id or "<any>",
        )
        results = search_memories(
            query=query, 
            k=k, 
            memory_type=type, 
            status=status, 
            user_id=user_id
        )
        logger.info("/memories:search success: results=%s", len(results))
        return results
    except ValueError as ve:
        logger.warning("/memories:search validation error: %s", str(ve))
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as err:  # noqa: BLE001
        logger.error("/memories:search failed: %s", str(err))
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/memories/{memory_id}", response_model=SearchResponseItem)
def get_memory(memory_id: str) -> SearchResponseItem:
    """Get a specific memory by ID."""
    try:
        logger.info("/memories/%s called", memory_id)
        
        memory = get_memory_by_id(memory_id)
        if not memory:
            logger.warning("/memories/%s not found", memory_id)
            raise HTTPException(status_code=404, detail=f"Memory with ID '{memory_id}' not found")
        
        logger.info("/memories/%s success", memory_id)
        return memory
    except ValueError as ve:
        logger.warning("/memories/%s validation error: %s", memory_id, str(ve))
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as err:  # noqa: BLE001
        logger.error("/memories/%s failed: %s", memory_id, str(err))
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.delete("/memories/{memory_id}")
def delete_memory(memory_id: str) -> Dict[str, Any]:
    """Delete a specific memory by ID."""
    try:
        logger.info("/memories/%s DELETE called", memory_id)
        
        success = delete_memory_by_id(memory_id)
        if not success:
            logger.warning("/memories/%s DELETE not found or failed", memory_id)
            raise HTTPException(status_code=404, detail=f"Memory with ID '{memory_id}' not found or could not be deleted")
        
        logger.info("/memories/%s DELETE success", memory_id)
        return {"message": f"Memory '{memory_id}' deleted successfully", "deleted": True}
    except ValueError as ve:
        logger.warning("/memories/%s DELETE validation error: %s", memory_id, str(ve))
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as err:  # noqa: BLE001
        logger.error("/memories/%s DELETE failed: %s", memory_id, str(err))
        raise HTTPException(status_code=500, detail=str(err)) from err


# Optional: development entrypoint
def get_app() -> FastAPI:
    return app


