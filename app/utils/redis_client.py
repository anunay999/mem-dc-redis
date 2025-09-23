"""Redis client factory.

Usage:
    from app.redis.client import get_redis_client
    r = get_redis_client()
"""

from redis import Redis
from config import get_settings

settings = get_settings()


def get_redis_client() -> Redis:
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        username=settings.redis_username,
        password=settings.redis_password,
        decode_responses=True,
    )

