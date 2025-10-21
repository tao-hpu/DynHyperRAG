/**
 * Services Index
 * 统一导出所有 API 服务
 */

export { graphService, default as GraphService } from './graphService';
export { queryService, default as QueryService } from './queryService';

// 重新导出类型以便使用
export type {
  Node,
  Edge,
  GraphData,
  GraphStats,
  GraphFilter,
  ViewportState,
} from '@/types/graph';

export type {
  QueryMode,
  QueryRequest,
  QueryResponse,
  QueryPath,
  QueryHistoryItem,
} from '@/types/query';
