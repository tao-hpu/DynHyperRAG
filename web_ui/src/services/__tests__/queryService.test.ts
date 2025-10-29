import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { queryService } from '../queryService';
import api from '@/utils/api';
import { mockQueryResponse } from '@/test/mockData';

// Mock the API
vi.mock('@/utils/api');

describe('QueryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  afterEach(() => {
    queryService.clearHistory();
  });

  describe('executeQuery', () => {
    it('executes query successfully', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      const result = await queryService.executeQuery({
        query: 'What is hypertension?',
        mode: 'hybrid',
      });

      expect(api.post).toHaveBeenCalledWith('/query/', {
        query: 'What is hypertension?',
        mode: 'hybrid',
        top_k: 60,
        max_token_for_text_unit: 4000,
        max_token_for_local_context: 4000,
        max_token_for_global_context: 4000,
      });
      expect(result).toEqual(mockQueryResponse);
    });

    it('executes query with custom parameters', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({
        query: 'Test query',
        mode: 'local',
        topK: 100,
        maxTokenForTextUnit: 5000,
        maxTokenForLocalContext: 5000,
        maxTokenForGlobalContext: 5000,
      });

      expect(api.post).toHaveBeenCalledWith('/query/', {
        query: 'Test query',
        mode: 'local',
        top_k: 100,
        max_token_for_text_unit: 5000,
        max_token_for_local_context: 5000,
        max_token_for_global_context: 5000,
      });
    });

    it('adds query to history after execution', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({
        query: 'Test query',
        mode: 'hybrid',
      });

      const history = queryService.getLocalHistory();
      expect(history).toHaveLength(1);
      expect(history[0].query).toBe('Test query');
      expect(history[0].mode).toBe('hybrid');
    });
  });

  describe('getQueryHistory', () => {
    it('fetches history from server', async () => {
      const mockHistory = [
        {
          id: '1',
          query: 'Query 1',
          mode: 'hybrid' as const,
          answer: 'Answer 1',
          timestamp: Date.now(),
          executionTime: 2.5,
        },
      ];
      vi.mocked(api.get).mockResolvedValue({ data: mockHistory });

      const result = await queryService.getQueryHistory();

      expect(api.get).toHaveBeenCalledWith('/query/history', {
        params: { limit: 10 },
      });
      expect(result).toEqual(mockHistory);
    });

    it('falls back to local cache when server fails', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Server error'));
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      // Add some local history
      await queryService.executeQuery({
        query: 'Local query',
        mode: 'hybrid',
      });

      const result = await queryService.getQueryHistory();

      expect(result).toHaveLength(1);
      expect(result[0].query).toBe('Local query');
    });
  });

  describe('getLocalHistory', () => {
    it('returns local history in reverse order', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Query 1', mode: 'hybrid' });
      await queryService.executeQuery({ query: 'Query 2', mode: 'local' });

      const history = queryService.getLocalHistory();

      expect(history).toHaveLength(2);
      expect(history[0].query).toBe('Query 2'); // Most recent first
      expect(history[1].query).toBe('Query 1');
    });

    it('limits history size', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      const history = queryService.getLocalHistory(1);

      expect(history.length).toBeLessThanOrEqual(1);
    });
  });

  describe('clearHistory', () => {
    it('clears all history', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Test', mode: 'hybrid' });
      expect(queryService.getLocalHistory()).toHaveLength(1);

      queryService.clearHistory();
      expect(queryService.getLocalHistory()).toHaveLength(0);
    });
  });

  describe('deleteHistoryItem', () => {
    it('deletes specific history item', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Query 1', mode: 'hybrid' });
      await queryService.executeQuery({ query: 'Query 2', mode: 'local' });

      const history = queryService.getLocalHistory();
      const idToDelete = history[0].id;

      queryService.deleteHistoryItem(idToDelete);

      const updatedHistory = queryService.getLocalHistory();
      expect(updatedHistory).toHaveLength(1);
      expect(updatedHistory[0].query).toBe('Query 1');
    });
  });

  describe('reExecuteQuery', () => {
    it('re-executes query from history', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Original query', mode: 'hybrid' });

      const history = queryService.getLocalHistory();
      const result = await queryService.reExecuteQuery(history[0]);

      expect(result).toEqual(mockQueryResponse);
      expect(api.post).toHaveBeenCalledTimes(2); // Original + re-execute
    });
  });

  describe('executeBatchQueries', () => {
    it('executes multiple queries', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      const queries = [
        { query: 'Query 1', mode: 'hybrid' as const },
        { query: 'Query 2', mode: 'local' as const },
      ];

      const results = await queryService.executeBatchQueries(queries);

      expect(results).toHaveLength(2);
      expect(api.post).toHaveBeenCalledTimes(2);
    });

    it('handles partial failures in batch', async () => {
      vi.mocked(api.post)
        .mockResolvedValueOnce({ data: mockQueryResponse })
        .mockRejectedValueOnce(new Error('Query failed'));

      const queries = [
        { query: 'Query 1', mode: 'hybrid' as const },
        { query: 'Query 2', mode: 'local' as const },
      ];

      const results = await queryService.executeBatchQueries(queries);

      expect(results).toHaveLength(1); // Only successful query
    });
  });

  describe('exportHistory', () => {
    it('exports history as JSON string', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Test', mode: 'hybrid' });

      const exported = queryService.exportHistory();
      const parsed = JSON.parse(exported);

      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed[0].query).toBe('Test');
    });
  });

  describe('importHistory', () => {
    it('imports history from JSON string', async () => {
      const historyData = [
        {
          id: '1',
          query: 'Imported query',
          mode: 'hybrid',
          answer: 'Answer',
          timestamp: Date.now(),
          executionTime: 2.5,
        },
      ];

      queryService.importHistory(JSON.stringify(historyData));

      const history = queryService.getLocalHistory();
      expect(history).toHaveLength(1);
      expect(history[0].query).toBe('Imported query');
    });

    it('throws error for invalid JSON', () => {
      expect(() => {
        queryService.importHistory('invalid json');
      }).toThrow();
    });
  });

  describe('getHistoryStats', () => {
    it('calculates history statistics', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockQueryResponse });

      await queryService.executeQuery({ query: 'Query 1', mode: 'hybrid' });
      await queryService.executeQuery({ query: 'Query 2', mode: 'local' });
      await queryService.executeQuery({ query: 'Query 3', mode: 'hybrid' });

      const stats = queryService.getHistoryStats();

      expect(stats.totalQueries).toBe(3);
      expect(stats.averageExecutionTime).toBeGreaterThan(0);
      expect(stats.modeDistribution.hybrid).toBe(2);
      expect(stats.modeDistribution.local).toBe(1);
    });
  });
});
