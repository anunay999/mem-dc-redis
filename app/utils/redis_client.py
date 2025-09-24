"""Redis client and LangChain RedisVectorStore factory (Gemini embeddings)."""

from redis import Redis
from config import get_settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_redis import RedisConfig, RedisVectorStore

settings = get_settings()


def get_redis_client() -> Redis:
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        username=settings.redis_username,
        password=settings.redis_password,
        decode_responses=True,
    )


def _build_redis_url() -> str:
    host = settings.redis_host or "localhost"
    port = settings.redis_port or 6379
    user = settings.redis_username
    pwd = settings.redis_password
    if user and pwd:
        return f"redis://{user}:{pwd}@{host}:{port}"
    return f"redis://{host}:{port}"


# Embeddings: Google Gemini via LangChain (defaults to 768-dim)
_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.google_api_key,
)


# Vector store configured once per process
redis_vector_store = RedisVectorStore(
    embeddings=_embeddings,
    config=RedisConfig(
        index_name="memories",
        redis_url=_build_redis_url(),
        metadata_schema=[
            {"name": "id", "type": "tag"},
            {"name": "type", "type": "tag"},
            {"name": "created_at", "type": "text"},
            {"name": "userId", "type": "tag"},
        ],
    ),
)