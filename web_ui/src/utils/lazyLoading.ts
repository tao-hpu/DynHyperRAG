/**
 * Lazy Loading Utilities
 * 懒加载工具 - 按需加载图数据
 */

import type { GraphData, Node, Edge } from '@/types/graph';
import { graphService } from '@/services/graphService';

export interface LazyLoadingOptions {
  initialLimit: number; // 初始加载的节点数量
  batchSize: number; // 每次加载的批次大小
  loadThreshold: number; // 触发加载的阈值（距离边界的距离）
  cacheEnabled: boolean; // 是否启用缓存
}

export interface LoadedDataCache {
  nodes: Map<string, Node>;
  edges: Map<string, Edge>;
  nodeOffset: number;
  edgeOffset: number;
  hasMoreNodes: boolean;
  hasMoreEdges: boolean;
}

/**
 * 懒加载管理器
 */
export class LazyLoadingManager {
  private options: LazyLoadingOptions;
  private cache: LoadedDataCache;
  private loading: boolean = false;
  private loadingPromise: Promise<{ nodes: Node[]; edges: Edge[] }> | null = null;

  constructor(options?: Partial<LazyLoadingOptions>) {
    this.options = {
      initialLimit: 1000,
      batchSize: 500,
      loadThreshold: 0.8, // 当显示80%的数据时触发加载
      cacheEnabled: true,
      ...options,
    };

    this.cache = {
      nodes: new Map(),
      edges: new Map(),
      nodeOffset: 0,
      edgeOffset: 0,
      hasMoreNodes: true,
      hasMoreEdges: true,
    };
  }

  /**
   * 初始加载核心数据
   */
  async loadInitialData(params?: {
    entityType?: string;
    minWeight?: number;
  }): Promise<GraphData> {
    this.loading = true;

    try {
      const data = await graphService.getGraphData({
        nodeLimit: this.options.initialLimit,
        edgeLimit: this.options.initialLimit,
        entityType: params?.entityType,
        minWeight: params?.minWeight,
      });

      // 更新缓存
      if (this.options.cacheEnabled) {
        data.nodes.forEach(node => this.cache.nodes.set(node.id, node));
        data.edges.forEach(edge => this.cache.edges.set(edge.id, edge));
        
        this.cache.nodeOffset = data.nodes.length;
        this.cache.edgeOffset = data.edges.length;
        
        // 如果返回的数据少于请求的数量，说明没有更多数据了
        this.cache.hasMoreNodes = data.nodes.length >= this.options.initialLimit;
        this.cache.hasMoreEdges = data.edges.length >= this.options.initialLimit;
      }

      return data;
    } finally {
      this.loading = false;
    }
  }

  /**
   * 加载更多节点
   */
  async loadMoreNodes(params?: {
    entityType?: string;
  }): Promise<Node[]> {
    if (this.loading || !this.cache.hasMoreNodes) {
      return [];
    }

    this.loading = true;

    try {
      const nodes = await graphService.getNodes({
        limit: this.options.batchSize,
        offset: this.cache.nodeOffset,
        entityType: params?.entityType,
      });

      // 更新缓存
      if (this.options.cacheEnabled) {
        nodes.forEach(node => this.cache.nodes.set(node.id, node));
        this.cache.nodeOffset += nodes.length;
        this.cache.hasMoreNodes = nodes.length >= this.options.batchSize;
      }

      return nodes;
    } finally {
      this.loading = false;
    }
  }

  /**
   * 加载更多边
   */
  async loadMoreEdges(params?: {
    minWeight?: number;
  }): Promise<Edge[]> {
    if (this.loading || !this.cache.hasMoreEdges) {
      return [];
    }

    this.loading = true;

    try {
      const edges = await graphService.getEdges({
        limit: this.options.batchSize,
        offset: this.cache.edgeOffset,
        minWeight: params?.minWeight,
      });

      // 更新缓存
      if (this.options.cacheEnabled) {
        edges.forEach(edge => this.cache.edges.set(edge.id, edge));
        this.cache.edgeOffset += edges.length;
        this.cache.hasMoreEdges = edges.length >= this.options.batchSize;
      }

      return edges;
    } finally {
      this.loading = false;
    }
  }

  /**
   * 检查是否需要加载更多数据
   */
  shouldLoadMore(currentVisibleCount: number, totalLoadedCount: number): boolean {
    if (this.loading) return false;
    
    const ratio = currentVisibleCount / totalLoadedCount;
    return ratio >= this.options.loadThreshold;
  }

  /**
   * 自动加载更多数据（如果需要）
   */
  async autoLoadMore(
    visibleNodeCount: number,
    visibleEdgeCount: number,
    params?: {
      entityType?: string;
      minWeight?: number;
    }
  ): Promise<{ nodes: Node[]; edges: Edge[] }> {
    // 避免重复加载
    if (this.loadingPromise) {
      await this.loadingPromise;
      return { nodes: [], edges: [] };
    }

    const loadedNodeCount = this.cache.nodes.size;
    const loadedEdgeCount = this.cache.edges.size;

    const needMoreNodes = this.shouldLoadMore(visibleNodeCount, loadedNodeCount) && this.cache.hasMoreNodes;
    const needMoreEdges = this.shouldLoadMore(visibleEdgeCount, loadedEdgeCount) && this.cache.hasMoreEdges;

    if (!needMoreNodes && !needMoreEdges) {
      return { nodes: [], edges: [] };
    }

    // 创建加载 Promise
    this.loadingPromise = (async () => {
      const results = await Promise.all([
        needMoreNodes ? this.loadMoreNodes(params) : Promise.resolve([]),
        needMoreEdges ? this.loadMoreEdges(params) : Promise.resolve([]),
      ]);

      this.loadingPromise = null;
      return { nodes: results[0], edges: results[1] };
    })();

    return this.loadingPromise;
  }

  /**
   * 获取缓存的数据
   */
  getCachedData(): GraphData {
    return {
      nodes: Array.from(this.cache.nodes.values()),
      edges: Array.from(this.cache.edges.values()),
    };
  }

  /**
   * 获取缓存的节点
   */
  getCachedNode(nodeId: string): Node | undefined {
    return this.cache.nodes.get(nodeId);
  }

  /**
   * 获取缓存的边
   */
  getCachedEdge(edgeId: string): Edge | undefined {
    return this.cache.edges.get(edgeId);
  }

  /**
   * 清空缓存
   */
  clearCache(): void {
    this.cache.nodes.clear();
    this.cache.edges.clear();
    this.cache.nodeOffset = 0;
    this.cache.edgeOffset = 0;
    this.cache.hasMoreNodes = true;
    this.cache.hasMoreEdges = true;
  }

  /**
   * 获取加载状态
   */
  isLoading(): boolean {
    return this.loading;
  }

  /**
   * 获取统计信息
   */
  getStats(): {
    cachedNodes: number;
    cachedEdges: number;
    hasMoreNodes: boolean;
    hasMoreEdges: boolean;
    isLoading: boolean;
  } {
    return {
      cachedNodes: this.cache.nodes.size,
      cachedEdges: this.cache.edges.size,
      hasMoreNodes: this.cache.hasMoreNodes,
      hasMoreEdges: this.cache.hasMoreEdges,
      isLoading: this.loading,
    };
  }

  /**
   * 预加载子图数据
   */
  async preloadSubgraph(centerNodeId: string, depth: number = 1): Promise<GraphData> {
    const subgraph = await graphService.getSubgraph({
      centerNodeId,
      depth,
    });

    // 将子图数据添加到缓存
    if (this.options.cacheEnabled) {
      subgraph.nodes.forEach(node => {
        if (!this.cache.nodes.has(node.id)) {
          this.cache.nodes.set(node.id, node);
        }
      });
      
      subgraph.edges.forEach(edge => {
        if (!this.cache.edges.has(edge.id)) {
          this.cache.edges.set(edge.id, edge);
        }
      });
    }

    return subgraph;
  }
}

/**
 * 创建加载指示器组件的数据
 */
export interface LoadingIndicatorData {
  isLoading: boolean;
  progress: number; // 0-100
  message: string;
}

export function createLoadingIndicator(
  manager: LazyLoadingManager,
  totalExpectedNodes?: number
): LoadingIndicatorData {
  const stats = manager.getStats();
  
  let progress = 0;
  if (totalExpectedNodes && totalExpectedNodes > 0) {
    progress = Math.min(100, (stats.cachedNodes / totalExpectedNodes) * 100);
  }

  let message = 'Loading graph data...';
  if (stats.isLoading) {
    message = `Loading more data... (${stats.cachedNodes} nodes, ${stats.cachedEdges} edges)`;
  } else if (!stats.hasMoreNodes && !stats.hasMoreEdges) {
    message = 'All data loaded';
  }

  return {
    isLoading: stats.isLoading,
    progress,
    message,
  };
}
