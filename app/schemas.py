from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateMemoryRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Memory text")
    type: str = Field(default="generic", description="Memory classification label")
    memory_id: Optional[str] = Field(default=None, description="Optional memory ID for upsert functionality")
    status: str = Field(default="active", description="Memory status (e.g., active, archived, deleted)")
    title: Optional[str] = Field(default=None, description="Memory title")

class CreateMemoryResponse(BaseModel):
    dc_status: str = Field(..., description="Data Cloud status")
    redis_status: str = Field(..., description="Redis status")


class SearchResponseItem(BaseModel):
    id: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    userId: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    text: str = Field(..., description="Memory snippet")
    score: Optional[float] = Field(default=None, description="Memory score (None for direct ID lookups)")


class HealthResponse(BaseModel):
    status: str

