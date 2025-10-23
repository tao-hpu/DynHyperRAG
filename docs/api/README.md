# HyperGraphRAG Visualization API Documentation

## Overview

The HyperGraphRAG Visualization API provides RESTful endpoints for accessing hypergraph data and executing RAG queries. Built with FastAPI, it offers automatic OpenAPI documentation, type validation, and high performance.

**Base URL**: `http://localhost:3401/api`

**API Version**: 1.0.0

## Quick Start

### Starting the API Server

```bash
# Development mode (with auto-reload)
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload

# Production mode
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401
```

### Interactive Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:3401/docs
- **ReDoc**: http://localhost:3401/redoc
- **OpenAPI JSON**: http://localhost:3401/openapi.json

## Authentication

Currently, the API does not require authentication. This may be added in future versions.

## API Endpoints

### Health & Status

#### `GET /api/health`

Health check endpoint to verify the API is running.

**Response:**
```json
{
  "status": "ok",
  "service": "HyperGraphRAG Visualization API",
  "version": "1.0.0"
}
```

---

## Graph Endpoints

### Get Nodes

#### `GET /api/graph/nodes`

Retrieve entity nodes with pagination and filtering.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of nodes to return (1-10000, default: 100)
- `offset` (integer, optional): Number of nodes to skip for pagination (default: 0)
- `entity_type` (string, optional): Filter by entity type (e.g., "DISEASE", "PERSON")

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/nodes?limit=10&entity_type=DISEASE"
```

**Example Response:**
```json
[
  {
    "id": "hypertension",
    "label": "Hypertension",
    "type": "DISEASE",
    "description": "A condition characterized by elevated blood pressure",
    "weight": 0.95,
    "relevanceScore": null
  },
  {
    "id": "diabetes",
    "label": "Diabetes",
    "type": "DISEASE",
    "description": "A metabolic disorder affecting blood sugar regulation",
    "weight": 0.92,
    "relevanceScore": null
  }
]
```

---

### Get Node by ID

#### `GET /api/graph/nodes/{node_id}`

Retrieve detailed information about a specific node.

**Path Parameters:**
- `node_id` (string, required): Unique node identifier

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/nodes/hypertension"
```

**Example Response:**
```json
{
  "id": "hypertension",
  "label": "Hypertension",
  "type": "DISEASE",
  "description": "A condition characterized by elevated blood pressure",
  "weight": 0.95,
  "relevanceScore": null
}
```

**Error Responses:**
- `404 Not Found`: Node does not exist
- `500 Internal Server Error`: Server error

---

### Get Edges

#### `GET /api/graph/edges`

Retrieve edges (including hyperedges) with pagination and filtering.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of edges to return (1-10000, default: 100)
- `offset` (integer, optional): Number of edges to skip for pagination (default: 0)
- `min_weight` (float, optional): Minimum edge weight threshold (0.0-1.0)

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/edges?limit=5&min_weight=0.8"
```

**Example Response:**
```json
[
  {
    "id": "hypertension-diabetes-<hyperedge>123",
    "source": "hypertension",
    "target": "diabetes",
    "relation": "connected_via",
    "description": "Both conditions are risk factors for cardiovascular disease",
    "weight": 0.88,
    "entities": ["hypertension", "diabetes", "cardiovascular_disease"],
    "isHyperedge": true
  }
]
```

---

### Get Edge by ID

#### `GET /api/graph/edges/{edge_id}`

Retrieve detailed information about a specific edge.

**Path Parameters:**
- `edge_id` (string, required): Edge identifier (format: "source-target")

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/edges/hypertension-diabetes"
```

**Error Responses:**
- `404 Not Found`: Edge does not exist
- `500 Internal Server Error`: Server error

---

### Get Graph Statistics

#### `GET /api/graph/stats`

Retrieve overview statistics about the hypergraph.

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/stats"
```

**Example Response:**
```json
{
  "numNodes": 1523,
  "numEdges": 4892,
  "numHyperedges": 342,
  "avgDegree": 6.42,
  "density": 0.0042
}
```

**Response Fields:**
- `numNodes`: Total number of entity nodes
- `numEdges`: Total number of edges (including hyperedges)
- `numHyperedges`: Number of hyperedges (connecting 3+ entities)
- `avgDegree`: Average node degree
- `density`: Graph density (0.0-1.0)

---

### Get Subgraph

#### `GET /api/graph/subgraph`

Extract a subgraph by expanding from a center node using BFS.

**Query Parameters:**
- `center_node_id` (string, required): ID of the center node
- `depth` (integer, optional): Number of hops to expand (1-3, default: 1)

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/subgraph?center_node_id=hypertension&depth=2"
```

**Example Response:**
```json
{
  "nodes": [
    {
      "id": "hypertension",
      "label": "Hypertension",
      "type": "DISEASE",
      "description": "...",
      "weight": 0.95
    },
    {
      "id": "diabetes",
      "label": "Diabetes",
      "type": "DISEASE",
      "description": "...",
      "weight": 0.92
    }
  ],
  "edges": [
    {
      "id": "hypertension-diabetes",
      "source": "hypertension",
      "target": "diabetes",
      "relation": "connected_via",
      "description": "...",
      "weight": 0.88,
      "entities": ["hypertension", "diabetes"],
      "isHyperedge": false
    }
  ]
}
```

**Error Responses:**
- `404 Not Found`: Center node not found or has no neighbors
- `500 Internal Server Error`: Server error

---

### Search Nodes

#### `GET /api/graph/search`

Search entity nodes using semantic vector similarity.

**Query Parameters:**
- `keyword` (string, required): Search query (minimum 1 character)
- `limit` (integer, optional): Maximum number of results (1-100, default: 20)

**Example Request:**
```bash
curl "http://localhost:3401/api/graph/search?keyword=blood%20pressure&limit=5"
```

**Example Response:**
```json
[
  {
    "id": "hypertension",
    "label": "Hypertension",
    "type": "DISEASE",
    "description": "A condition characterized by elevated blood pressure",
    "weight": 0.95,
    "relevanceScore": 0.92
  },
  {
    "id": "systolic_pressure",
    "label": "Systolic Pressure",
    "type": "MEASUREMENT",
    "description": "The pressure in arteries during heart contraction",
    "weight": 0.87,
    "relevanceScore": 0.85
  }
]
```

**Note**: Results are sorted by relevance score (highest first).

---

## Query Endpoints

### Execute Query

#### `POST /api/query/`

Execute a RAG query using the hypergraph knowledge base.

**Request Body:**
```json
{
  "query": "What are the risk factors for cardiovascular disease?",
  "mode": "hybrid",
  "top_k": 60,
  "max_token_for_text_unit": 4000,
  "max_token_for_local_context": 4000,
  "max_token_for_global_context": 4000
}
```

**Request Fields:**
- `query` (string, required): Query text
- `mode` (string, optional): Query mode - "local", "global", "hybrid", or "naive" (default: "hybrid")
- `top_k` (integer, optional): Number of entities/relationships to retrieve (default: 60)
- `max_token_for_text_unit` (integer, optional): Max tokens for text chunks (default: 4000)
- `max_token_for_local_context` (integer, optional): Max tokens for entity descriptions (default: 4000)
- `max_token_for_global_context` (integer, optional): Max tokens for relationship descriptions (default: 4000)

**Query Modes:**
- **local**: Entity-focused retrieval (uses entity descriptions)
- **global**: Relationship-focused retrieval (uses relationship descriptions)
- **hybrid**: Combines both local and global (recommended)
- **naive**: Simple RAG without graph structure

**Example Request:**
```bash
curl -X POST "http://localhost:3401/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the risk factors for cardiovascular disease?",
    "mode": "hybrid",
    "top_k": 60
  }'
```

**Example Response:**
```json
{
  "answer": "The main risk factors for cardiovascular disease include hypertension, diabetes, high cholesterol, smoking, obesity, and sedentary lifestyle...",
  "queryPath": {
    "nodes": ["cardiovascular_disease", "hypertension", "diabetes", "cholesterol"],
    "edges": ["cardiovascular_disease-hypertension", "cardiovascular_disease-diabetes"],
    "scores": {
      "cardiovascular_disease": 0.95,
      "hypertension": 0.88,
      "diabetes": 0.82
    }
  },
  "contextUsed": [
    "Hypertension is a major risk factor...",
    "Diabetes increases cardiovascular risk..."
  ],
  "executionTime": 2.34,
  "mode": "hybrid",
  "timestamp": "2025-10-22T10:30:45.123Z"
}
```

**Response Fields:**
- `answer`: Generated answer text
- `queryPath`: Information about the retrieval path
  - `nodes`: List of entity IDs accessed during retrieval
  - `edges`: List of edge IDs accessed during retrieval
  - `scores`: Relevance scores for each node/edge
- `contextUsed`: List of context snippets used for generation
- `executionTime`: Query execution time in seconds
- `mode`: Query mode used
- `timestamp`: Query execution timestamp

**Error Responses:**
- `422 Unprocessable Entity`: Invalid request parameters
- `503 Service Unavailable`: Query service not initialized
- `500 Internal Server Error`: Query execution failed

---

### Get Query History

#### `GET /api/query/history`

Retrieve recent query history.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of history items (1-100, default: 10)

**Example Request:**
```bash
curl "http://localhost:3401/api/query/history?limit=5"
```

**Example Response:**
```json
{
  "queries": [
    {
      "query": "What are the risk factors for cardiovascular disease?",
      "mode": "hybrid",
      "timestamp": "2025-10-22T10:30:45.123Z",
      "executionTime": 2.34
    },
    {
      "query": "How is diabetes treated?",
      "mode": "local",
      "timestamp": "2025-10-22T10:25:12.456Z",
      "executionTime": 1.87
    }
  ],
  "total": 2
}
```

---

### Clear Query History

#### `DELETE /api/query/history`

Clear all query history.

**Example Request:**
```bash
curl -X DELETE "http://localhost:3401/api/query/history"
```

**Example Response:**
```json
{
  "message": "Query history cleared",
  "status": "success"
}
```

---

## Data Models

### Node

Represents an entity in the hypergraph.

```typescript
{
  id: string;              // Unique identifier
  label: string;           // Display name
  type: string;            // Entity type (e.g., "DISEASE", "PERSON")
  description: string;     // Entity description
  weight: number;          // Importance weight (0.0-1.0)
  relevanceScore?: number; // Relevance score (for search results)
}
```

### Edge

Represents a connection between entities (including hyperedges).

```typescript
{
  id: string;              // Unique identifier
  source: string;          // Source node ID
  target: string;          // Target node ID
  relation: string;        // Relationship type
  description: string;     // Relationship description
  weight: number;          // Edge weight (0.0-1.0)
  entities: string[];      // All connected entity IDs
  isHyperedge: boolean;    // True if connects 3+ entities
}
```

### GraphData

Complete graph structure.

```typescript
{
  nodes: Node[];           // List of nodes
  edges: Edge[];           // List of edges
}
```

### GraphStats

Graph statistics.

```typescript
{
  numNodes: number;        // Total number of nodes
  numEdges: number;        // Total number of edges
  numHyperedges: number;   // Number of hyperedges (3+ entities)
  avgDegree: number;       // Average node degree
  density: number;         // Graph density (0.0-1.0)
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Invalid request parameters
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service not initialized

### Common Error Scenarios

**Node Not Found:**
```json
{
  "detail": "Node hypertension not found"
}
```

**Invalid Parameters:**
```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 10000",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Service Unavailable:**
```json
{
  "detail": "Query service not available"
}
```

---

## Rate Limiting

Currently, there is no rate limiting. This may be added in future versions for production deployments.

---

## CORS Configuration

The API allows cross-origin requests from:
- `http://localhost:3400` (React dev server)
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:3400`
- `http://127.0.0.1:5173`

For production deployments, update the CORS configuration in `api/main.py`.

---

## Performance Considerations

### Pagination

Always use pagination for large datasets:
- Default `limit` is 100
- Maximum `limit` is 10,000
- Use `offset` for pagination

### Caching

Consider implementing caching for frequently accessed data:
- Graph statistics (changes infrequently)
- Popular search queries
- Subgraph results

### Timeouts

- Default request timeout: 30 seconds
- Long-running queries may timeout
- Consider implementing async query execution for complex queries

---

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_api_integration.py

# Run with coverage
pytest --cov=api tests/
```

### Adding New Endpoints

1. Define data models in `api/models/`
2. Implement business logic in `api/services/`
3. Create route handlers in `api/routes/`
4. Register routes in `api/main.py`
5. Add tests in `tests/`

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Support

For issues, questions, or contributions:
- GitHub Issues: [Project Repository]
- Documentation: `/docs`
- API Docs: http://localhost:3401/docs

---

## Changelog

### Version 1.0.0 (2025-10-22)
- Initial release
- Graph data endpoints
- Query execution endpoints
- Query history management
- OpenAPI documentation
