# Export Functionality Implementation

## Overview

This document describes the export functionality implemented for the HyperGraphRAG visualization system.

## Components

### 1. ExportPanel Component (`ExportPanel.tsx`)

A UI panel that provides export controls with the following features:

- **Format Selection**: Choose between PNG, SVG, or JSON export formats
- **Image Export Options**:
  - Scale/Resolution: 1x to 4x (Standard, High, Ultra High)
  - Quality: 50% to 100% (PNG only)
  - Background Color: Customizable hex color picker
- **JSON Export Options**:
  - Include layout positions (node coordinates)
  - Include node styles (colors, sizes, etc.)
- **Import Functionality**: Import previously exported JSON files to restore graph state

### 2. Export Utilities (`utils/exportUtils.ts`)

Core export functions that handle the actual data conversion:

#### `exportToPNG(cy, options)`
- Exports the graph as a PNG image
- Uses Cytoscape's `png()` method with base64uri output
- Converts base64 to Blob for download
- Supports custom scale and background color

#### `exportToSVG(cy, options)`
- Exports the graph as an SVG image
- Creates an SVG wrapper with embedded PNG image
- Note: True vector SVG export would require the cytoscape-svg plugin
- Current implementation provides a scalable image format

#### `exportToJSON(cy, graphData, options)`
- Exports complete graph data as JSON
- Includes:
  - Node and edge data
  - Optional: Layout positions (x, y coordinates)
  - Optional: Node styles (colors, sizes, borders)
  - Timestamp and version information

#### `importFromJSON(jsonString)`
- Parses and validates imported JSON data
- Returns graph data, layout, and styles
- Handles errors gracefully

#### `downloadFile(blob, filename)`
- Utility function to trigger browser download
- Creates temporary URL and link element
- Cleans up after download

### 3. GraphCanvas Updates

The `GraphCanvas` component was updated to:

- Use `forwardRef` to expose methods to parent components
- Implement `useImperativeHandle` to provide export methods
- Support imported layout positions
- Export interface: `GraphCanvasRef` with methods:
  - `exportPNG(options)`
  - `exportSVG(options)`
  - `exportJSON(options)`
  - `getCytoscapeInstance()`

### 4. App Integration

The main `App.tsx` was updated to:

- Add `ExportPanel` to the sidebar (visible in graph view)
- Create ref to `GraphCanvas` for accessing export methods
- Handle export requests by calling appropriate methods
- Handle import by parsing JSON and updating graph data
- Support imported layout restoration

## Usage

### Exporting

1. Navigate to the graph view
2. In the sidebar, find the "Export Graph" panel
3. Select desired format (PNG, SVG, or JSON)
4. Adjust options as needed:
   - For images: Set scale, quality, and background color
   - For JSON: Choose whether to include layout and styles
5. Click "Export as [FORMAT]" button
6. File will be downloaded automatically

### Importing

1. In the "Export Graph" panel, scroll to "Import Graph" section
2. Click "Import JSON" button
3. Select a previously exported JSON file
4. Graph will be restored with original data and layout (if included)

## File Naming

Exported files are automatically named with timestamps:
- Format: `hypergraph-YYYY-MM-DDTHH-MM-SS.[ext]`
- Example: `hypergraph-2024-10-22T14-30-45.png`

## Technical Details

### Export Options Interface

```typescript
interface ExportOptions {
  // Image export options
  scale?: number;           // 1-4, default: 2
  quality?: number;         // 0.5-1.0, default: 0.95
  backgroundColor?: string; // Hex color, default: '#ffffff'
  
  // JSON export options
  includeLayout?: boolean;  // Default: true
  includeStyles?: boolean;  // Default: false
}
```

### JSON Export Format

```json
{
  "version": "1.0",
  "timestamp": "2024-10-22T14:30:45.123Z",
  "nodes": [...],
  "edges": [...],
  "layout": {
    "node_id": { "x": 100, "y": 200 },
    ...
  },
  "styles": {
    "node_id": {
      "backgroundColor": "#3b82f6",
      "borderColor": "#1e40af",
      ...
    },
    ...
  }
}
```

## Future Enhancements

1. **True SVG Export**: Integrate cytoscape-svg plugin for vector export
2. **PDF Export**: Add PDF generation capability
3. **Batch Export**: Export multiple views or filtered graphs
4. **Custom Templates**: Save and load export presets
5. **Cloud Storage**: Direct upload to cloud services
6. **Clipboard Copy**: Copy image to clipboard
7. **Print Support**: Optimize for printing

## Requirements Satisfied

- ✅ 5.1: Export format selection (PNG, SVG, JSON)
- ✅ 5.2: Image export with resolution and quality settings
- ✅ 5.2: Data export with layout positions
- ✅ 5.2: Import JSON to restore graph state
