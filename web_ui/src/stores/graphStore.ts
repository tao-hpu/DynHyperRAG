import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { GraphData, GraphStats, GraphFilter, ViewportState, Node, Edge } from '@/types/graph';

interface GraphState {
  // 图数据
  graphData: GraphData | null;
  stats: GraphStats | null;
  
  // 选中状态
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  highlightedNodes: Set<string>;
  highlightedEdges: Set<string>;
  
  // 过滤器
  filter: GraphFilter;
  
  // 视口状态
  viewport: ViewportState;
  
  // 加载状态
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setGraphData: (data: GraphData) => void;
  setStats: (stats: GraphStats) => void;
  
  selectNode: (nodeId: string | null) => void;
  selectEdge: (edgeId: string | null) => void;
  
  highlightNodes: (nodeIds: string[]) => void;
  highlightEdges: (edgeIds: string[]) => void;
  clearHighlights: () => void;
  
  setFilter: (filter: Partial<GraphFilter>) => void;
  resetFilter: () => void;
  
  setViewport: (viewport: Partial<ViewportState>) => void;
  
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  
  // 辅助方法
  getNodeById: (nodeId: string) => Node | undefined;
  getEdgeById: (edgeId: string) => Edge | undefined;
  getFilteredData: () => GraphData;
}

const defaultFilter: GraphFilter = {
  entityTypes: [],
  minWeight: 0,
  maxWeight: 1,
};

const defaultViewport: ViewportState = {
  zoom: 1,
  pan: { x: 0, y: 0 },
};

export const useGraphStore = create<GraphState>()(
  persist(
    (set, get) => ({
      // 初始状态
      graphData: null,
      stats: null,
      selectedNodeId: null,
      selectedEdgeId: null,
      highlightedNodes: new Set(),
      highlightedEdges: new Set(),
      filter: defaultFilter,
      viewport: defaultViewport,
      isLoading: false,
      error: null,

      // Actions
      setGraphData: (data) => set({ graphData: data, error: null }),
      
      setStats: (stats) => set({ stats }),
      
      selectNode: (nodeId) => set({ 
        selectedNodeId: nodeId,
        selectedEdgeId: null, // 取消边的选择
      }),
      
      selectEdge: (edgeId) => set({ 
        selectedEdgeId: edgeId,
        selectedNodeId: null, // 取消节点的选择
      }),
      
      highlightNodes: (nodeIds) => set({ 
        highlightedNodes: new Set(nodeIds) 
      }),
      
      highlightEdges: (edgeIds) => set({ 
        highlightedEdges: new Set(edgeIds) 
      }),
      
      clearHighlights: () => set({ 
        highlightedNodes: new Set(),
        highlightedEdges: new Set(),
      }),
      
      setFilter: (newFilter) => set((state) => ({ 
        filter: { ...state.filter, ...newFilter } 
      })),
      
      resetFilter: () => set({ filter: defaultFilter }),
      
      setViewport: (newViewport) => set((state) => ({ 
        viewport: { ...state.viewport, ...newViewport } 
      })),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error, isLoading: false }),
      
      // 辅助方法
      getNodeById: (nodeId) => {
        const { graphData } = get();
        return graphData?.nodes.find(node => node.id === nodeId);
      },
      
      getEdgeById: (edgeId) => {
        const { graphData } = get();
        return graphData?.edges.find(edge => edge.id === edgeId);
      },
      
      getFilteredData: () => {
        const { graphData, filter } = get();
        if (!graphData) return { nodes: [], edges: [] };
        
        // 过滤节点
        let filteredNodes = graphData.nodes;
        if (filter.entityTypes.length > 0) {
          filteredNodes = filteredNodes.filter(node => 
            filter.entityTypes.includes(node.type)
          );
        }
        
        // 过滤边
        let filteredEdges = graphData.edges.filter(edge => 
          edge.weight >= filter.minWeight && edge.weight <= filter.maxWeight
        );
        
        // 只保留连接到过滤后节点的边
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        filteredEdges = filteredEdges.filter(edge => 
          nodeIds.has(edge.source) && nodeIds.has(edge.target)
        );
        
        return {
          nodes: filteredNodes,
          edges: filteredEdges,
        };
      },
    }),
    {
      name: 'graph-store',
      partialize: (state) => ({
        // 只持久化这些字段
        filter: state.filter,
        viewport: state.viewport,
      }),
    }
  )
);
