"""Redis client and LangChain RedisVectorStore factory (Gemini embeddings)."""

import logging
from redis import Redis
from config import get_settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore

settings = get_settings()
logger = logging.getLogger(__name__)

# Embeddings: Google Gemini via LangChain (defaults to 768-dim)
_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.google_api_key,
)

logger.info(
    "Redis connection: ",
    bool(getattr(settings, "redis_url", None)),
)

# Vector store configured once per process
try:
    logger.info("Initializing RedisVectorStore index=%s", "memories")
    redis_vector_store = RedisVectorStore(
        embeddings=_embeddings,
        config=RedisConfig(
            index_name="memories",
            redis_url=settings.redis_url,
            metadata_schema=[
                {"name": "id", "type": "tag"},
                {"name": "type", "type": "tag"},
                {"name": "created_at", "type": "text"},
                {"name": "userId", "type": "tag"},
            ],
        ),
    )
    logger.info("RedisVectorStore initialized successfully")
except Exception as e:  # noqa: BLE001
    logger.error("Failed to initialize RedisVectorStore: %s", str(e))
    raise