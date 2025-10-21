import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { QueryRequest, QueryResponse, QueryHistoryItem, QueryMode } from '@/types/query';

interface QueryState {
  // 当前查询
  currentQuery: string;
  currentMode: QueryMode;
  currentResponse: QueryResponse | null;
  
  // 查询历史
  history: QueryHistoryItem[];
  
  // 查询配置
  config: {
    topK: number;
    maxTokenForTextUnit: number;
    maxTokenForLocalContext: number;
    maxTokenForGlobalContext: number;
  };
  
  // 加载状态
  isQuerying: boolean;
  error: string | null;
  
  // Actions
  setCurrentQuery: (query: string) => void;
  setCurrentMode: (mode: QueryMode) => void;
  setCurrentResponse: (response: QueryResponse | null) => void;
  
  setConfig: (config: Partial<QueryState['config']>) => void;
  
  addToHistory: (item: Omit<QueryHistoryItem, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  removeFromHistory: (id: string) => void;
  
  setQuerying: (isQuerying: boolean) => void;
  setError: (error: string | null) => void;
  
  // 辅助方法
  getQueryRequest: () => QueryRequest;
}

const defaultConfig = {
  topK: 60,
  maxTokenForTextUnit: 4000,
  maxTokenForLocalContext: 4000,
  maxTokenForGlobalContext: 4000,
};

export const useQueryStore = create<QueryState>()(
  persist(
    (set, get) => ({
      // 初始状态
      currentQuery: '',
      currentMode: 'hybrid',
      currentResponse: null,
      history: [],
      config: defaultConfig,
      isQuerying: false,
      error: null,

      // Actions
      setCurrentQuery: (query) => set({ currentQuery: query }),
      
      setCurrentMode: (mode) => set({ currentMode: mode }),
      
      setCurrentResponse: (response) => set({ 
        currentResponse: response,
        error: null,
      }),
      
      setConfig: (newConfig) => set((state) => ({ 
        config: { ...state.config, ...newConfig } 
      })),
      
      addToHistory: (item) => {
        const historyItem: QueryHistoryItem = {
          ...item,
          id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: Date.now(),
        };
        
        set((state) => ({
          history: [historyItem, ...state.history].slice(0, 50), // 最多保存 50 条
        }));
      },
      
      clearHistory: () => set({ history: [] }),
      
      removeFromHistory: (id) => set((state) => ({
        history: state.history.filter(item => item.id !== id),
      })),
      
      setQuerying: (isQuerying) => set({ isQuerying }),
      
      setError: (error) => set({ error, isQuerying: false }),
      
      // 辅助方法
      getQueryRequest: () => {
        const { currentQuery, currentMode, config } = get();
        return {
          query: currentQuery,
          mode: currentMode,
          topK: config.topK,
          maxTokenForTextUnit: config.maxTokenForTextUnit,
          maxTokenForLocalContext: config.maxTokenForLocalContext,
          maxTokenForGlobalContext: config.maxTokenForGlobalContext,
        };
      },
    }),
    {
      name: 'query-store',
      partialize: (state) => ({
        // 持久化这些字段
        history: state.history,
        config: state.config,
        currentMode: state.currentMode,
      }),
    }
  )
);
