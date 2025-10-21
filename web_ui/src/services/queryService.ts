import api from '@/utils/api';
import type {
  QueryRequest,
  QueryResponse,
  QueryHistoryItem,
  QueryMode,
} from '@/types/query';

/**
 * Query API Service
 * 提供查询相关的所有方法
 */
class QueryService {
  private historyCache: QueryHistoryItem[] = [];
  private readonly HISTORY_STORAGE_KEY = 'hypergraph_query_history';
  private readonly MAX_HISTORY_SIZE = 50;

  constructor() {
    // 从 localStorage 加载历史记录
    this.loadHistoryFromStorage();
  }

  /**
   * 执行 RAG 查询
   */
  async executeQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await api.post<QueryResponse>('/query/', {
      query: request.query,
      mode: request.mode,
      top_k: request.topK || 60,
      max_token_for_text_unit: request.maxTokenForTextUnit || 4000,
      max_token_for_local_context: request.maxTokenForLocalContext || 4000,
      max_token_for_global_context: request.maxTokenForGlobalContext || 4000,
    });

    // 将查询添加到历史记录
    this.addToHistory({
      id: this.generateId(),
      query: request.query,
      mode: request.mode,
      answer: response.data.answer,
      timestamp: Date.now(),
      executionTime: response.data.executionTime,
    });

    return response.data;
  }

  /**
   * 获取查询历史
   */
  async getQueryHistory(limit?: number): Promise<QueryHistoryItem[]> {
    try {
      // 尝试从服务器获取历史记录
      const response = await api.get<QueryHistoryItem[]>('/query/history', {
        params: { limit: limit || 10 },
      });
      return response.data;
    } catch (error) {
      // 如果服务器不支持历史记录，返回本地缓存
      console.warn('Server history not available, using local cache:', error);
      return this.getLocalHistory(limit);
    }
  }

  /**
   * 获取本地历史记录
   */
  getLocalHistory(limit?: number): QueryHistoryItem[] {
    const history = [...this.historyCache].reverse(); // 最新的在前
    return limit ? history.slice(0, limit) : history;
  }

  /**
   * 清除历史记录
   */
  clearHistory(): void {
    this.historyCache = [];
    this.saveHistoryToStorage();
  }

  /**
   * 删除单条历史记录
   */
  deleteHistoryItem(id: string): void {
    this.historyCache = this.historyCache.filter(item => item.id !== id);
    this.saveHistoryToStorage();
  }

  /**
   * 重新执行历史查询
   */
  async reExecuteQuery(historyItem: QueryHistoryItem): Promise<QueryResponse> {
    return this.executeQuery({
      query: historyItem.query,
      mode: historyItem.mode,
    });
  }

  /**
   * 执行批量查询
   */
  async executeBatchQueries(
    queries: Array<{ query: string; mode: QueryMode }>
  ): Promise<QueryResponse[]> {
    const promises = queries.map(q => this.executeQuery(q));
    const results = await Promise.allSettled(promises);
    
    return results
      .filter((result): result is PromiseFulfilledResult<QueryResponse> => 
        result.status === 'fulfilled'
      )
      .map(result => result.value);
  }

  /**
   * 添加到历史记录
   */
  private addToHistory(item: QueryHistoryItem): void {
    // 添加到缓存
    this.historyCache.push(item);

    // 限制历史记录大小
    if (this.historyCache.length > this.MAX_HISTORY_SIZE) {
      this.historyCache = this.historyCache.slice(-this.MAX_HISTORY_SIZE);
    }

    // 保存到 localStorage
    this.saveHistoryToStorage();
  }

  /**
   * 从 localStorage 加载历史记录
   */
  private loadHistoryFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.HISTORY_STORAGE_KEY);
      if (stored) {
        this.historyCache = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load query history from storage:', error);
      this.historyCache = [];
    }
  }

  /**
   * 保存历史记录到 localStorage
   */
  private saveHistoryToStorage(): void {
    try {
      localStorage.setItem(
        this.HISTORY_STORAGE_KEY,
        JSON.stringify(this.historyCache)
      );
    } catch (error) {
      console.error('Failed to save query history to storage:', error);
    }
  }

  /**
   * 生成唯一 ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 导出历史记录为 JSON
   */
  exportHistory(): string {
    return JSON.stringify(this.historyCache, null, 2);
  }

  /**
   * 从 JSON 导入历史记录
   */
  importHistory(jsonString: string): void {
    try {
      const imported = JSON.parse(jsonString);
      if (Array.isArray(imported)) {
        this.historyCache = imported;
        this.saveHistoryToStorage();
      } else {
        throw new Error('Invalid history format');
      }
    } catch (error) {
      console.error('Failed to import history:', error);
      throw error;
    }
  }

  /**
   * 获取历史统计信息
   */
  getHistoryStats(): {
    totalQueries: number;
    averageExecutionTime: number;
    modeDistribution: Record<QueryMode, number>;
  } {
    const totalQueries = this.historyCache.length;
    
    const averageExecutionTime = totalQueries > 0
      ? this.historyCache.reduce((sum, item) => sum + item.executionTime, 0) / totalQueries
      : 0;

    const modeDistribution: Record<QueryMode, number> = {
      local: 0,
      global: 0,
      hybrid: 0,
      naive: 0,
    };

    this.historyCache.forEach(item => {
      modeDistribution[item.mode]++;
    });

    return {
      totalQueries,
      averageExecutionTime,
      modeDistribution,
    };
  }
}

// 导出单例实例
export const queryService = new QueryService();

// 也导出类本身，以便需要时创建新实例
export default QueryService;
