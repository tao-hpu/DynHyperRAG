# API Services

This directory contains the API service layer for the HyperGraphRAG visualization frontend.

## Services

### GraphService (`graphService.ts`)

Provides methods to interact with the graph data API.

**Methods:**
- `getNodes(params?)` - Get list of nodes with pagination and filtering
- `getNodeById(nodeId)` - Get single node details
- `getEdges(params?)` - Get list of edges with pagination and weight filtering
- `getEdgeById(edgeId)` - Get single edge details
- `getStats()` - Get graph statistics (node count, edge count, etc.)
- `getSubgraph(params)` - Get subgraph centered on a specific node
- `searchNodes(params)` - Search nodes using semantic search
- `getNodesByIds(nodeIds)` - Batch get nodes by ID list
- `getEdgesByIds(edgeIds)` - Batch get edges by ID list
- `getGraphData(params?)` - Get complete graph data (nodes + edges)

**Usage Example:**
```typescript
import { graphService } from '@/services';

// Get first 100 nodes
const nodes = await graphService.getNodes({ limit: 100, offset: 0 });

// Search for nodes
const results = await graphService.searchNodes({ 
  keyword: 'hypertension', 
  limit: 20 
});

// Get subgraph
const subgraph = await graphService.getSubgraph({
  centerNodeId: 'node-123',
  depth: 2
});

// Get statistics
const stats = await graphService.getStats();
```

### QueryService (`queryService.ts`)

Provides methods to execute RAG queries and manage query history.

**Methods:**
- `executeQuery(request)` - Execute a RAG query
- `getQueryHistory(limit?)` - Get query history from server or local cache
- `getLocalHistory(limit?)` - Get local query history
- `clearHistory()` - Clear all history
- `deleteHistoryItem(id)` - Delete a single history item
- `reExecuteQuery(historyItem)` - Re-execute a historical query
- `executeBatchQueries(queries)` - Execute multiple queries in parallel
- `exportHistory()` - Export history as JSON string
- `importHistory(jsonString)` - Import history from JSON
- `getHistoryStats()` - Get statistics about query history

**Usage Example:**
```typescript
import { queryService } from '@/services';

// Execute a query
const response = await queryService.executeQuery({
  query: 'What is hypertension?',
  mode: 'hybrid',
  topK: 60
});

console.log(response.answer);
console.log(response.queryPath);

// Get query history
const history = await queryService.getQueryHistory(10);

// Get history statistics
const stats = queryService.getHistoryStats();
console.log(`Total queries: ${stats.totalQueries}`);
console.log(`Average execution time: ${stats.averageExecutionTime}s`);
```

## Integration with Zustand Stores

The services are designed to work seamlessly with the Zustand stores:

```typescript
import { graphService, queryService } from '@/services';
import { useGraphStore } from '@/stores/graphStore';
import { useQueryStore } from '@/stores/queryStore';

// In a React component
function MyComponent() {
  const { setGraphData, setLoading } = useGraphStore();
  const { setCurrentResponse, setQuerying } = useQueryStore();

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await graphService.getGraphData({ nodeLimit: 1000 });
      setGraphData(data);
    } catch (error) {
      console.error('Failed to load graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeQuery = async (query: string) => {
    setQuerying(true);
    try {
      const response = await queryService.executeQuery({
        query,
        mode: 'hybrid'
      });
      setCurrentResponse(response);
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setQuerying(false);
    }
  };

  // ...
}
```

## Error Handling

All services use the centralized API client (`@/utils/api.ts`) which provides:
- Automatic error logging
- Standardized error format
- Request/response interceptors
- Timeout handling (30s default)

Errors are returned in the format:
```typescript
{
  status: number;
  message: string;
  details?: any;
}
```

## Type Safety

All services are fully typed using TypeScript generics and interfaces from `@/types/graph.ts` and `@/types/query.ts`. This ensures type safety throughout the application.

## Singleton Pattern

Both services export singleton instances for convenience:
```typescript
import { graphService, queryService } from '@/services';
```

But also export the classes if you need to create custom instances:
```typescript
import GraphService from '@/services/graphService';
const customGraphService = new GraphService();
```
