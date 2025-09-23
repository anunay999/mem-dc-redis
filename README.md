## mem-dc-redis

Framework scaffolding for bi-directional memory sync between a Redis vector store and a Data Cloud. It is designed to:

- Export memories from Redis (vector index) into a Data Cloud dataset/table
- Import memories from Data Cloud back into Redis (upsert) to keep both sides in sync

This README outlines the intended architecture, data model, configuration, and flows so implementation can proceed in small, testable steps.

### Scope and assumptions

- **Redis vector store**: Assumes Redis Stack with RediSearch for HNSW vector similarity. Embeddings are stored alongside metadata.
- **Data Cloud**: Abstracted as a pluggable destination/source (e.g., Salesforce Data Cloud, Snowflake, BigQuery, or any warehouse/lake with an ingestion API). Vendor wiring will be implemented behind a provider interface.
