# mem-dc-redis

A comprehensive memory management system that provides bi-directional sync between Redis vector store and Salesforce Data Cloud. The system supports semantic memory search, status-based filtering, and upsert operations through both REST API and CLI interfaces.

## Features

- 🧠 **Memory Management**: Create, search, and manage memories with metadata
- 🔍 **Semantic Search**: Vector-based similarity search using Google Gemini embeddings
- 📊 **Status Filtering**: Filter memories by status (active, archived, deleted, etc.)
- 🔄 **Upsert Operations**: Create new or update existing memories with custom IDs
- 🌐 **Dual Storage**: Automatic sync between Redis vector store and Salesforce Data Cloud
- 🚀 **FastAPI REST API**: Modern async API with automatic documentation
- 💻 **CLI Interface**: Command-line tools for memory operations

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

# Search with filters
curl "http://localhost:8000/memories:search?query=weekend&status=active&type=personal&k=3"
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
    "text": "Alice loves weekend hiking",
    "score": 0.95
  }
]
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
```

## Memory Schema

Each memory contains the following metadata:

- **id**: Unique identifier (auto-generated or custom)
- **type**: Memory classification (personal, work, hobby, etc.)
- **created_at**: Timestamp of creation
- **userId**: Associated user identifier
- **status**: Memory status (active, archived, deleted, etc.)
- **text**: The actual memory text content
- **score**: Similarity score (in search results)

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

### Status Filtering

```bash
# API: Search only active memories
curl "http://localhost:8000/memories:search?query=text&status=active"

# CLI: Search archived memories
uv run app/main.py search "old notes" --status archived
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

### Logs

The application uses structured logging. Check logs for detailed error information:

```bash
# View API logs
tail -f logs/api.log

# CLI operations log to stdout
uv run app/main.py search "test" --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[MIT](LICENSE)
