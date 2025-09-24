from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateMemoryRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Memory snippet text")
    type: str = Field(default="generic", description="Memory classification label")
    userId: Optional[str] = Field(default=None, description="Optional userId to associate with this memory")


class CreateMemoryResponse(BaseModel):
    id: str = Field(..., description="Created memory id/key")


class SearchResponseItem(BaseModel):
    id: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    userId: Optional[str] = Field(default=None)
    snippet: str


class HealthResponse(BaseModel):
    status: str
    redis_host: Optional[str]


