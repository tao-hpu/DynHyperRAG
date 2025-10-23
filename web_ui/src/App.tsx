import { useState, useEffect, useMemo, useRef } from 'react'
import GraphCanvas, { type GraphCanvasRef } from './components/GraphCanvas'
import SearchBar from './components/SearchBar'
import FilterPanel from './components/FilterPanel'
import QueryPanel from './components/QueryPanel'
import PathAnimationControls from './components/PathAnimationControls'
import QueryModeControls from './components/QueryModeControls'
import ExportPanel, { type ExportFormat, type ExportOptions } from './components/ExportPanel'
import SettingsPanel from './components/SettingsPanel'
import type { GraphData, Node, Edge, GraphFilter } from './types/graph'
import type { QueryResponse, QueryMode } from './types/query'
import { graphService } from './services/graphService'
import { importFromJSON } from './utils/exportUtils'
import { useSettingsStore } from './stores/settingsStore'
import './App.css'

function App() {
  const graphCanvasRef = useRef<GraphCanvasRef>(null);
  const { settings } = useSettingsStore();
  const [rawGraphData, setRawGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'graph' | 'query'>('graph');
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [queryMode, setQueryMode] = useState<QueryMode>('hybrid');
  const [animationStep, setAnimationStep] = useState<number | null>(null);
  const [showLocalPath, setShowLocalPath] = useState(true);
  const [showGlobalPath, setShowGlobalPath] = useState(true);
  const [importedLayout, setImportedLayout] = useState<Record<string, { x: number; y: number }> | null>(null);
  const [layoutKey, setLayoutKey] = useState(0); // Key to force layout recalculation
  const [sidebarOpen, setSidebarOpen] = useState(false); // For mobile/tablet sidebar toggle
  const [bottomDrawerOpen, setBottomDrawerOpen] = useState(false); // For mobile bottom drawer

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
        }
      }
    }
  };

  const handleQueryExecuted = (response: QueryResponse) => {
    setQueryResponse(response);
    setAnimationStep(null); // Reset animation
    // 自动切换到图视图以显示查询路径
    setCurrentView('graph');
  };

  const handleAnimationStep = (step: number, nodeId: string) => {
    setAnimationStep(step);
    setFocusNodeId(nodeId);
  };

  const handleModeFilterChange = (showLocal: boolean, showGlobal: boolean) => {
    setShowLocalPath(showLocal);
    setShowGlobalPath(showGlobal);
  };

  const handleExport = (format: ExportFormat, options?: ExportOptions) => {
    if (!graphCanvasRef.current) {
      console.error('Graph canvas ref not available');
      return;
    }

    try {
      switch (format) {
        case 'png':
          graphCanvasRef.current.exportPNG(options);
          break;
        case 'svg':
          graphCanvasRef.current.exportSVG(options);
          break;
        case 'json':
          graphCanvasRef.current.exportJSON(options);
          break;
      }
    } catch (err) {
      console.error('Export failed:', err);
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const handleImport = (jsonString: string) => {
    try {
      const imported = importFromJSON(jsonString);

      if (!imported) {
        throw new Error('Invalid JSON format');
      }

      // 更新图数据
      setRawGraphData(imported.graphData);

      // 保存布局信息（如果有）
      if (imported.layout) {
        setImportedLayout(imported.layout);
      }

      // 切换到图视图
      setCurrentView('graph');

      console.log('Graph imported successfully');
    } catch (err) {
      console.error('Import failed:', err);
      setError(err instanceof Error ? err.message : 'Import failed');
    }
  };

  const handleSettingsApply = () => {
    // Force layout recalculation by incrementing key
    setLayoutKey(prev => prev + 1);
  };

  return (
    <div className="h-screen bg-white overflow-hidden">
      {/* 主画布区域 - 为固定的 sidebar 留出右侧空间 */}
      <div className="h-full flex flex-col min-h-0 p-0 sm:p-2 lg:p-1 bg-white lg:pr-[322px]">
        <div className="bg-white rounded-none sm:rounded-lg shadow-none sm:shadow-lg h-full flex flex-col">
          <div className="p-2 sm:p-3 lg:p-3 border-b space-y-2 sm:space-y-3 flex-shrink-0">
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-800 truncate">HyperGraphRAG Visualization</h1>
                <p className="text-xs sm:text-sm text-gray-600 mt-1 hidden sm:block">Interactive hypergraph visualization with Cytoscape.js</p>
              </div>
              {/* Mobile Menu Button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
                aria-label="Toggle sidebar"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              {/* View Toggle */}
              <div className="hidden sm:flex gap-2">
                <button
                  onClick={() => setCurrentView('graph')}
                  className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${currentView === 'graph'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  <div className="flex items-center gap-1 sm:gap-2">
                    <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                    <span className="hidden md:inline">Graph View</span>
                    <span className="md:hidden">Graph</span>
                  </div>
                </button>
                <button
                  onClick={() => setCurrentView('query')}
                  className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${currentView === 'query'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                >
                  <div className="flex items-center gap-1 sm:gap-2">
                    <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Query
                  </div>
                </button>
              </div>
            </div>
            {/* Mobile View Toggle */}
            <div className="flex sm:hidden gap-2">
              <button
                onClick={() => setCurrentView('graph')}
                className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${currentView === 'graph'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
                  }`}
              >
                <div className="flex items-center justify-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  Graph
                </div>
              </button>
              <button
                onClick={() => setCurrentView('query')}
                className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${currentView === 'query'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700'
                  }`}
              >
                <div className="flex items-center justify-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Query
                </div>
              </button>
            </div>
            {currentView === 'graph' && <SearchBar onNodeSelect={handleNodeSearch} />}
          </div>

          <div className="flex-1 min-h-0">
            {/* Graph View */}
            {currentView === 'graph' && (
              <div className="h-full">
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
                    key={layoutKey}
                    ref={graphCanvasRef}
                    data={filteredGraphData}
                    settings={settings}
                    onNodeClick={handleNodeClick}
                    onEdgeClick={handleEdgeClick}
                    onNodeDoubleClick={handleNodeDoubleClick}
                    focusNodeId={focusNodeId}
                    queryPath={queryResponse?.queryPath || null}
                    animationStep={animationStep}
                    showLocalPath={showLocalPath}
                    showGlobalPath={showGlobalPath}
                    queryMode={queryMode}
                    importedLayout={importedLayout}
                  />
                )}
              </div>
            )}

            {/* Query View */}
            {currentView === 'query' && (
              <div className="h-full">
                <QueryPanel
                  onQueryExecuted={handleQueryExecuted}
                  onModeChange={setQueryMode}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 侧边栏 - Fixed position on all screen sizes */}
      <div className={`
        fixed inset-y-0 right-0 z-50 w-80 bg-white shadow-xl
        flex flex-col gap-4 p-4 h-screen overflow-y-auto
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
      `}>
        {/* Close button for tablet */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden absolute top-4 right-4 p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors z-10"
          aria-label="Close sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex flex-col gap-4 pt-12 md:pt-4 lg:pt-0">
          {/* 设置面板 */}
          {currentView === 'graph' && !loading && !error && (
            <div className="flex-shrink-0">
              <SettingsPanel onApply={handleSettingsApply} />
            </div>
          )}

          {/* 导出面板 */}
          {currentView === 'graph' && !loading && !error && (
            <div className="flex-shrink-0">
              <ExportPanel
                onExport={handleExport}
                onImport={handleImport}
              />
            </div>
          )}

          {/* 过滤面板 */}
          <div className="bg-white rounded-lg shadow-lg p-4 flex-shrink-0">
            <h2 className="text-lg font-semibold mb-4">Filters</h2>
            <FilterPanel
              onFilterChange={setFilter}
              availableTypes={availableTypes}
            />
          </div>

          {/* 查询模式控制面板 */}
          {queryResponse && currentView === 'graph' && (
            <div className="flex-shrink-0">
              <QueryModeControls
                currentMode={queryMode}
                onModeFilterChange={handleModeFilterChange}
              />
            </div>
          )}

          {/* 路径动画控制面板 */}
          {queryResponse && currentView === 'graph' && (
            <div className="flex-shrink-0">
              <PathAnimationControls
                queryPath={queryResponse.queryPath}
                onAnimationStep={handleAnimationStep}
                onAnimationComplete={() => setAnimationStep(null)}
              />
            </div>
          )}

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

      {/* Overlay for mobile/tablet sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar overlay"
        />
      )}

      {/* Mobile Bottom Drawer */}
      <div className="lg:hidden md:hidden">
        {/* Bottom drawer toggle button */}
        <button
          onClick={() => setBottomDrawerOpen(!bottomDrawerOpen)}
          className="fixed bottom-4 right-4 z-30 p-3 rounded-full bg-blue-600 text-white shadow-lg hover:bg-blue-700 transition-colors"
          style={{ minWidth: '44px', minHeight: '44px' }}
          aria-label="Toggle details drawer"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={bottomDrawerOpen ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"} />
          </svg>
        </button>

        {/* Bottom drawer */}
        <div className={`
          fixed inset-x-0 bottom-0 z-40 bg-white rounded-t-2xl shadow-2xl
          transform transition-transform duration-300 ease-in-out
          ${bottomDrawerOpen ? 'translate-y-0' : 'translate-y-full'}
          max-h-[70vh] overflow-hidden flex flex-col
        `}>
          {/* Drawer handle */}
          <div className="flex justify-center py-2 border-b">
            <div className="w-12 h-1 bg-gray-300 rounded-full"></div>
          </div>

          {/* Drawer content */}
          <div className="overflow-y-auto flex-1 p-4 space-y-4">
            {/* 设置面板 */}
            {currentView === 'graph' && !loading && !error && (
              <div className="flex-shrink-0">
                <SettingsPanel onApply={handleSettingsApply} />
              </div>
            )}

            {/* 导出面板 */}
            {currentView === 'graph' && !loading && !error && (
              <div className="flex-shrink-0">
                <ExportPanel
                  onExport={handleExport}
                  onImport={handleImport}
                />
              </div>
            )}

            {/* 过滤面板 */}
            <div className="bg-white rounded-lg border shadow-sm p-4 flex-shrink-0">
              <h2 className="text-lg font-semibold mb-4">Filters</h2>
              <FilterPanel
                onFilterChange={setFilter}
                availableTypes={availableTypes}
              />
            </div>

            {/* 查询模式控制面板 */}
            {queryResponse && currentView === 'graph' && (
              <div className="flex-shrink-0">
                <QueryModeControls
                  currentMode={queryMode}
                  onModeFilterChange={handleModeFilterChange}
                />
              </div>
            )}

            {/* 路径动画控制面板 */}
            {queryResponse && currentView === 'graph' && (
              <div className="flex-shrink-0">
                <PathAnimationControls
                  queryPath={queryResponse.queryPath}
                  onAnimationStep={handleAnimationStep}
                  onAnimationComplete={() => setAnimationStep(null)}
                />
              </div>
            )}

            {/* 详情面板 */}
            <div className="bg-white rounded-lg border shadow-sm p-4 flex-shrink-0">
              <h2 className="text-lg font-semibold mb-4">Details</h2>
              <div className="space-y-3">
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
                    <p>Tap on a node or edge to view details.</p>
                    <p className="mt-2">Double-tap a node to expand neighbors.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Overlay for bottom drawer */}
        {bottomDrawerOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-30 z-30"
            onClick={() => setBottomDrawerOpen(false)}
          />
        )}
      </div>
    </div>
  )
}

export default App
