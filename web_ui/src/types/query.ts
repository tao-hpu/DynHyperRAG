export type QueryMode = 'local' | 'global' | 'hybrid' | 'naive';

export interface QueryRequest {
  query: string;
  mode: QueryMode;
  topK?: number;
  maxTokenForTextUnit?: number;
  maxTokenForLocalContext?: number;
  maxTokenForGlobalContext?: number;
}

export interface QueryPath {
  nodes: string[];
  edges: string[];
  scores: Record<string, number>;
}

export interface QueryResponse {
  answer: string;
  queryPath: QueryPath;
  contextUsed: string[];
  executionTime: number;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  mode: QueryMode;
  answer: string;
  timestamp: number;
  executionTime: number;
}
