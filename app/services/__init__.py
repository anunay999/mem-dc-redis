"""Services module - External service integrations."""

from .redis_memory_service import RedisMemoryService
from .datacloud_service import DataCloudService

# Lazy initialization - services will be initialized on first use
redis_memory_service: RedisMemoryService | None = None
datacloud_service: DataCloudService | None = None

def get_redis_memory_service() -> RedisMemoryService:
    """Get or initialize the Redis Memory Service."""
    global redis_memory_service
    if redis_memory_service is None:
        redis_memory_service = RedisMemoryService()
    return redis_memory_service

def get_datacloud_service() -> DataCloudService:
    """Get or initialize the Data Cloud Service."""
    global datacloud_service
    if datacloud_service is None:
        datacloud_service = DataCloudService()
    return datacloud_service

__all__ = [
    "get_redis_memory_service",
    "get_datacloud_service",
    "RedisMemoryService",
    "DataCloudService"
]