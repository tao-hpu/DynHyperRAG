# HyperGraphRAG Visualization API

FastAPI backend for HyperGraphRAG visualization and query interface.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
# Development mode (with auto-reload)
python api/main.py

# Or using uvicorn directly
uvicorn api.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Project Structure

```
api/
├── __init__.py           # Package initialization
├── main.py              # FastAPI application entry point
├── models/              # Pydantic data models
│   └── __init__.py
├── routes/              # API route handlers
│   └── __init__.py
└── services/            # Business logic layer
    ├── __init__.py
    └── graph_service.py # HyperGraphRAG wrapper
```

## API Endpoints

### Health Check
- `GET /api/health` - Check API status

### Graph Data (Coming Soon)
- `GET /api/graph/nodes` - Get entity nodes
- `GET /api/graph/edges` - Get hyperedges
- `GET /api/graph/stats` - Get graph statistics
- `GET /api/graph/search` - Search nodes

### Query (Coming Soon)
- `POST /api/query/` - Execute RAG query

## Configuration

The API uses the existing `config.py` and `.env` configuration:

```bash
# .env
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Development

### Adding New Routes

1. Create route file in `api/routes/`
2. Import and register in `api/main.py`:

```python
from api.routes import graph
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
```

### Adding New Services

1. Create service file in `api/services/`
2. Import in route handlers

## Testing

```bash
# Run tests (to be added)
pytest tests/
```

## Deployment

See `docker-compose.yml` for containerized deployment.
