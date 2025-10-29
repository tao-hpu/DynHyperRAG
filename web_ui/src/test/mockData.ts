import type { Node, Edge, GraphData, GraphStats } from '@/types/graph';
import type { QueryResponse, QueryPath } from '@/types/query';

export const mockNodes: Node[] = [
  {
    id: 'node1',
    label: 'Test Node 1',
    type: 'person',
    description: 'A test person node',
    weight: 5.0,
  },
  {
    id: 'node2',
    label: 'Test Node 2',
    type: 'organization',
    description: 'A test organization node',
    weight: 3.5,
  },
  {
    id: 'node3',
    label: 'Test Node 3',
    type: 'location',
    description: 'A test location node',
    weight: 4.2,
  },
];

export const mockEdges: Edge[] = [
  {
    id: 'edge1',
    source: 'node1',
    target: 'node2',
    relation: 'works_at',
    description: 'Person works at organization',
    weight: 0.8,
    entities: ['node1', 'node2'],
    isHyperedge: false,
  },
  {
    id: 'edge2',
    source: 'node1',
    target: 'node3',
    relation: 'lives_in',
    description: 'Person lives in location',
    weight: 0.9,
    entities: ['node1', 'node2', 'node3'],
    isHyperedge: true,
  },
];

export const mockGraphData: GraphData = {
  nodes: mockNodes,
  edges: mockEdges,
};

export const mockGraphStats: GraphStats = {
  numNodes: 100,
  numEdges: 150,
  numHyperedges: 45,
  avgDegree: 3.0,
  density: 0.015,
};

export const mockQueryPath: QueryPath = {
  nodes: ['node1', 'node2'],
  edges: ['edge1'],
  scores: {
    node1: 0.9,
    node2: 0.7,
  },
  nodeTypes: {
    node1: 'local',
    node2: 'global',
  },
};

export const mockQueryResponse: QueryResponse = {
  answer: 'This is a test answer from the RAG system.',
  queryPath: mockQueryPath,
  contextUsed: ['Context chunk 1', 'Context chunk 2'],
  executionTime: 2.5,
};
