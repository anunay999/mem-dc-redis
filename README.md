## mem-dc-redis

Framework scaffolding for bi-directional memory sync between a Redis vector store and a Data Cloud. It is designed to:

- Export memories from Redis (vector index) into a Data Cloud dataset/table
- Import memories from Data Cloud back into Redis (upsert) to keep both sides in sync

This README outlines the intended architecture, data model, configuration, and flows so implementation can proceed in small, testable steps.

### Scope and assumptions

- **Redis vector store**: Assumes Redis Stack with RediSearch for HNSW vector similarity. Embeddings are stored alongside metadata.
- **Data Cloud**: Abstracted as a pluggable destination/source (e.g., Salesforce Data Cloud, Snowflake, BigQuery, or any warehouse/lake with an ingestion API). Vendor wiring will be implemented behind a provider interface.
- **Python 3.10+**: See `.python-version`.

## Architecture

- **Connectors**
  - **RedisConnector**: Read/query from Redis vector index; write/upsert memories.
  - **DataCloudConnector**: Write batch records to Data Cloud; read/paginate new or updated records. Concrete providers implement auth and I/O specifics.
- **Transforms**
  - Normalize records to a canonical `Memory` model; serialize/deserialize embeddings and metadata.
- **Orchestrators**
  - `export_redis_to_dc`: Incremental export from Redis to Data Cloud with idempotency.
  - `import_dc_to_redis`: Incremental import from Data Cloud to Redis with conflict resolution.
- **State/Offsets**
  - Track high-water marks (timestamps, version, sequence) to support resumable sync.

```
Redis (HNSW index)  <——>  Transform  <——>  Provider(Data Cloud)
       ^ export                        import v
     State/offsets persisted (e.g., key in Redis or file/DB)
```

## Data model

Canonical `Memory` record (fields can be extended):

- **id**: Stable unique identifier
- **subjectId**: Owner or grouping key (e.g., userId, sessionId)
- **text**: Raw memory content
- **embedding**: Vector of float32 (or a serialized form)
- **metadata**: JSON-serializable auxiliary data (source, score, tags, timestamps)
- **updatedAt**: ISO-8601 last update timestamp for incremental sync

### Redis schema (reference)

- Keys: `memory:{id}` storing fields as Hash (HSET)
- Index: RediSearch FT index with HNSW vector field

```redis
FT.CREATE idx:memory ON HASH PREFIX 1 memory: SCHEMA \
  id TAG \
  subjectId TAG \
  text TEXT \
  metadata TEXT \
  updatedAt TAG \
  embedding VECTOR HNSW 6 TYPE FLOAT32 DIM 1536 DISTANCE_METRIC COSINE
```

> Note: Adjust DIM and metric to your embedding model.

### Data Cloud schema (reference)

Target table/dataset with at least:

- `MemoryId` (string, primary key)
- `SubjectId` (string)
- `Text` (string)
- `Embedding` (array<float> or base64-encoded bytes) — optional if Data Cloud does not store vectors
- `Metadata` (variant/json)
- `UpdatedAt` (timestamp)

## Configuration

Environment variables (example — finalized during implementation):

- `REDIS_URL` — e.g., `redis://localhost:6379`
- `REDIS_INDEX` — e.g., `idx:memory`
- `REDIS_KEY_PREFIX` — e.g., `memory:`
- `EMBEDDING_DIM` — e.g., `1536`
- `DC_PROVIDER` — e.g., `salesforce|snowflake|custom`
- Provider-specific auth (e.g., `DC_CLIENT_ID`, `DC_CLIENT_SECRET`, `DC_TENANT`, `DC_ENDPOINT`, etc.)

Optional mapping config (to be added later) to translate field names/types between Redis and Data Cloud.

## Flows

### Export: Redis → Data Cloud

1. Scan Redis for changed/new records since last `UpdatedAt` (or via keyspace tracking)
2. Transform to canonical `Memory`
3. Batch write to Data Cloud via provider
4. Update high-water mark/state

### Import: Data Cloud → Redis

1. Read new/updated rows from Data Cloud since last offset
2. Transform to canonical `Memory`
3. Upsert into Redis hash; update embedding and fields; reindex automatically via RediSearch
4. Update high-water mark/state

### Idempotency and conflict resolution

- Prefer last-writer-wins by `UpdatedAt`, with deterministic tiebreakers
- Use upsert semantics on both sides; batch retries are safe

## Development

```bash
uv sync
```

### Minimal vector memory ingestion

The project includes a very small Redis JSON-based vector memory store inspired by the Redis vector database quick start guide [reference](https://redis.io/docs/latest/develop/get-started/vector-database/).

Requirements:

- Redis Stack with RediSearch and RedisJSON available (e.g., local Redis Stack or Redis Cloud)
- Set `REDIS_HOST`, `REDIS_PORT`, and optional `REDIS_USERNAME`/`REDIS_PASSWORD` in `.env`

Usage:

```bash
uv run app/main.py ingest "Alice likes hiking on weekends" --type user
# prints created key, e.g., mem:3f2f2c6d-...
```

This will:

- Create an embedding with `sentence-transformers` (`msmarco-distilbert-base-v4`)
- Ensure a RediSearch JSON index `idx:memories` with a vector field exists
- Store the JSON document under prefix `mem:` with fields: `type`, `snippet`, `embedding`, `created_at`

## Roadmap

- Implement provider interface and a minimal provider (e.g., file-based or Snowflake/Salesforce)
- Add `RedisConnector` with HNSW vector read/write helpers
- Add orchestrators for export/import with offset persistence
- Provide config file and env var loading
- Add small CLI: `memdc export|import --since ...` with dry-run mode
- Add tests with a local Redis Stack and a mock Data Cloud provider

## License

See `LICENSE`.
