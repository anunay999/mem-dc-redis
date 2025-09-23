from __future__ import annotations

import time
import uuid
from typing import Optional, List, Dict, Any

import numpy as np
from redis import Redis
from redis.exceptions import ResponseError
from redis.commands.search.field import (
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

from utils import get_redis_client


INDEX_NAME = "idx:memories"
KEY_PREFIX = "mem:"
VECTOR_PATH = "$.embedding"
SNIPPET_PATH = "$.snippet"
TYPE_PATH = "$.type"
INDEX_DIM_KEY = "mem:index:dim"
INDEX_MODEL_KEY = "mem:index:model"

_embedder: Optional[SentenceTransformer] = None


def _get_embedder(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(model_name)
    return _embedder


def _ensure_index(client: Redis, vector_dimension: int, model_name: str) -> None:
    try:
        client.ft(INDEX_NAME).info()
        # Index exists; verify dimension
        try:
            dim_str = client.get(INDEX_DIM_KEY)
            if dim_str is not None:
                existing_dim = int(dim_str)
                if existing_dim != vector_dimension:
                    raise ValueError(
                        f"Existing index DIM={existing_dim} differs from embedding DIM={vector_dimension}. "
                        f"Either use a model that produces {existing_dim} dims or recreate the index and re-ingest."
                    )
            else:
                # Set if missing to avoid future ambiguity
                client.set(INDEX_DIM_KEY, str(vector_dimension))
                client.set(INDEX_MODEL_KEY, model_name)
        except Exception:
            # Best-effort; allow continuing if info keys aren't available
            pass
        return
    except ResponseError:
        pass

    schema = (
        TagField(TYPE_PATH, as_name="type"),
        TextField(SNIPPET_PATH, as_name="snippet"),
        VectorField(
            VECTOR_PATH,
            "FLAT",
            {"TYPE": "FLOAT32", "DIM": vector_dimension, "DISTANCE_METRIC": "COSINE"},
            as_name="vector",
        ),
    )
    definition = IndexDefinition(prefix=[KEY_PREFIX], index_type=IndexType.JSON)
    client.ft(INDEX_NAME).create_index(fields=schema, definition=definition)
    # Persist index configuration for later validation
    client.set(INDEX_DIM_KEY, str(vector_dimension))
    client.set(INDEX_MODEL_KEY, model_name)


def ingest_memory(snippet: str, memory_type: str = "generic", model_name: str = "all-MiniLM-L6-v2") -> str:
    if not snippet or not snippet.strip():
        raise ValueError("snippet must be non-empty")

    client = get_redis_client()
    embedder = _get_embedder(model_name)

    embedding = embedder.encode([snippet])[0].astype(np.float32).tolist()
    vector_dimension = len(embedding)

    _ensure_index(client, vector_dimension, model_name)

    key = f"{KEY_PREFIX}{uuid.uuid4()}"
    doc = {
        "type": memory_type,
        "snippet": snippet,
        "embedding": embedding,
        "created_at": int(time.time()),
    }

    client.json().set(key, "$", doc)
    return key

def search_memories(query: str, k: int = 5, memory_type: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2") -> List[Dict[str, Any]]:
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    client = get_redis_client()
    embedder = _get_embedder(model_name)

    q_embed = embedder.encode([query])[0]
    q_vec = np.array(q_embed, dtype=np.float32)

    # Validate against stored index dimension if present
    try:
        dim_str = client.get(INDEX_DIM_KEY)
        if dim_str is not None:
            expected_dim = int(dim_str)
            if q_vec.shape[-1] != expected_dim:
                raise ValueError(
                    f"Query embedding dim {q_vec.shape[-1]} does not match index dim {expected_dim}. "
                    f"Use a matching model or recreate the index and re-ingest."
                )
    except Exception:
        pass

    q_bytes = q_vec.tobytes()

    if memory_type:
        q = (
            Query(f"(@type:{{{memory_type}}})=>[KNN {int(k)} @vector $query_vector AS vector_score]")
            .sort_by("vector_score")
            .return_fields("vector_score", "id", "type", "snippet")
            .dialect(2)
        )
    else:
        q = (
            Query(f"(*)=>[KNN {int(k)} @vector $query_vector AS vector_score]")
            .sort_by("vector_score")
            .return_fields("vector_score", "id", "type", "snippet")
            .dialect(2)
        )

    docs = client.ft(INDEX_NAME).search(q, {"query_vector": q_bytes}).docs

    results: List[Dict[str, Any]] = []
    for d in docs:
        try:
            score = round(1.0 - float(d.vector_score), 4)
        except Exception:
            score = None
        results.append(
            {
                "id": d.id,
                "score": score,
                "type": getattr(d, "type", None),
                "snippet": getattr(d, "snippet", None),
            }
        )
    return results
