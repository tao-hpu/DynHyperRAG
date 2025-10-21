# GraphCanvas Component

## Overview

`GraphCanvas` is a React component that provides interactive hypergraph visualization using Cytoscape.js. It renders nodes (entities) and edges (relationships/hyperedges) with support for various interactions.

## Features

### ✅ Implemented (Task 9)

#### 9.1 Cytoscape.js Integration
- ✅ Installed Cytoscape.js and type definitions
- ✅ Created `GraphCanvas.tsx` component
- ✅ Initialized Cytoscape instance with proper configuration
- ✅ Configured base styles for nodes and edges

#### 9.2 Node and Edge Rendering
- ✅ Convert API data to Cytoscape format
- ✅ Render entity nodes (circles with labels)
- ✅ Render regular edges (straight lines with arrows)
- ✅ Render hyperedges (dashed lines, special styling for 3+ entities)
- ✅ Color-coded nodes by entity type:
  - **Person**: Green (#10b981)
  - **Organization**: Orange (#f59e0b)
  - **Location**: Purple (#8b5cf6)
  - **Event**: Pink (#ec4899)
  - **Concept**: Cyan (#06b6d4)
  - **Default**: Blue (#3b82f6)

#### 9.3 Force-Directed Layout
- ✅ Configured Cytoscape COSE (force-directed) layout algorithm
- ✅ Adjusted layout parameters (repulsion: 8000, edge length: 100)
- ✅ Implemented layout animation (1000ms with ease-out)
- ✅ Optimized for large-scale graphs with performance settings

#### 9.4 Basic Interactions
- ✅ Mouse wheel zoom (0.1x - 10x range)
- ✅ Canvas drag to pan
- ✅ Node dragging
- ✅ Zoom/pan animations
- ✅ Click events for nodes and edges
- ✅ Double-click event for node expansion

## Usage

```tsx
import GraphCanvas from '@/components/GraphCanvas';
import type { GraphData, Node, Edge } from '@/types/graph';

function MyComponent() {
  const data: GraphData = {
    nodes: [
      { id: '1', label: 'Node 1', type: 'person', description: '...', weight: 1.0 },
      // ... more nodes
    ],
    edges: [
      { 
        id: 'e1', 
        source: '1', 
        target: '2', 
        relation: 'knows',
        description: '...',
        weight: 1.0,
        entities: ['1', '2'],
        isHyperedge: false
      },
      // ... more edges
    ]
  };

  const handleNodeClick = (node: Node) => {
    console.log('Node clicked:', node);
  };

  const handleEdgeClick = (edge: Edge) => {
    console.log('Edge clicked:', edge);
  };

  const handleNodeDoubleClick = (nodeId: string) => {
    console.log('Expand node:', nodeId);
    // Fetch and add neighbors
  };

  return (
    <GraphCanvas
      data={data}
      onNodeClick={handleNodeClick}
      onEdgeClick={handleEdgeClick}
      onNodeDoubleClick={handleNodeDoubleClick}
    />
  );
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `data` | `GraphData` | Yes | Graph data containing nodes and edges |
| `onNodeClick` | `(node: Node) => void` | No | Callback when a node is clicked |
| `onEdgeClick` | `(edge: Edge) => void` | No | Callback when an edge is clicked |
| `onNodeDoubleClick` | `(nodeId: string) => void` | No | Callback when a node is double-clicked |

## Styling

The component uses Cytoscape.js stylesheets for graph elements. Key style features:

- **Node size**: Based on weight (20-60px range)
- **Edge width**: 2px for regular edges, 3px for hyperedges
- **Hyperedges**: Dashed orange lines
- **Selection**: Red border highlight
- **Hover**: Blue/orange overlay effect

## Performance Optimizations

- `hideEdgesOnViewport`: Hide edges when zooming/panning for better performance
- `textureOnViewport`: Use texture rendering during viewport changes
- `motionBlur`: Enable motion blur for smoother animations
- `pixelRatio: 'auto'`: Automatic pixel ratio detection

## Interactive Controls

- **Zoom**: Mouse wheel (0.1x - 10x)
- **Pan**: Click and drag on canvas background
- **Select**: Click on node or edge
- **Move Node**: Drag a node
- **Expand**: Double-click a node (triggers `onNodeDoubleClick`)

## Development

To test the component:

```bash
cd web_ui
pnpm install
pnpm run dev
```

Visit http://localhost:3000 to see the demo with sample data.

## Next Steps

The following features are planned for future tasks:

- **Task 10**: Node and edge hover tooltips, detailed interactions
- **Task 11**: Search and filter functionality
- **Task 12-13**: Query visualization and path highlighting
- **Task 14-15**: Export and configuration features
- **Task 16**: Responsive design for mobile devices
- **Task 17**: Performance optimizations (viewport culling, lazy loading)

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **Requirement 1.1**: ✅ Render all entity nodes with labels
- **Requirement 1.2**: ✅ Render hyperedges with visual distinction
- **Requirement 1.3**: ✅ Force-directed layout algorithm
- **Requirement 2.1**: ✅ Mouse wheel zoom (0.1x - 10x)
- **Requirement 2.2**: ✅ Canvas drag to pan
- **Requirement 7.1**: ✅ Performance optimizations for large graphs
