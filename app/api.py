from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from config import get_settings
from vector_store import create_memory, search_memories
from schemas import IngestRequest, IngestResponse, SearchResponseItem, HealthResponse


## Models are now centralized in schemas.py


app = FastAPI(title="Memory DC Redis API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", redis_host=settings.redis_host)


@app.post("/memories:ingest", response_model=IngestResponse)
def ingest(req: IngestRequest) -> IngestResponse:
    try:
        key = create_memory(snippet=req.text, memory_type=req.type, user_id=req.userId)
        if not key:
            raise HTTPException(status_code=500, detail="Failed to create memory")
        return IngestResponse(id=key)
    except ValueError as ve:  # validation from vector_store
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/memories:search", response_model=List[SearchResponseItem])
def search(
    query: str = Query(..., min_length=1, description="Search query text"),
    k: int = Query(5, ge=1, le=100, description="Top K results"),
    type: Optional[str] = Query(None, description="Optional type filter"),
) -> List[SearchResponseItem]:
    try:
        results: List[Dict[str, Any]] = search_memories(query=query, k=k, memory_type=type)
        return [SearchResponseItem(**r) for r in results]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err


# Optional: development entrypoint
def get_app() -> FastAPI:
    return app


