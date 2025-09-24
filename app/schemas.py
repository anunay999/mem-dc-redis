from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateMemoryRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Memory snippet text")
    type: str = Field(default="generic", description="Memory classification label")

class CreateMemoryResponse(BaseModel):
    dc_status: str = Field(..., description="Data Cloud status")
    redis_status: str = Field(..., description="Redis status")


class SearchResponseItem(BaseModel):
    id: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    userId: Optional[str] = Field(default=None)
    snippet: str


class HealthResponse(BaseModel):
    status: str
    redis_host: Optional[str]


