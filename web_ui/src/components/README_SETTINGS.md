# Settings Panel - Configuration Management

## Overview

The Settings Panel provides a comprehensive interface for customizing the visualization appearance and behavior. All settings are automatically persisted to localStorage and restored on application startup.

## Features

### 1. Color Schemes

Choose from predefined color schemes or customize individual colors:

- **Default**: Standard blue-based color palette
- **Vibrant**: High-contrast, saturated colors
- **Pastel**: Soft, muted colors
- **Monochrome**: Grayscale palette

Each scheme includes colors for:
- Entity types (person, organization, location, event, concept)
- Edges and hyperedges
- Query path highlights

### 2. Node Appearance

Customize node visual properties:

- **Font Size** (8-20px): Label text size
- **Font Weight** (300-700): Label text boldness
- **Min Node Size** (10-40px): Minimum node diameter
- **Max Node Size** (40-100px): Maximum node diameter

Node sizes are dynamically calculated based on weight, scaled between min and max values.

### 3. Layout Parameters

Fine-tune the force-directed layout algorithm:

- **Edge Length** (50-300): Ideal distance between connected nodes
- **Node Repulsion** (1000-15000): Force pushing nodes apart
- **Gravity** (0-1): Force pulling nodes toward center
- **Iterations** (500-5000): Number of layout calculation steps

**Note**: Changing layout parameters triggers a full layout recalculation, which may take a few seconds for large graphs.

## Implementation Details

### Architecture

```
SettingsPanel (UI Component)
    ↓
settingsStore (Zustand Store with Persistence)
    ↓
GraphCanvas (Applies settings to Cytoscape)
```

### Files

- `types/settings.ts` - Type definitions and default values
- `stores/settingsStore.ts` - State management with localStorage persistence
- `components/SettingsPanel.tsx` - UI component
- `components/GraphCanvas.tsx` - Applies settings to visualization

### Real-time Updates

Settings are applied in real-time:

1. **Color & Style Changes**: Applied immediately via Cytoscape style updates
2. **Node Size Changes**: Recalculated and applied to all nodes
3. **Layout Changes**: Triggers full layout recalculation (graph is re-rendered)

### Persistence

Settings are automatically saved to localStorage under the key `visualization-settings`. They are restored when the application loads.

## Usage

### In the UI

1. Click the Settings panel in the sidebar (collapsed by default)
2. Adjust any parameter using sliders or dropdowns
3. Changes apply immediately
4. Click "Reset to Defaults" to restore original settings

### Programmatically

```typescript
import { useSettingsStore } from '@/stores/settingsStore';

function MyComponent() {
  const { settings, updateLayoutSettings, resetSettings } = useSettingsStore();
  
  // Update a setting
  updateLayoutSettings({ idealEdgeLength: 150 });
  
  // Reset all settings
  resetSettings();
  
  // Access current settings
  console.log(settings.colorScheme.person);
}
```

## Performance Considerations

- **Color/Style Changes**: Very fast, no layout recalculation
- **Node Size Changes**: Fast, updates existing nodes
- **Layout Changes**: Slow for large graphs (>1000 nodes), triggers full recalculation

For large graphs, consider:
- Adjusting layout parameters before loading data
- Using imported layouts (which skip layout calculation)
- Reducing the number of iterations for faster (but less optimal) layouts

## Future Enhancements

Potential improvements:

1. Custom color pickers for individual entity types
2. Export/import settings as JSON
3. Multiple saved presets
4. Animation speed controls
5. Edge styling options (thickness, opacity)
6. Advanced layout algorithms (hierarchical, circular, etc.)
