# mem-dc-redis

A comprehensive memory management system that provides bi-directional sync between Redis vector store and Salesforce Data Cloud. The system supports semantic memory search, status-based filtering, and upsert operations through both REST API and CLI interfaces.

## Features

- 🧠 **Memory Management**: Create, search, retrieve, and delete memories with rich metadata
- 🔍 **Semantic Search**: Vector-based similarity search using Google Gemini embeddings
- 🎯 **Advanced Filtering**: Filter by type, status, and user ID with logical combinations
- 🔄 **Upsert Operations**: Create new or update existing memories with custom IDs
- 📋 **CRUD Operations**: Complete Create, Read, Update, Delete functionality via API
- 🔑 **Flexible ID Handling**: Support for both full IDs and hex-only formats
- 🌐 **Dual Storage**: Automatic sync between Redis vector store and Salesforce Data Cloud
- 🚀 **FastAPI REST API**: Modern async API with automatic documentation
- 💻 **CLI Interface**: Command-line tools for memory operations
- ✅ **Comprehensive Testing**: Full API integration tests with error handling

## Quick Start

### Prerequisites

- Python 3.10+
- Redis Stack (for vector search)
- Google API key (for embeddings)
- Salesforce Data Cloud access (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mem-dc-redis

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Start the API Server

```bash
# Start development server
./start-api.sh

# Or manually
uv run fastapi dev app/api.py
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

## Configuration

Configure the following environment variables in `.env`:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Google AI (for embeddings)
GOOGLE_API_KEY=your_google_api_key

# Salesforce Data Cloud (optional)
SALESFORCE_BASE_URL=https://your-org.salesforce.com
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
DC_INGEST_CONNECTOR=your_connector
DC_DLO=your_dlo
```

## API Usage

### Create Memory

```bash
# Create new memory (auto-generated ID)
curl -X POST "http://localhost:8000/memories:create" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alice loves weekend hiking",
    "type": "personal",
    "status": "active"
  }'

# Upsert memory with specific ID
curl -X POST "http://localhost:8000/memories:create" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Alice really loves weekend hiking",
    "type": "personal",
    "memory_id": "alice-hiking-001",
    "status": "active"
  }'
```

### Search Memories

```bash
# Basic search
curl "http://localhost:8000/memories:search?query=hiking&k=5"

# Search with single filters
curl "http://localhost:8000/memories:search?query=weekend&status=active"
curl "http://localhost:8000/memories:search?query=work&type=task"
curl "http://localhost:8000/memories:search?query=notes&user_id=alice123"

# Search with OR status filter (multiple status values)
curl "http://localhost:8000/memories:search?query=project&status=active,consolidated"
curl "http://localhost:8000/memories:search?query=tasks&status=active,consolidated,archived"

# Search with multiple filters (logical AND between different filter types)
curl "http://localhost:8000/memories:search?query=weekend&status=active&type=personal&user_id=alice123&k=3"

# Combine OR status with other filters
curl "http://localhost:8000/memories:search?query=work&type=task&status=active,consolidated"
```

### Get Memory by ID

```bash

# Get memory by ID (prefix automatically handled)
curl "http://localhost:8000/memories/abc123def456"
```

### Delete Memory by ID

```bash
# Delete memory by ID
curl -X DELETE "http://localhost:8000/memories/abc123def456"
```

### API Response Format

**Memory Creation Response:**

```json
{
  "dc_status": "success",
  "redis_status": "memories:abc123..."
}
```

**Search Response:**

```json
[
  {
    "id": "memories:abc123...",
    "type": "personal",
    "created_at": "2024-01-15T10:30:00Z",
    "userId": "alice",
    "status": "active",
    "title": "Alice's Hiking Memory",
    "text": "Alice loves weekend hiking",
    "score": 0.95
  }
]
```

**Get Memory by ID Response:**

```json
{
  "id": "memories:abc123...",
  "type": "personal",
  "created_at": "2024-01-15T10:30:00Z",
  "userId": "alice",
  "status": "active",
  "title": "Alice's Hiking Memory",
  "text": "Alice loves weekend hiking",
  "score": null
}
```

**Delete Memory Response:**

```json
{
  "message": "Memory 'abc123...' deleted successfully",
  "deleted": true
}
```

## CLI Usage

### Create Memories

```bash
# Basic memory creation
uv run app/main.py create "Alice enjoys reading books"

# Create with type and status
uv run app/main.py create "Bob's work notes" --type work --status active

# Upsert with specific ID
uv run app/main.py create "Updated memory" --memory-id custom-001
```

### Search Memories

```bash
# Basic search
uv run app/main.py search "hiking adventures"

# Search with filters
uv run app/main.py search "weekend" --status active --k 3

# Search specific type
uv run app/main.py search "work" --type professional

# Search with multiple filters
uv run app/main.py search "notes" --type task --status active
```

## API Endpoints

### Complete REST API Reference

| Method   | Endpoint                | Description                  |
| -------- | ----------------------- | ---------------------------- |
| `POST`   | `/memories:create`      | Create or upsert memory      |
| `GET`    | `/memories:search`      | Search memories with filters |
| `GET`    | `/memories/{memory_id}` | Get specific memory by ID    |
| `DELETE` | `/memories/{memory_id}` | Delete memory by ID          |
| `GET`    | `/health`               | Health check                 |

### Query Parameters for Search

| Parameter | Type    | Description                                              | Example                                                  |
| --------- | ------- | -------------------------------------------------------- | -------------------------------------------------------- |
| `query`   | string  | Search query text (required)                             | `hiking`                                                 |
| `k`       | integer | Number of results (1-20, default: 5)                     | `10`                                                     |
| `type`    | string  | Memory type filter                                       | `task`, `idea`, `note`                                   |
| `status`  | string  | Memory status filter (supports OR with comma separation) | `active`, `active,consolidated`, `active,archived,draft` |
| `user_id` | string  | User ID filter                                           | `alice123`                                               |

## Memory Schema

Each memory contains the following metadata:

- **id**: Unique identifier (auto-generated or custom)
- **type**: Memory classification (personal, work, task, idea, note, etc.)
- **created_at**: Timestamp of creation
- **userId**: Associated user identifier
- **status**: Memory status (active, archived, deleted, etc.)
- **title**: Optional memory title
- **text**: The actual memory text content
- **score**: Similarity score (in search results, null for direct ID lookups)

## Architecture

### Service Layer

- **RedisMemoryService**: Handles Redis vector store operations
- **DataCloudService**: Manages Salesforce Data Cloud integration
- **Memory Store**: High-level memory operations combining both services

### Key Components

```
app/
├── api.py              # FastAPI REST endpoints
├── main.py             # CLI interface
├── config.py           # Configuration management
├── schemas.py          # Pydantic models
├── services/           # Business logic services
│   ├── redis_memory_service.py
│   └── datacloud_service.py
└── vector_store/       # Memory operations
    └── memory_store.py
```

## Status Management

Memories support flexible status management:

- **active**: Current, searchable memories (default)
- **archived**: Historical memories, searchable when needed
- **deleted**: Soft-deleted memories, can be filtered out
- **custom**: Any string value for specialized workflows

### Advanced Filtering

The system supports powerful filtering capabilities with logical AND combinations:

```bash
# API: Multiple filters (status AND type AND user)
curl "http://localhost:8000/memories:search?query=project&status=active&type=task&user_id=alice123"

# API: OR status filtering (status=active OR consolidated)
curl "http://localhost:8000/memories:search?query=project&status=active,consolidated"

# API: Complex combination (type=task AND (status=active OR consolidated))
curl "http://localhost:8000/memories:search?query=work&type=task&status=active,consolidated"

# CLI: Multiple filters
uv run app/main.py search "meeting" --status active --type note
```

### Memory Operations by ID

```bash
# API: Get memory by ID (flexible ID format)
curl "http://localhost:8000/memories/abc123def456"
curl "http://localhost:8000/memories/abc123def456"

# API: Delete memory by ID
curl -X DELETE "http://localhost:8000/memories/abc123def456"
```

## Health Check

Check system status:

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**: Ensure Redis Stack is running with vector search enabled
2. **Google API Errors**: Verify `GOOGLE_API_KEY` is set correctly
3. **Import Errors**: Run `uv sync` to ensure all dependencies are installed
4. **Memory Not Found (404)**: Check memory ID format - system accepts both hex and full IDs
5. **Search Returns No Results**: Verify filters are compatible and memory exists with specified criteria

### Logs

The application uses structured logging. Check logs for detailed error information:

```bash
# View API logs
tail -f logs/api.log

# CLI operations log to stdout
uv run app/main.py search "test" --verbose
```

### Manual Testing

```bash
# Start the API server
./start-api.sh

# Test in another terminal
curl -X POST "http://localhost:8000/memories:create" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test memory", "type": "test"}'

# Get the returned ID and test retrieval
curl "http://localhost:8000/memories/{memory_id}"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[MIT](LICENSE)
