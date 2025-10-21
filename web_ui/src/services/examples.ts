/**
 * API Services 使用示例
 * 
 * 这个文件展示了如何在 React 组件中使用 graphService 和 queryService
 */

import { graphService, queryService } from '@/services';
import { useGraphStore } from '@/stores/graphStore';
import { useQueryStore } from '@/stores/queryStore';

// ============================================================================
// 示例 1: 加载图数据
// ============================================================================

export async function loadGraphExample() {
  try {
    // 获取图统计信息
    const stats = await graphService.getStats();
    console.log('图统计:', stats);
    
    // 加载节点和边
    const graphData = await graphService.getGraphData({
      nodeLimit: 1000,
      edgeLimit: 1000,
      minWeight: 0.5, // 只加载权重 > 0.5 的边
    });
    
    console.log(`加载了 ${graphData.nodes.length} 个节点`);
    console.log(`加载了 ${graphData.edges.length} 条边`);
    
    return graphData;
  } catch (error) {
    console.error('加载图数据失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 2: 搜索节点
// ============================================================================

export async function searchNodesExample(keyword: string) {
  try {
    const results = await graphService.searchNodes({
      keyword,
      limit: 20,
    });
    
    console.log(`找到 ${results.length} 个匹配的节点`);
    results.forEach(node => {
      console.log(`- ${node.label} (${node.type}): ${node.description}`);
    });
    
    return results;
  } catch (error) {
    console.error('搜索失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 3: 获取子图
// ============================================================================

export async function getSubgraphExample(nodeId: string) {
  try {
    // 获取以指定节点为中心，深度为 2 的子图
    const subgraph = await graphService.getSubgraph({
      centerNodeId: nodeId,
      depth: 2,
    });
    
    console.log(`子图包含 ${subgraph.nodes.length} 个节点`);
    console.log(`子图包含 ${subgraph.edges.length} 条边`);
    
    return subgraph;
  } catch (error) {
    console.error('获取子图失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 4: 执行查询
// ============================================================================

export async function executeQueryExample(query: string) {
  try {
    const response = await queryService.executeQuery({
      query,
      mode: 'hybrid',
      topK: 60,
    });
    
    console.log('查询答案:', response.answer);
    console.log('执行时间:', response.executionTime, '秒');
    console.log('查询路径:', response.queryPath);
    console.log('使用的上下文:', response.contextUsed.length, '个片段');
    
    return response;
  } catch (error) {
    console.error('查询失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 5: 在 React 组件中使用（配合 Zustand Store）
// ============================================================================

export function useGraphDataLoader() {
  const { setGraphData, setLoading, setError } = useGraphStore();
  
  const loadGraph = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await graphService.getGraphData({
        nodeLimit: 1000,
        edgeLimit: 1000,
      });
      
      setGraphData(data);
    } catch (error: any) {
      setError(error.message || '加载图数据失败');
    } finally {
      setLoading(false);
    }
  };
  
  return { loadGraph };
}

export function useQueryExecutor() {
  const { setCurrentResponse, setQuerying, setError, addToHistory } = useQueryStore();
  
  const executeQuery = async (query: string, mode: 'local' | 'global' | 'hybrid' | 'naive' = 'hybrid') => {
    setQuerying(true);
    setError(null);
    
    try {
      const response = await queryService.executeQuery({
        query,
        mode,
      });
      
      setCurrentResponse(response);
      
      // 添加到历史记录
      addToHistory({
        query,
        mode,
        answer: response.answer,
        executionTime: response.executionTime,
      });
      
      return response;
    } catch (error: any) {
      setError(error.message || '查询失败');
      throw error;
    } finally {
      setQuerying(false);
    }
  };
  
  return { executeQuery };
}

// ============================================================================
// 示例 6: 批量操作
// ============================================================================

export async function batchOperationsExample() {
  try {
    // 批量获取节点
    const nodeIds = ['node1', 'node2', 'node3'];
    const nodes = await graphService.getNodesByIds(nodeIds);
    console.log(`成功获取 ${nodes.length} 个节点`);
    
    // 批量执行查询
    const queries = [
      { query: '什么是高血压？', mode: 'hybrid' as const },
      { query: '糖尿病的症状有哪些？', mode: 'local' as const },
    ];
    
    const responses = await queryService.executeBatchQueries(queries);
    console.log(`成功执行 ${responses.length} 个查询`);
    
    return { nodes, responses };
  } catch (error) {
    console.error('批量操作失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 7: 查询历史管理
// ============================================================================

export async function queryHistoryExample() {
  try {
    // 获取查询历史
    const history = await queryService.getQueryHistory(10);
    console.log(`历史记录: ${history.length} 条`);
    
    // 获取历史统计
    const stats = queryService.getHistoryStats();
    console.log('历史统计:', stats);
    
    // 导出历史
    const exported = queryService.exportHistory();
    console.log('导出的历史记录:', exported);
    
    // 重新执行历史查询
    if (history.length > 0) {
      const response = await queryService.reExecuteQuery(history[0]);
      console.log('重新执行查询结果:', response.answer);
    }
    
    return { history, stats };
  } catch (error) {
    console.error('历史管理失败:', error);
    throw error;
  }
}

// ============================================================================
// 示例 8: 错误处理
// ============================================================================

export async function errorHandlingExample() {
  try {
    // 尝试获取不存在的节点
    const node = await graphService.getNodeById('non-existent-id');
    console.log('节点:', node);
  } catch (error: any) {
    // 错误格式: { status, message, details }
    console.error('错误状态码:', error.status);
    console.error('错误消息:', error.message);
    console.error('错误详情:', error.details);
    
    if (error.status === 404) {
      console.log('节点不存在');
    } else if (error.status === 0) {
      console.log('网络错误');
    } else {
      console.log('其他错误');
    }
  }
}
