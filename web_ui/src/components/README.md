# HyperGraphRAG Web UI Components

## Query Components (Task 12)

### QueryInterface.tsx
Query input component with the following features:
- **Query Input**: Multi-line textarea with Ctrl+Enter shortcut
- **Mode Selection**: Dropdown for local/global/hybrid/naive query modes
- **Advanced Parameters**: Collapsible section for:
  - Top K (number of results)
  - Max tokens for text unit, local context, and global context
- **Submit Button**: With loading state and disabled state handling
- **Keyboard Shortcuts**: Ctrl+Enter (Cmd+Enter on Mac) to submit

### QueryResult.tsx
Query result display component with:
- **Answer Display**: Markdown-rendered answer with custom styling
- **Execution Time**: Badge showing query execution time
- **Context Used**: Expandable list of text chunks used in the query
- **Query Path Info**: Statistics about nodes and edges visited
- **Top Scored Nodes**: List of most relevant nodes with scores
- **Close Button**: Option to dismiss the result

### QueryPanel.tsx
Integrated query panel with tabbed interface:
- **Three Tabs**:
  1. Query: Input and configuration
  2. Result: Display query results
  3. History: View and re-execute past queries
- **Query History Management**:
  - View all past queries with timestamps
  - Re-execute any historical query
  - Delete individual queries
  - Clear all history
- **Error Handling**: Display error messages prominently
- **Auto-switch**: Automatically switches to result tab after query execution

### Integration with GraphCanvas
The query functionality is integrated with the graph visualization:
- **Query Path Highlighting**: Nodes and edges in the query path are highlighted
  - High-score nodes (>0.7): Orange with thick border
  - Regular path nodes: Yellow with medium border
  - Path edges: Yellow with increased width
- **Auto-focus**: Graph automatically fits to show all query path elements
- **View Toggle**: Switch between Graph View and Query View
- **Seamless Flow**: Execute query → auto-switch to graph → see highlighted path

## UI Components

### textarea.tsx
Custom textarea component following shadcn/ui patterns:
- Consistent styling with other form elements
- Focus states and accessibility
- Responsive sizing

## State Management

### queryStore.ts (Zustand)
Manages query-related state:
- Current query and mode
- Query configuration parameters
- Query history (persisted to localStorage)
- Loading and error states
- Helper methods for query execution

### queryService.ts
API service for query operations:
- Execute queries with full configuration
- Manage query history (local and server-side)
- Re-execute historical queries
- Export/import history
- Query statistics

## Usage Example

```tsx
import QueryPanel from '@/components/QueryPanel';

function App() {
  const handleQueryExecuted = (response: QueryResponse) => {
    // Handle query response
    // Update graph visualization with query path
  };

  return (
    <QueryPanel onQueryExecuted={handleQueryExecuted} />
  );
}
```

## Features Implemented

✅ Task 12.1: Query input component with mode selection and advanced parameters
✅ Task 12.2: Query result display with markdown rendering and context
✅ Task 12.3: Integration with graph visualization and query path highlighting

## Next Steps (Future Tasks)

- Task 13: Query path animation (step-by-step visualization)
- Task 14: Data export functionality
- Task 15: Configuration management
- Task 16: Responsive design improvements
