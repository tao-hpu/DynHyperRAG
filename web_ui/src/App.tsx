import { useState, useEffect, useMemo } from 'react'
import GraphCanvas from './components/GraphCanvas'
import SearchBar from './components/SearchBar'
import FilterPanel from './components/FilterPanel'
import type { GraphData, Node, Edge, GraphFilter } from './types/graph'
import { graphService } from './services/graphService'
import './App.css'

function App() {
  const [rawGraphData, setRawGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);
  const [loadingNode, setLoadingNode] = useState(false);

  const [filter, setFilter] = useState<GraphFilter>({
    entityTypes: [],
    minWeight: 0,
    maxWeight: 20  // 调整为 20 以适应实际数据范围（8-18）
  });

  // 加载图数据
  useEffect(() => {
    const loadGraphData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 获取节点和边数据
        const [nodes, edges] = await Promise.all([
          graphService.getNodes({ limit: 500 }),  // 增加到 500 以确保加载所有节点
          graphService.getEdges({ limit: 500 })   // 增加到 500 以确保加载所有边
        ]);

        setRawGraphData({
          nodes,
          edges
        });
      } catch (err) {
        console.error('Failed to load graph data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load graph data');
      } finally {
        setLoading(false);
      }
    };

    loadGraphData();
  }, []);

  // 应用过滤器
  const filteredGraphData = useMemo(() => {
    if (!rawGraphData) return null;

    let filteredNodes = rawGraphData.nodes;
    let filteredEdges = rawGraphData.edges;

    // 过滤节点类型
    if (filter.entityTypes.length > 0) {
      filteredNodes = filteredNodes.filter(node =>
        filter.entityTypes.includes(node.type)
      );
      const nodeIds = new Set(filteredNodes.map(n => n.id));
      filteredEdges = filteredEdges.filter(edge =>
        nodeIds.has(edge.source) && nodeIds.has(edge.target)
      );
    }

    // 过滤边权重
    filteredEdges = filteredEdges.filter(edge =>
      edge.weight >= filter.minWeight && edge.weight <= filter.maxWeight
    );

    // 移除孤立节点
    const connectedNodeIds = new Set<string>();
    filteredEdges.forEach(edge => {
      connectedNodeIds.add(edge.source);
      connectedNodeIds.add(edge.target);
    });
    filteredNodes = filteredNodes.filter(node => connectedNodeIds.has(node.id));

    return {
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [rawGraphData, filter]);

  // 获取可用的实体类型
  const availableTypes = useMemo(() => {
    if (!rawGraphData) return [];
    const types = new Set(rawGraphData.nodes.map(n => n.type));
    return Array.from(types).sort();
  }, [rawGraphData]);

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
    console.log('Node clicked:', node);
  };

  const handleEdgeClick = (edge: Edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    console.log('Edge clicked:', edge);
  };

  const handleNodeDoubleClick = async (nodeId: string) => {
    console.log('Node double-clicked:', nodeId);

    try {
      // 获取子图（邻居节点）
      const subgraph = await graphService.getSubgraph({ centerNodeId: nodeId, depth: 1 });

      if (rawGraphData) {
        // 合并新节点和边到现有图数据
        const existingNodeIds = new Set(rawGraphData.nodes.map(n => n.id));
        const existingEdgeIds = new Set(rawGraphData.edges.map(e => e.id));

        const newNodes = subgraph.nodes.filter(n => !existingNodeIds.has(n.id));
        const newEdges = subgraph.edges.filter(e => !existingEdgeIds.has(e.id));

        if (newNodes.length > 0 || newEdges.length > 0) {
          setRawGraphData({
            nodes: [...rawGraphData.nodes, ...newNodes],
            edges: [...rawGraphData.edges, ...newEdges]
          });
        }
      }
    } catch (err) {
      console.error('Failed to expand node:', err);
    }
  };

  const handleNodeSearch = async (nodeId: string) => {
    console.log('Node searched:', nodeId);

    // 检查节点是否已经在图中
    if (rawGraphData) {
      const nodeExists = rawGraphData.nodes.some(n => n.id === nodeId);

      if (nodeExists) {
        // 节点已存在，直接聚焦
        setFocusNodeId(nodeId);
      } else {
        // 节点不存在，动态加载
        try {
          setLoadingNode(true);
          const subgraph = await graphService.getSubgraph({ centerNodeId: nodeId, depth: 1 });

          // 合并新节点和边到现有图数据
          const existingNodeIds = new Set(rawGraphData.nodes.map(n => n.id));
          const existingEdgeIds = new Set(rawGraphData.edges.map(e => e.id));

          const newNodes = subgraph.nodes.filter(n => !existingNodeIds.has(n.id));
          const newEdges = subgraph.edges.filter(e => !existingEdgeIds.has(e.id));

          setRawGraphData({
            nodes: [...rawGraphData.nodes, ...newNodes],
            edges: [...rawGraphData.edges, ...newEdges]
          });

          // 等待一帧后聚焦（确保节点已渲染）
          setTimeout(() => {
            setFocusNodeId(nodeId);
          }, 100);
        } catch (err) {
          console.error('Failed to load node:', err);
        } finally {
          setLoadingNode(false);
        }
      }
    }
  };

  return (
    <div className="flex h-screen bg-white">
      {/* 主画布区域 */}
      <div className="flex-1 p-4 bg-white">
        <div className="bg-white rounded-lg shadow-lg h-full">
          <div className="p-4 border-b space-y-3">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">HyperGraphRAG Visualization</h1>
              <p className="text-sm text-gray-600 mt-1">Interactive hypergraph visualization with Cytoscape.js</p>
            </div>
            <SearchBar onNodeSelect={handleNodeSearch} />
          </div>
          <div className="h-[calc(100%-140px)]">
            {loading && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading graph data...</p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-red-600">
                  <p className="font-semibold mb-2">Error loading graph</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            )}

            {!loading && !error && filteredGraphData && (
              <GraphCanvas
                data={filteredGraphData}
                onNodeClick={handleNodeClick}
                onEdgeClick={handleEdgeClick}
                onNodeDoubleClick={handleNodeDoubleClick}
                focusNodeId={focusNodeId}
              />
            )}
          </div>
        </div>
      </div>

      {/* 侧边栏 */}
      <div className="w-80 p-4 flex flex-col gap-4 h-screen">
        {/* 过滤面板 */}
        <div className="bg-white rounded-lg shadow-lg p-4 flex-shrink-0">
          <h2 className="text-lg font-semibold mb-4">Filters</h2>
          <FilterPanel
            onFilterChange={setFilter}
            availableTypes={availableTypes}
          />
        </div>

        {/* 详情面板 */}
        <div className="bg-white rounded-lg shadow-lg p-4 flex-1 flex flex-col min-h-0">
          <h2 className="text-lg font-semibold mb-4 flex-shrink-0">Details</h2>
          <div className="overflow-y-auto flex-1">
            {selectedNode && (
              <div className="space-y-3">
                <h3 className="font-medium text-blue-600">Selected Node</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">ID:</span> {selectedNode.id}
                  </div>
                  <div>
                    <span className="font-medium">Label:</span> {selectedNode.label}
                  </div>
                  <div>
                    <span className="font-medium">Type:</span>
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      {selectedNode.type}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Description:</span> {selectedNode.description}
                  </div>
                  <div>
                    <span className="font-medium">Weight:</span> {selectedNode.weight.toFixed(2)}
                  </div>
                  {selectedNode.relevanceScore && (
                    <div>
                      <span className="font-medium">Relevance:</span> {selectedNode.relevanceScore.toFixed(2)}
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedEdge && (
              <div className="space-y-3">
                <h3 className="font-medium text-orange-600">Selected Edge</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium">Type:</span>
                    <span className={`ml-2 px-2 py-1 rounded ${selectedEdge.isHyperedge ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'}`}>
                      {selectedEdge.isHyperedge ? `Hyperedge (${selectedEdge.entities.length} entities)` : 'Regular Edge'}
                    </span>
                  </div>
                  {selectedEdge.isHyperedge && (
                    <div className="p-3 bg-orange-50 rounded border border-orange-200">
                      <div className="text-xs font-medium text-orange-800 mb-2">
                        ⚡ This is a hyperedge connecting {selectedEdge.entities.length} entities:
                      </div>
                      <ul className="text-xs space-y-1 list-disc list-inside text-orange-700">
                        {selectedEdge.entities.map((entity, idx) => (
                          <li key={idx}>{entity.replace(/"/g, '')}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div>
                    <span className="font-medium">Description:</span>
                    <div className="mt-1 text-gray-700 italic">
                      "{selectedEdge.description.replace(/"/g, '').substring(0, 200)}..."
                    </div>
                  </div>
                  <div>
                    <span className="font-medium">Weight:</span> {selectedEdge.weight.toFixed(1)}
                  </div>
                  <div>
                    <span className="font-medium">Relation:</span> {selectedEdge.relation}
                  </div>
                </div>
              </div>
            )}

            {!selectedNode && !selectedEdge && (
              <div className="text-gray-500 text-sm">
                <p>Click on a node to view details.</p>
                <p className="mt-2">Double-click a node to expand neighbors.</p>

                <div className="mt-4 space-y-2">
                  <h3 className="font-medium text-gray-700">Legend:</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-0.5 bg-gray-400 opacity-50"></div>
                      <span className="text-xs">Direct connection</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-8 bg-orange-100 border-2 border-orange-400 border-dashed rounded"></div>
                      <span className="text-xs">Hyperedge region (3+ entities)</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-orange-50 rounded border border-orange-200">
                  <div className="text-xs font-medium text-orange-800 mb-1">
                    💡 Understanding Hyperedges
                  </div>
                  <div className="text-xs text-orange-700">
                    Orange dashed regions (convex hulls) represent hyperedges that connect 3 or more entities simultaneously.
                    Entities within the same region share a common relationship.
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <h3 className="font-medium text-gray-700">Controls:</h3>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Mouse wheel: Zoom in/out</li>
                    <li>Click + drag: Pan canvas</li>
                    <li>Click node/edge: View details</li>
                    <li>Double-click node: Expand neighbors</li>
                    <li>Drag node: Reposition</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
