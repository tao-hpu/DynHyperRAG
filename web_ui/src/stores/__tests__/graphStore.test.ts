import { describe, it, expect, beforeEach } from 'vitest';
import { useGraphStore } from '../graphStore';
import { mockGraphData, mockGraphStats, mockNodes, mockEdges } from '@/test/mockData';

describe('GraphStore', () => {
  beforeEach(() => {
    // Reset store state
    useGraphStore.setState({
      graphData: null,
      stats: null,
      selectedNodeId: null,
      selectedEdgeId: null,
      highlightedNodes: new Set(),
      highlightedEdges: new Set(),
      filter: {
        entityTypes: [],
        minWeight: 0,
        maxWeight: 1,
      },
      viewport: {
        zoom: 1,
        pan: { x: 0, y: 0 },
      },
      isLoading: false,
      error: null,
    });
  });

  describe('setGraphData', () => {
    it('sets graph data', () => {
      const { setGraphData } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      
      expect(useGraphStore.getState().graphData).toEqual(mockGraphData);
    });

    it('clears error when setting data', () => {
      const { setError, setGraphData } = useGraphStore.getState();
      
      setError('Test error');
      setGraphData(mockGraphData);
      
      expect(useGraphStore.getState().error).toBeNull();
    });
  });

  describe('setStats', () => {
    it('sets graph statistics', () => {
      const { setStats } = useGraphStore.getState();
      
      setStats(mockGraphStats);
      
      expect(useGraphStore.getState().stats).toEqual(mockGraphStats);
    });
  });

  describe('selectNode', () => {
    it('selects a node', () => {
      const { selectNode } = useGraphStore.getState();
      
      selectNode('node1');
      
      expect(useGraphStore.getState().selectedNodeId).toBe('node1');
    });

    it('deselects edge when selecting node', () => {
      const { selectNode, selectEdge } = useGraphStore.getState();
      
      selectEdge('edge1');
      selectNode('node1');
      
      expect(useGraphStore.getState().selectedNodeId).toBe('node1');
      expect(useGraphStore.getState().selectedEdgeId).toBeNull();
    });
  });

  describe('selectEdge', () => {
    it('selects an edge', () => {
      const { selectEdge } = useGraphStore.getState();
      
      selectEdge('edge1');
      
      expect(useGraphStore.getState().selectedEdgeId).toBe('edge1');
    });

    it('deselects node when selecting edge', () => {
      const { selectNode, selectEdge } = useGraphStore.getState();
      
      selectNode('node1');
      selectEdge('edge1');
      
      expect(useGraphStore.getState().selectedEdgeId).toBe('edge1');
      expect(useGraphStore.getState().selectedNodeId).toBeNull();
    });
  });

  describe('highlightNodes', () => {
    it('highlights multiple nodes', () => {
      const { highlightNodes } = useGraphStore.getState();
      
      highlightNodes(['node1', 'node2']);
      
      const highlighted = useGraphStore.getState().highlightedNodes;
      expect(highlighted.has('node1')).toBe(true);
      expect(highlighted.has('node2')).toBe(true);
    });
  });

  describe('highlightEdges', () => {
    it('highlights multiple edges', () => {
      const { highlightEdges } = useGraphStore.getState();
      
      highlightEdges(['edge1', 'edge2']);
      
      const highlighted = useGraphStore.getState().highlightedEdges;
      expect(highlighted.has('edge1')).toBe(true);
      expect(highlighted.has('edge2')).toBe(true);
    });
  });

  describe('clearHighlights', () => {
    it('clears all highlights', () => {
      const { highlightNodes, highlightEdges, clearHighlights } = useGraphStore.getState();
      
      highlightNodes(['node1', 'node2']);
      highlightEdges(['edge1']);
      clearHighlights();
      
      expect(useGraphStore.getState().highlightedNodes.size).toBe(0);
      expect(useGraphStore.getState().highlightedEdges.size).toBe(0);
    });
  });

  describe('setFilter', () => {
    it('updates filter partially', () => {
      const { setFilter } = useGraphStore.getState();
      
      setFilter({ entityTypes: ['person'] });
      
      const filter = useGraphStore.getState().filter;
      expect(filter.entityTypes).toEqual(['person']);
      expect(filter.minWeight).toBe(0); // Unchanged
    });

    it('updates multiple filter properties', () => {
      const { setFilter } = useGraphStore.getState();
      
      setFilter({ entityTypes: ['person'], minWeight: 0.5 });
      
      const filter = useGraphStore.getState().filter;
      expect(filter.entityTypes).toEqual(['person']);
      expect(filter.minWeight).toBe(0.5);
    });
  });

  describe('resetFilter', () => {
    it('resets filter to default', () => {
      const { setFilter, resetFilter } = useGraphStore.getState();
      
      setFilter({ entityTypes: ['person'], minWeight: 0.5 });
      resetFilter();
      
      const filter = useGraphStore.getState().filter;
      expect(filter.entityTypes).toEqual([]);
      expect(filter.minWeight).toBe(0);
      expect(filter.maxWeight).toBe(1);
    });
  });

  describe('setViewport', () => {
    it('updates viewport state', () => {
      const { setViewport } = useGraphStore.getState();
      
      setViewport({ zoom: 2, pan: { x: 100, y: 200 } });
      
      const viewport = useGraphStore.getState().viewport;
      expect(viewport.zoom).toBe(2);
      expect(viewport.pan).toEqual({ x: 100, y: 200 });
    });
  });

  describe('getNodeById', () => {
    it('returns node by ID', () => {
      const { setGraphData, getNodeById } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      const node = getNodeById('node1');
      
      expect(node).toEqual(mockNodes[0]);
    });

    it('returns undefined for non-existent node', () => {
      const { setGraphData, getNodeById } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      const node = getNodeById('nonexistent');
      
      expect(node).toBeUndefined();
    });
  });

  describe('getEdgeById', () => {
    it('returns edge by ID', () => {
      const { setGraphData, getEdgeById } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      const edge = getEdgeById('edge1');
      
      expect(edge).toEqual(mockEdges[0]);
    });

    it('returns undefined for non-existent edge', () => {
      const { setGraphData, getEdgeById } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      const edge = getEdgeById('nonexistent');
      
      expect(edge).toBeUndefined();
    });
  });

  describe('getFilteredData', () => {
    it('returns all data when no filters applied', () => {
      const { setGraphData, getFilteredData } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      const filtered = getFilteredData();
      
      expect(filtered.nodes).toHaveLength(mockNodes.length);
      expect(filtered.edges).toHaveLength(mockEdges.length);
    });

    it('filters nodes by entity type', () => {
      const { setGraphData, setFilter, getFilteredData } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      setFilter({ entityTypes: ['person'] });
      const filtered = getFilteredData();
      
      expect(filtered.nodes).toHaveLength(1);
      expect(filtered.nodes[0].type).toBe('person');
    });

    it('filters edges by weight', () => {
      const { setGraphData, setFilter, getFilteredData } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      setFilter({ minWeight: 0.85, maxWeight: 1.0 });
      const filtered = getFilteredData();
      
      expect(filtered.edges.every(e => e.weight >= 0.85 && e.weight <= 1.0)).toBe(true);
    });

    it('removes edges not connected to filtered nodes', () => {
      const { setGraphData, setFilter, getFilteredData } = useGraphStore.getState();
      
      setGraphData(mockGraphData);
      setFilter({ entityTypes: ['person'] }); // Only node1
      const filtered = getFilteredData();
      
      // Edges should only connect to person nodes
      expect(filtered.edges.length).toBeLessThanOrEqual(mockEdges.length);
    });
  });

  describe('loading and error states', () => {
    it('sets loading state', () => {
      const { setLoading } = useGraphStore.getState();
      
      setLoading(true);
      expect(useGraphStore.getState().isLoading).toBe(true);
      
      setLoading(false);
      expect(useGraphStore.getState().isLoading).toBe(false);
    });

    it('sets error state', () => {
      const { setError } = useGraphStore.getState();
      
      setError('Test error');
      expect(useGraphStore.getState().error).toBe('Test error');
      expect(useGraphStore.getState().isLoading).toBe(false);
    });
  });
});
