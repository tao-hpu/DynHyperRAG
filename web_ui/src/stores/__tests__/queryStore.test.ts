import { describe, it, expect, beforeEach } from 'vitest';
import { useQueryStore } from '../queryStore';
import { mockQueryResponse } from '@/test/mockData';

describe('QueryStore', () => {
  beforeEach(() => {
    // Reset store state
    useQueryStore.setState({
      currentQuery: '',
      currentMode: 'hybrid',
      currentResponse: null,
      history: [],
      config: {
        topK: 60,
        maxTokenForTextUnit: 4000,
        maxTokenForLocalContext: 4000,
        maxTokenForGlobalContext: 4000,
      },
      isQuerying: false,
      error: null,
    });
  });

  describe('setCurrentQuery', () => {
    it('sets current query', () => {
      const { setCurrentQuery } = useQueryStore.getState();
      
      setCurrentQuery('What is hypertension?');
      
      expect(useQueryStore.getState().currentQuery).toBe('What is hypertension?');
    });
  });

  describe('setCurrentMode', () => {
    it('sets current mode', () => {
      const { setCurrentMode } = useQueryStore.getState();
      
      setCurrentMode('local');
      
      expect(useQueryStore.getState().currentMode).toBe('local');
    });
  });

  describe('setCurrentResponse', () => {
    it('sets current response', () => {
      const { setCurrentResponse } = useQueryStore.getState();
      
      setCurrentResponse(mockQueryResponse);
      
      expect(useQueryStore.getState().currentResponse).toEqual(mockQueryResponse);
    });

    it('clears error when setting response', () => {
      const { setError, setCurrentResponse } = useQueryStore.getState();
      
      setError('Test error');
      setCurrentResponse(mockQueryResponse);
      
      expect(useQueryStore.getState().error).toBeNull();
    });
  });

  describe('setConfig', () => {
    it('updates config partially', () => {
      const { setConfig } = useQueryStore.getState();
      
      setConfig({ topK: 100 });
      
      const config = useQueryStore.getState().config;
      expect(config.topK).toBe(100);
      expect(config.maxTokenForTextUnit).toBe(4000); // Unchanged
    });

    it('updates multiple config properties', () => {
      const { setConfig } = useQueryStore.getState();
      
      setConfig({ topK: 100, maxTokenForTextUnit: 5000 });
      
      const config = useQueryStore.getState().config;
      expect(config.topK).toBe(100);
      expect(config.maxTokenForTextUnit).toBe(5000);
    });
  });

  describe('addToHistory', () => {
    it('adds item to history', () => {
      const { addToHistory } = useQueryStore.getState();
      
      addToHistory({
        query: 'Test query',
        mode: 'hybrid',
        answer: 'Test answer',
        executionTime: 2.5,
      });
      
      const history = useQueryStore.getState().history;
      expect(history).toHaveLength(1);
      expect(history[0].query).toBe('Test query');
      expect(history[0]).toHaveProperty('id');
      expect(history[0]).toHaveProperty('timestamp');
    });

    it('adds new items to the beginning', () => {
      const { addToHistory } = useQueryStore.getState();
      
      addToHistory({
        query: 'Query 1',
        mode: 'hybrid',
        answer: 'Answer 1',
        executionTime: 2.5,
      });
      
      addToHistory({
        query: 'Query 2',
        mode: 'local',
        answer: 'Answer 2',
        executionTime: 3.0,
      });
      
      const history = useQueryStore.getState().history;
      expect(history[0].query).toBe('Query 2'); // Most recent first
      expect(history[1].query).toBe('Query 1');
    });

    it('limits history to 50 items', () => {
      const { addToHistory } = useQueryStore.getState();
      
      // Add 60 items
      for (let i = 0; i < 60; i++) {
        addToHistory({
          query: `Query ${i}`,
          mode: 'hybrid',
          answer: `Answer ${i}`,
          executionTime: 2.5,
        });
      }
      
      const history = useQueryStore.getState().history;
      expect(history).toHaveLength(50);
    });
  });

  describe('clearHistory', () => {
    it('clears all history', () => {
      const { addToHistory, clearHistory } = useQueryStore.getState();
      
      addToHistory({
        query: 'Test',
        mode: 'hybrid',
        answer: 'Answer',
        executionTime: 2.5,
      });
      
      clearHistory();
      
      expect(useQueryStore.getState().history).toHaveLength(0);
    });
  });

  describe('removeFromHistory', () => {
    it('removes specific history item', () => {
      const { addToHistory, removeFromHistory } = useQueryStore.getState();
      
      addToHistory({
        query: 'Query 1',
        mode: 'hybrid',
        answer: 'Answer 1',
        executionTime: 2.5,
      });
      
      addToHistory({
        query: 'Query 2',
        mode: 'local',
        answer: 'Answer 2',
        executionTime: 3.0,
      });
      
      const history = useQueryStore.getState().history;
      const idToRemove = history[0].id;
      
      removeFromHistory(idToRemove);
      
      const updatedHistory = useQueryStore.getState().history;
      expect(updatedHistory).toHaveLength(1);
      expect(updatedHistory[0].query).toBe('Query 1');
    });
  });

  describe('getQueryRequest', () => {
    it('builds query request from current state', () => {
      const { setCurrentQuery, setCurrentMode, setConfig, getQueryRequest } = useQueryStore.getState();
      
      setCurrentQuery('What is hypertension?');
      setCurrentMode('local');
      setConfig({ topK: 100 });
      
      const request = getQueryRequest();
      
      expect(request).toEqual({
        query: 'What is hypertension?',
        mode: 'local',
        topK: 100,
        maxTokenForTextUnit: 4000,
        maxTokenForLocalContext: 4000,
        maxTokenForGlobalContext: 4000,
      });
    });
  });

  describe('loading and error states', () => {
    it('sets querying state', () => {
      const { setQuerying } = useQueryStore.getState();
      
      setQuerying(true);
      expect(useQueryStore.getState().isQuerying).toBe(true);
      
      setQuerying(false);
      expect(useQueryStore.getState().isQuerying).toBe(false);
    });

    it('sets error state', () => {
      const { setError } = useQueryStore.getState();
      
      setError('Test error');
      expect(useQueryStore.getState().error).toBe('Test error');
      expect(useQueryStore.getState().isQuerying).toBe(false);
    });
  });
});
