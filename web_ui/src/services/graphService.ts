import api from '@/utils/api';
import type {
  Node,
  Edge,
  GraphData,
  GraphStats,
} from '@/types/graph';

/**
 * Graph API Service
 * 提供超图数据访问的所有方法
 */
class GraphService {
  /**
   * 获取节点列表（支持分页和过滤）
   */
  async getNodes(params?: {
    limit?: number;
    offset?: number;
    entityType?: string;
  }): Promise<Node[]> {
    const response = await api.get<Node[]>('/graph/nodes', { params });
    return response.data;
  }

  /**
   * 获取单个节点详情
   */
  async getNodeById(nodeId: string): Promise<Node> {
    const response = await api.get<Node>(`/graph/nodes/${nodeId}`);
    return response.data;
  }

  /**
   * 获取边列表（支持分页和权重过滤）
   */
  async getEdges(params?: {
    limit?: number;
    offset?: number;
    minWeight?: number;
  }): Promise<Edge[]> {
    const response = await api.get<Edge[]>('/graph/edges', { params });
    return response.data;
  }

  /**
   * 获取单个边详情
   */
  async getEdgeById(edgeId: string): Promise<Edge> {
    const response = await api.get<Edge>(`/graph/edges/${edgeId}`);
    return response.data;
  }

  /**
   * 获取超图统计信息
   */
  async getStats(): Promise<GraphStats> {
    const response = await api.get<GraphStats>('/graph/stats');
    return response.data;
  }

  /**
   * 获取子图（以指定节点为中心）
   */
  async getSubgraph(params: {
    centerNodeId: string;
    depth?: number;
  }): Promise<GraphData> {
    const response = await api.get<GraphData>('/graph/subgraph', {
      params: {
        center_node_id: params.centerNodeId,
        depth: params.depth || 1,
      },
    });
    return response.data;
  }

  /**
   * 搜索节点（语义搜索）
   */
  async searchNodes(params: {
    keyword: string;
    limit?: number;
  }): Promise<Node[]> {
    const response = await api.get<Node[]>('/graph/search', {
      params: {
        keyword: params.keyword,
        limit: params.limit || 20,
      },
    });
    return response.data;
  }

  /**
   * 批量获取节点（通过 ID 列表）
   */
  async getNodesByIds(nodeIds: string[]): Promise<Node[]> {
    const promises = nodeIds.map(id => this.getNodeById(id));
    const results = await Promise.allSettled(promises);
    
    return results
      .filter((result): result is PromiseFulfilledResult<Node> => 
        result.status === 'fulfilled'
      )
      .map(result => result.value);
  }

  /**
   * 批量获取边（通过 ID 列表）
   */
  async getEdgesByIds(edgeIds: string[]): Promise<Edge[]> {
    const promises = edgeIds.map(id => this.getEdgeById(id));
    const results = await Promise.allSettled(promises);
    
    return results
      .filter((result): result is PromiseFulfilledResult<Edge> => 
        result.status === 'fulfilled'
      )
      .map(result => result.value);
  }

  /**
   * 获取完整图数据（节点 + 边）
   */
  async getGraphData(params?: {
    nodeLimit?: number;
    edgeLimit?: number;
    entityType?: string;
    minWeight?: number;
  }): Promise<GraphData> {
    const [nodes, edges] = await Promise.all([
      this.getNodes({
        limit: params?.nodeLimit || 1000,
        offset: 0,
        entityType: params?.entityType,
      }),
      this.getEdges({
        limit: params?.edgeLimit || 1000,
        offset: 0,
        minWeight: params?.minWeight,
      }),
    ]);

    return { nodes, edges };
  }
}

// 导出单例实例
export const graphService = new GraphService();

// 也导出类本身，以便需要时创建新实例
export default GraphService;
