# Test Suite Documentation

## Overview

This directory contains comprehensive tests for the HyperGraphRAG Visualization API.

## Test Files

### 1. `test_models.py` - Unit Tests for Data Models
Tests Pydantic data models for validation and constraints.

**Coverage:**
- Node, Edge, GraphData, GraphStats models
- QueryRequest, QueryResponse, QueryPath models
- Pagination and Filter parameter models
- Field validation and constraints

**Status:** ✅ All 24 tests passing

### 2. `test_api_integration.py` - API Integration Tests
Tests complete API flow with all endpoints using FastAPI TestClient.

**Coverage:**
- Health and root endpoints
- Graph API endpoints (nodes, edges, stats, subgraph, search)
- Query API endpoints (execute, history, clear)
- Error handling (404, 422, 500)
- Pagination and filtering
- Parameter validation

**Test Classes:**
- `TestHealthEndpoints` - Health check and root endpoint tests
- `TestGraphAPI` - Graph data retrieval tests
- `TestQueryAPI` - Query execution and history tests
- `TestErrorHandling` - Error response tests

**Status:** ✅ Implemented (22 tests)

### 3. `test_performance.py` - Performance Tests
Tests response times and throughput for API endpoints.

**Coverage:**
- Graph API performance (stats, nodes, edges, search, subgraph)
- Query API performance (all modes: hybrid, local, global, naive)
- Pagination performance
- Concurrent request handling

**Test Classes:**
- `TestGraphAPIPerformance` - Graph endpoint performance
- `TestQueryAPIPerformance` - Query endpoint performance
- `TestConcurrency` - Concurrent request handling

**Status:** ✅ Implemented (13 tests)

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure `.env` file is configured with API keys:
```bash
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=your_base_url_here
```

3. Ensure example data exists in `expr/example/`:
- `graph_chunk_entity_relation.graphml`
- `vdb_entities.json`
- `vdb_hyperedges.json`
- `kv_store_text_chunks.json`

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

### Run Specific Test Files

```bash
# Model tests only (fast, no API initialization)
pytest tests/test_models.py -v

# Integration tests (requires data and API initialization)
pytest tests/test_api_integration.py -v

# Performance tests (slower, includes timing assertions)
pytest tests/test_performance.py -v -s
```

### Run Specific Test Classes

```bash
# Test only Graph API
pytest tests/test_api_integration.py::TestGraphAPI -v

# Test only Query API
pytest tests/test_api_integration.py::TestQueryAPI -v

# Test performance
pytest tests/test_performance.py::TestGraphAPIPerformance -v
```

### Run Specific Tests

```bash
# Test a single endpoint
pytest tests/test_api_integration.py::TestGraphAPI::test_get_nodes_default -v

# Test query execution
pytest tests/test_api_integration.py::TestQueryAPI::test_execute_query_hybrid -v
```

## Test Requirements Coverage

### Requirement 6.5 - Error Handling
✅ Covered by:
- `test_api_integration.py::TestErrorHandling`
- `test_api_integration.py::TestGraphAPI::test_validation_errors`
- `test_api_integration.py::TestQueryAPI::test_query_validation_errors`

### Requirement 7.1 - Performance
✅ Covered by:
- `test_performance.py::TestGraphAPIPerformance`
- `test_performance.py::TestQueryAPIPerformance`
- All performance tests verify response times

### Requirement 7.2 - Concurrent Handling
✅ Covered by:
- `test_performance.py::TestConcurrency`
- Tests concurrent stats and node requests

### Requirement 6.7 - Response Time (< 30s)
✅ Covered by:
- `test_performance.py::TestQueryAPIPerformance::test_query_hybrid_performance`
- Asserts execution_time < 30.0 seconds

## Test Data

Tests use the example data in `expr/example/`:
- **Nodes:** ~100+ entities
- **Edges:** ~200+ relationships
- **Hyperedges:** Edges connecting 3+ entities

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Fast tests only (models)
pytest tests/test_models.py -v --tb=short

# Full test suite with timeout
pytest tests/ -v --tb=short --timeout=300

# With coverage report
pytest tests/ --cov=api --cov-report=xml --cov-report=term
```

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Service Initialization Errors
If tests fail during setup, check:
1. `.env` file exists and has valid API keys
2. Example data exists in `expr/example/`
3. All required Python packages are installed

### Performance Test Failures
Performance tests have timing assertions. If they fail:
1. Check system load (tests may be slower on busy systems)
2. Check network latency (LLM API calls affect query performance)
3. Adjust timeout values if needed for your environment

## Future Enhancements

Potential additions:
- Load testing with locust or k6
- End-to-end tests with Playwright
- API contract testing with Pact
- Mutation testing with mutmut
- Security testing with bandit
