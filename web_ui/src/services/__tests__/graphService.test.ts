import { describe, it, expect, vi, beforeEach } from 'vitest';
import { graphService } from '../graphService';
import api from '@/utils/api';
import { mockNodes, mockEdges, mockGraphData, mockGraphStats } from '@/test/mockData';

// Mock the API
vi.mock('@/utils/api');

describe('GraphService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getNodes', () => {
    it('fetches nodes successfully', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes });

      const result = await graphService.getNodes();

      expect(api.get).toHaveBeenCalledWith('/graph/nodes', { params: undefined });
      expect(result).toEqual(mockNodes);
    });

    it('fetches nodes with pagination', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes });

      await graphService.getNodes({ limit: 10, offset: 20 });

      expect(api.get).toHaveBeenCalledWith('/graph/nodes', {
        params: { limit: 10, offset: 20 },
      });
    });

    it('fetches nodes with entity type filter', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes });

      await graphService.getNodes({ entityType: 'person' });

      expect(api.get).toHaveBeenCalledWith('/graph/nodes', {
        params: { entityType: 'person' },
      });
    });
  });

  describe('getNodeById', () => {
    it('fetches single node by ID', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes[0] });

      const result = await graphService.getNodeById('node1');

      expect(api.get).toHaveBeenCalledWith('/graph/nodes/node1');
      expect(result).toEqual(mockNodes[0]);
    });
  });

  describe('getEdges', () => {
    it('fetches edges successfully', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockEdges });

      const result = await graphService.getEdges();

      expect(api.get).toHaveBeenCalledWith('/graph/edges', { params: undefined });
      expect(result).toEqual(mockEdges);
    });

    it('fetches edges with weight filter', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockEdges });

      await graphService.getEdges({ minWeight: 0.5 });

      expect(api.get).toHaveBeenCalledWith('/graph/edges', {
        params: { minWeight: 0.5 },
      });
    });
  });

  describe('getEdgeById', () => {
    it('fetches single edge by ID', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockEdges[0] });

      const result = await graphService.getEdgeById('edge1');

      expect(api.get).toHaveBeenCalledWith('/graph/edges/edge1');
      expect(result).toEqual(mockEdges[0]);
    });
  });

  describe('getStats', () => {
    it('fetches graph statistics', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockGraphStats });

      const result = await graphService.getStats();

      expect(api.get).toHaveBeenCalledWith('/graph/stats');
      expect(result).toEqual(mockGraphStats);
    });
  });

  describe('getSubgraph', () => {
    it('fetches subgraph with default depth', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockGraphData });

      const result = await graphService.getSubgraph({ centerNodeId: 'node1' });

      expect(api.get).toHaveBeenCalledWith('/graph/subgraph', {
        params: { center_node_id: 'node1', depth: 1 },
      });
      expect(result).toEqual(mockGraphData);
    });

    it('fetches subgraph with custom depth', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockGraphData });

      await graphService.getSubgraph({ centerNodeId: 'node1', depth: 2 });

      expect(api.get).toHaveBeenCalledWith('/graph/subgraph', {
        params: { center_node_id: 'node1', depth: 2 },
      });
    });
  });

  describe('searchNodes', () => {
    it('searches nodes with keyword', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes });

      const result = await graphService.searchNodes({ keyword: 'test' });

      expect(api.get).toHaveBeenCalledWith('/graph/search', {
        params: { keyword: 'test', limit: 20 },
      });
      expect(result).toEqual(mockNodes);
    });

    it('searches nodes with custom limit', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockNodes });

      await graphService.searchNodes({ keyword: 'test', limit: 50 });

      expect(api.get).toHaveBeenCalledWith('/graph/search', {
        params: { keyword: 'test', limit: 50 },
      });
    });
  });

  describe('getNodesByIds', () => {
    it('fetches multiple nodes by IDs', async () => {
      vi.mocked(api.get)
        .mockResolvedValueOnce({ data: mockNodes[0] })
        .mockResolvedValueOnce({ data: mockNodes[1] });

      const result = await graphService.getNodesByIds(['node1', 'node2']);

      expect(result).toHaveLength(2);
      expect(result[0]).toEqual(mockNodes[0]);
      expect(result[1]).toEqual(mockNodes[1]);
    });

    it('handles failed requests gracefully', async () => {
      vi.mocked(api.get)
        .mockResolvedValueOnce({ data: mockNodes[0] })
        .mockRejectedValueOnce(new Error('Not found'));

      const result = await graphService.getNodesByIds(['node1', 'node2']);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual(mockNodes[0]);
    });
  });

  describe('getGraphData', () => {
    it('fetches complete graph data', async () => {
      vi.mocked(api.get)
        .mockResolvedValueOnce({ data: mockNodes })
        .mockResolvedValueOnce({ data: mockEdges });

      const result = await graphService.getGraphData();

      expect(result).toEqual(mockGraphData);
    });

    it('fetches graph data with filters', async () => {
      vi.mocked(api.get)
        .mockResolvedValueOnce({ data: mockNodes })
        .mockResolvedValueOnce({ data: mockEdges });

      await graphService.getGraphData({
        nodeLimit: 500,
        edgeLimit: 500,
        entityType: 'person',
        minWeight: 0.5,
      });

      expect(api.get).toHaveBeenCalledWith('/graph/nodes', {
        params: { limit: 500, offset: 0, entityType: 'person' },
      });
      expect(api.get).toHaveBeenCalledWith('/graph/edges', {
        params: { limit: 500, offset: 0, minWeight: 0.5 },
      });
    });
  });
});
