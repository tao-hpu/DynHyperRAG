export interface Node {
  id: string;
  label: string;
  type: string;
  description: string;
  weight: number;
  relevanceScore?: number;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  relation: string;
  description: string;
  weight: number;
  entities: string[];
  isHyperedge: boolean;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

export interface GraphStats {
  numNodes: number;
  numEdges: number;
  numHyperedges: number;
  avgDegree: number;
  density: number;
}

export interface GraphFilter {
  entityTypes: string[];
  minWeight: number;
  maxWeight: number;
}

export interface ViewportState {
  zoom: number;
  pan: { x: number; y: number };
}
