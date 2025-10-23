import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import cytoscape from 'cytoscape';
// @ts-ignore - cytoscape-cose-bilkent 没有类型定义
import coseBilkent from 'cytoscape-cose-bilkent';
import type { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import type { GraphData, Node, Edge } from '@/types/graph';
import type { QueryPath } from '@/types/query';
import type { VisualizationSettings } from '@/types/settings';
import { exportToPNG, exportToSVG, exportToJSON } from '@/utils/exportUtils';
import type { ExportOptions } from '@/components/ExportPanel';

// 注册 cose-bilkent 布局插件
cytoscape.use(coseBilkent);

interface GraphCanvasProps {
  data: GraphData;
  settings?: VisualizationSettings; // Visualization settings
  onNodeClick?: (node: Node) => void;
  onEdgeClick?: (edge: Edge) => void;
  onNodeDoubleClick?: (nodeId: string) => void;
  focusNodeId?: string | null;
  queryPath?: QueryPath | null;
  animationStep?: number | null; // Current animation step (null = show all)
  showLocalPath?: boolean; // Show local retrieval path (for hybrid mode)
  showGlobalPath?: boolean; // Show global retrieval path (for hybrid mode)
  queryMode?: string; // Current query mode
  importedLayout?: Record<string, { x: number; y: number }> | null; // Imported layout positions
}

// 导出的方法接口
export interface GraphCanvasRef {
  exportPNG: (options?: ExportOptions) => void;
  exportSVG: (options?: ExportOptions) => void;
  exportJSON: (options?: ExportOptions) => void;
  getCytoscapeInstance: () => Core | null;
}

const GraphCanvas = forwardRef<GraphCanvasRef, GraphCanvasProps>(({ data, settings, onNodeClick, onEdgeClick, onNodeDoubleClick, focusNodeId, queryPath, animationStep, showLocalPath = true, showGlobalPath = true, queryMode, importedLayout }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  // 暴露导出方法给父组件
  useImperativeHandle(ref, () => ({
    exportPNG: (options?: ExportOptions) => {
      if (cyRef.current) {
        exportToPNG(cyRef.current, options);
      }
    },
    exportSVG: (options?: ExportOptions) => {
      if (cyRef.current) {
        exportToSVG(cyRef.current, options);
      }
    },
    exportJSON: (options?: ExportOptions) => {
      if (cyRef.current) {
        exportToJSON(cyRef.current, data, options);
      }
    },
    getCytoscapeInstance: () => cyRef.current,
  }));

  // 计算凸包（Convex Hull）- Graham Scan 算法
  const computeConvexHull = (points: { x: number; y: number }[]) => {
    if (points.length < 3) return points;

    // 找到最下方的点（y 最小，如果相同则 x 最小）
    let lowest = 0;
    for (let i = 1; i < points.length; i++) {
      if (points[i].y < points[lowest].y ||
        (points[i].y === points[lowest].y && points[i].x < points[lowest].x)) {
        lowest = i;
      }
    }
    [points[0], points[lowest]] = [points[lowest], points[0]];

    const pivot = points[0];

    // 按极角排序
    const sorted = points.slice(1).sort((a, b) => {
      const angleA = Math.atan2(a.y - pivot.y, a.x - pivot.x);
      const angleB = Math.atan2(b.y - pivot.y, b.x - pivot.x);
      if (angleA !== angleB) return angleA - angleB;
      // 如果角度相同，距离近的在前
      const distA = Math.hypot(a.x - pivot.x, a.y - pivot.y);
      const distB = Math.hypot(b.x - pivot.x, b.y - pivot.y);
      return distA - distB;
    });

    const hull = [pivot, sorted[0]];

    for (let i = 1; i < sorted.length; i++) {
      while (hull.length > 1) {
        const p1 = hull[hull.length - 2];
        const p2 = hull[hull.length - 1];
        const p3 = sorted[i];
        // 计算叉积判断转向
        const cross = (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x);
        if (cross > 0) break;
        hull.pop();
      }
      hull.push(sorted[i]);
    }

    return hull;
  };

  // 初始化 Cytoscape 实例
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,

      // 基础样式配置
      style: [
        // 节点样式
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#1f2937',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'font-weight': 500,
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': 2,
            'border-color': '#1e40af',
            'text-outline-width': 2,
            'text-outline-color': '#ffffff',
          }
        },
        // 根据实体类型设置不同颜色
        {
          selector: 'node[type="person"]',
          style: {
            'background-color': '#10b981',
            'border-color': '#059669',
          }
        },
        {
          selector: 'node[type="organization"]',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#d97706',
          }
        },
        {
          selector: 'node[type="location"]',
          style: {
            'background-color': '#8b5cf6',
            'border-color': '#7c3aed',
          }
        },
        {
          selector: 'node[type="event"]',
          style: {
            'background-color': '#ec4899',
            'border-color': '#db2777',
          }
        },
        {
          selector: 'node[type="concept"]',
          style: {
            'background-color': '#06b6d4',
            'border-color': '#0891b2',
          }
        },
        // 选中状态
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#ef4444',
            'background-color': '#fca5a5',
          }
        },
        // 普通边样式
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#9ca3af',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.5,
          }
        },
        // 超边不显示为边，只通过凸包显示
        {
          selector: 'edge[?isHyperedge]',
          style: {
            'width': 0,           // 隐藏超边的线
            'opacity': 0,         // 完全透明
            'display': 'none',    // 不显示
          }
        },
        // 边选中状态
        {
          selector: 'edge:selected',
          style: {
            'width': 4,
            'line-color': '#ef4444',
            'target-arrow-color': '#ef4444',
            'opacity': 1,
          }
        },
        // 悬停状态
        {
          selector: 'node:active',
          style: {
            'overlay-opacity': 0.2,
            'overlay-color': '#3b82f6',
          }
        },
        {
          selector: 'edge:active',
          style: {
            'overlay-opacity': 0.2,
            'overlay-color': '#f59e0b',
          }
        },
        // 查询路径高亮样式 - 低相关性节点
        {
          selector: 'node.query-path-low',
          style: {
            'background-color': '#fef3c7',
            'border-color': '#fbbf24',
            'border-width': 3,
            'opacity': 0.7,
            'z-index': 998,
          }
        },
        // 查询路径高亮样式 - 中等相关性节点
        {
          selector: 'node.query-path-medium',
          style: {
            'background-color': '#fbbf24',
            'border-color': '#f59e0b',
            'border-width': 4,
            'opacity': 0.85,
            'z-index': 999,
          }
        },
        // 查询路径高亮样式 - 高相关性节点
        {
          selector: 'node.query-path-high',
          style: {
            'background-color': '#f59e0b',
            'border-color': '#ea580c',
            'border-width': 5,
            'opacity': 1,
            'z-index': 1000,
          }
        },
        // Local 查询模式节点 (蓝色系)
        {
          selector: 'node.query-mode-local',
          style: {
            'background-color': '#60a5fa',
            'border-color': '#3b82f6',
            'border-width': 4,
            'z-index': 999,
          }
        },
        // Global 查询模式节点 (紫色系)
        {
          selector: 'node.query-mode-global',
          style: {
            'background-color': '#a78bfa',
            'border-color': '#8b5cf6',
            'border-width': 4,
            'z-index': 999,
          }
        },
        // Both 查询模式节点 (绿色系 - 表示两种模式都检索到)
        {
          selector: 'node.query-mode-both',
          style: {
            'background-color': '#34d399',
            'border-color': '#10b981',
            'border-width': 5,
            'z-index': 1000,
          }
        },
        // 查询路径边高亮
        {
          selector: 'edge.query-path',
          style: {
            'width': 4,
            'line-color': '#fbbf24',
            'target-arrow-color': '#fbbf24',
            'opacity': 0.9,
            'z-index': 999,
          }
        },
        // 查询路径边高亮 - 高权重
        {
          selector: 'edge.query-path-high',
          style: {
            'width': 5,
            'line-color': '#f59e0b',
            'target-arrow-color': '#f59e0b',
            'opacity': 1,
            'z-index': 1000,
          }
        },
      ],

      // 初始布局（后续会应用力导向布局）
      layout: {
        name: 'preset',
      },

      // 交互配置
      minZoom: 0.1,
      maxZoom: 10,
      wheelSensitivity: 0.2,

      // 移动端手势支持
      touchTapThreshold: 8,
      desktopTapThreshold: 4,

      // 性能优化
      hideEdgesOnViewport: true,
      textureOnViewport: true,
      motionBlur: true,
      pixelRatio: 'auto',
    });

    cyRef.current = cy;

    // 创建凸包渲染的 Canvas overlay
    const container = containerRef.current;
    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.style.position = 'absolute';
    overlayCanvas.style.top = '0';
    overlayCanvas.style.left = '0';
    overlayCanvas.style.pointerEvents = 'none'; // 不阻挡鼠标事件
    overlayCanvas.style.zIndex = '0'; // 放在最底层，节点在上面
    overlayCanvas.id = 'hyperedge-underlay';
    container.style.position = 'relative'; // 确保容器是相对定位

    // 将 canvas 插入到容器的第一个位置（最底层）
    container.insertBefore(overlayCanvas, container.firstChild);

    // console.log('Underlay canvas created (below nodes):', overlayCanvas);

    // 调整 overlay canvas 大小
    const resizeOverlay = () => {
      const rect = container.getBoundingClientRect();
      overlayCanvas.width = rect.width;
      overlayCanvas.height = rect.height;
      overlayCanvas.style.width = `${rect.width}px`;
      overlayCanvas.style.height = `${rect.height}px`;
    };
    resizeOverlay();

    // 自定义超边凸包渲染
    const renderHyperedgeHulls = () => {
      const ctx = overlayCanvas.getContext('2d');
      if (!ctx) return;

      // 清空画布
      ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

      // 获取所有超边
      const hyperedges = cy.edges('[?isHyperedge]');

      // console.log(`Rendering ${hyperedges.length} hyperedge hulls`);

      let drawnCount = 0;
      hyperedges.forEach((edge) => {
        const entities = edge.data('entities') || [];
        if (entities.length < 3) {
          // console.log(`Hyperedge ${idx}: skipped (only ${entities.length} entities)`);
          return;
        }

        // 获取所有相关节点的位置
        const nodePositions: { x: number; y: number }[] = [];
        const foundNodes: string[] = [];
        entities.forEach((entityId: unknown) => {
          // 不要去掉引号！节点 ID 本身就包含引号
          const nodeId = String(entityId);
          const node = cy.getElementById(nodeId);
          if (node.length > 0) {
            foundNodes.push(nodeId);
            const pos = node.renderedPosition();
            const nodeRadius = node.width() / 2;
            // 在节点周围添加均匀的 padding 点
            const padding = nodeRadius + 20;
            for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 4) {
              nodePositions.push({
                x: pos.x + Math.cos(angle) * padding,
                y: pos.y + Math.sin(angle) * padding
              });
            }
          }
        });

        if (nodePositions.length < 3) {
          // console.log(`Hyperedge ${idx}: skipped (found ${foundNodes.length}/${entities.length} nodes)`);
          return;
        }

        // 计算凸包
        const hull = computeConvexHull([...nodePositions]);

        if (hull.length < 3) {
          // console.log(`Hyperedge ${idx}: hull too small (${hull.length} points)`);
          return;
        }

        drawnCount++;

        // 绘制凸包区域
        ctx.save();

        ctx.beginPath();
        ctx.moveTo(hull[0].x, hull[0].y);
        for (let i = 1; i < hull.length; i++) {
          ctx.lineTo(hull[i].x, hull[i].y);
        }
        ctx.closePath();

        // 填充半透明橙色背景（在节点下面，所以可以更明显）
        ctx.fillStyle = 'rgba(251, 146, 60, 0.15)';
        ctx.fill();

        // 绘制虚线边框
        ctx.strokeStyle = 'rgba(249, 115, 22, 0.7)';
        ctx.lineWidth = 3;
        ctx.setLineDash([10, 5]);
        ctx.stroke();

        ctx.restore();
      });

      // console.log(`Actually drew ${drawnCount} hulls`);
    };

    // 在每次渲染后绘制凸包
    cy.on('render', renderHyperedgeHulls);
    cy.on('viewport', renderHyperedgeHulls);

    // 窗口大小变化时重新调整
    let resizeTimeout: ReturnType<typeof setTimeout> | null = null;
    const handleResize = () => {
      // 防抖处理，避免频繁触发
      if (resizeTimeout) {
        clearTimeout(resizeTimeout);
      }

      resizeTimeout = setTimeout(() => {
        resizeOverlay();

        // 调整 Cytoscape 画布大小
        if (cy && !cy.destroyed()) {
          cy.resize();

          // 平滑地重新适配视图
          cy.animate({
            fit: {
              eles: cy.elements(),
              padding: 50
            },
            duration: 300,
            easing: 'ease-in-out'
          });
        }
      }, 250); // 250ms 防抖延迟
    };

    window.addEventListener('resize', handleResize);

    // 清理函数
    return () => {
      window.removeEventListener('resize', handleResize);
      if (resizeTimeout) {
        clearTimeout(resizeTimeout);
      }
      if (cyRef.current) {
        cyRef.current.off('render', renderHyperedgeHulls);
        cyRef.current.off('viewport', renderHyperedgeHulls);
        cyRef.current.destroy();
        cyRef.current = null;
      }
      if (overlayCanvas && overlayCanvas.parentNode) {
        overlayCanvas.parentNode.removeChild(overlayCanvas);
      }
    };
  }, []); // 只在组件挂载时初始化一次

  // 应用设置到 Cytoscape 样式（实时更新）
  useEffect(() => {
    if (!cyRef.current || !settings) return;

    const cy = cyRef.current;
    if (cy.destroyed()) return;

    // 更新节点样式
    cy.style()
      .selector('node')
      .style({
        'font-size': `${settings.node.fontSize}px`,
        'font-weight': settings.node.fontWeight,
      })
      .selector('node[type="person"]')
      .style({
        'background-color': settings.colorScheme.person,
      })
      .selector('node[type="organization"]')
      .style({
        'background-color': settings.colorScheme.organization,
      })
      .selector('node[type="location"]')
      .style({
        'background-color': settings.colorScheme.location,
      })
      .selector('node[type="event"]')
      .style({
        'background-color': settings.colorScheme.event,
      })
      .selector('node[type="concept"]')
      .style({
        'background-color': settings.colorScheme.concept,
      })
      .selector('node:not([type])')
      .style({
        'background-color': settings.colorScheme.default,
      })
      .selector('edge')
      .style({
        'line-color': settings.colorScheme.edge,
        'target-arrow-color': settings.colorScheme.edge,
      })
      .selector('edge.query-path-low')
      .style({
        'background-color': settings.colorScheme.queryPathLow,
      })
      .selector('edge.query-path-medium')
      .style({
        'background-color': settings.colorScheme.queryPathMedium,
      })
      .selector('edge.query-path-high')
      .style({
        'background-color': settings.colorScheme.queryPathHigh,
      })
      .update();

    // 更新节点大小（基于权重和设置）
    cy.nodes().forEach(node => {
      const weight = node.data('weight') || 1;
      const minSize = settings.node.minSize;
      const maxSize = settings.node.maxSize;
      const size = Math.max(minSize, Math.min(maxSize, minSize + weight * (maxSize - minSize) / 20));
      node.style('width', size);
      node.style('height', size);
    });
  }, [settings]);

  // 转换数据并渲染图
  useEffect(() => {
    if (!cyRef.current || !data) return;

    const cy = cyRef.current;

    // 检查实例是否已销毁
    if (cy.destroyed()) return;

    // 计算节点大小（使用设置或默认值）
    const minSize = settings?.node.minSize || 20;
    const maxSize = settings?.node.maxSize || 60;

    // 转换节点数据为 Cytoscape 格式
    const cytoscapeNodes = data.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label || node.id,
        type: node.type,
        description: node.description,
        weight: node.weight,
        relevanceScore: node.relevanceScore,
        // 根据权重设置节点大小
        size: Math.max(minSize, Math.min(maxSize, minSize + node.weight * (maxSize - minSize) / 20)),
      }
    }));

    // 转换边数据为 Cytoscape 格式
    const cytoscapeEdges = data.edges.map(edge => {
      const isHyper = edge.isHyperedge === true || edge.entities.length >= 3;
      return {
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          relation: edge.relation,
          description: edge.description,
          weight: edge.weight,
          entities: edge.entities,
          isHyperedge: isHyper,
        }
      };
    });

    // 调试：打印边的统计信息（已注释）
    // const hyperCount = cytoscapeEdges.filter(e => e.data.isHyperedge).length;
    // const regularCount = cytoscapeEdges.length - hyperCount;
    // console.log(`Graph edges: ${cytoscapeEdges.length} total (${hyperCount} hyperedges, ${regularCount} regular)`);

    // 批量更新图数据
    cy.batch(() => {
      cy.elements().remove();
      cy.add([...cytoscapeNodes, ...cytoscapeEdges]);
    });

    // 如果有导入的布局，应用它；否则使用力导向布局
    if (importedLayout) {
      // 应用导入的布局位置
      cy.batch(() => {
        cy.nodes().forEach((node) => {
          const pos = importedLayout[node.id()];
          if (pos) {
            node.position(pos);
          }
        });
      });

      // 适配视图以显示所有节点
      cy.fit(undefined, 50);
    } else {
      // 应用 cose-bilkent 高质量力导向布局（使用设置或默认值）
      const layoutSettings = settings?.layout || {
        idealEdgeLength: 120,
        nodeRepulsion: 6000,
        gravity: 0.5,
        numIter: 2500,
      };

      const layout = cy.layout({
        name: 'cose-bilkent',
        // @ts-ignore - cose-bilkent 特定选项
        animate: 'end',
        animationDuration: 1000,
        // 布局参数优化
        idealEdgeLength: layoutSettings.idealEdgeLength,
        nodeRepulsion: layoutSettings.nodeRepulsion,
        gravity: layoutSettings.gravity,
        numIter: layoutSettings.numIter,
        tile: true,
        randomize: true,
        tilingPaddingVertical: 10,
        tilingPaddingHorizontal: 10,
      });

      layout.run();

      // 清理函数：停止布局动画
      return () => {
        if (layout && typeof layout.stop === 'function') {
          layout.stop();
        }
      };
    }
  }, [data, importedLayout, settings]);

  // 设置事件监听器
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;

    // 创建 tooltip 元素
    const tooltip = document.createElement('div');
    tooltip.style.position = 'absolute';
    tooltip.style.display = 'none';
    tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '8px 12px';
    tooltip.style.borderRadius = '6px';
    tooltip.style.fontSize = '12px';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.zIndex = '1000';
    tooltip.style.maxWidth = '300px';
    tooltip.style.wordWrap = 'break-word';
    document.body.appendChild(tooltip);

    // 节点点击事件
    const handleNodeTap = (evt: cytoscape.EventObject) => {
      const node: NodeSingular = evt.target;
      const nodeData = node.data();

      if (onNodeClick) {
        onNodeClick({
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          description: nodeData.description,
          weight: nodeData.weight,
          relevanceScore: nodeData.relevanceScore,
        });
      }
    };

    // 节点双击事件
    const handleNodeDoubleTap = (evt: cytoscape.EventObject) => {
      const node: NodeSingular = evt.target;
      const nodeId = node.data('id');

      if (onNodeDoubleClick) {
        onNodeDoubleClick(nodeId);
      }
    };

    // 边点击事件
    const handleEdgeTap = (evt: cytoscape.EventObject) => {
      const edge: EdgeSingular = evt.target;
      const edgeData = edge.data();

      if (onEdgeClick) {
        onEdgeClick({
          id: edgeData.id,
          source: edgeData.source,
          target: edgeData.target,
          relation: edgeData.relation,
          description: edgeData.description,
          weight: edgeData.weight,
          entities: edgeData.entities || [edgeData.source, edgeData.target],
          isHyperedge: edgeData.isHyperedge,
        });
      }
    };

    // 节点悬停事件
    const handleNodeMouseover = (evt: cytoscape.EventObject) => {
      const node: NodeSingular = evt.target;
      const nodeData = node.data();

      tooltip.innerHTML = `
        <div><strong>${nodeData.label}</strong></div>
        <div style="margin-top: 4px; font-size: 11px; opacity: 0.9;">
          Type: ${nodeData.type}<br/>
          Weight: ${nodeData.weight?.toFixed(2) || 'N/A'}
        </div>
      `;
      tooltip.style.display = 'block';
    };

    const handleNodeMouseout = () => {
      tooltip.style.display = 'none';
    };

    const handleNodeMousemove = (evt: cytoscape.EventObject) => {
      const event = evt.originalEvent as MouseEvent;
      tooltip.style.left = `${event.pageX + 10}px`;
      tooltip.style.top = `${event.pageY + 10}px`;
    };

    // 边悬停事件
    const handleEdgeMouseover = (evt: cytoscape.EventObject) => {
      const edge: EdgeSingular = evt.target;
      const edgeData = edge.data();

      const entities = edgeData.entities || [];
      const isHyperedge = entities.length >= 3;

      tooltip.innerHTML = `
        <div style="margin-bottom: 6px;">
          ${isHyperedge
          ? `<span style="color: #fbbf24; font-weight: bold;">⚡ Hyperedge (${entities.length} entities)</span>`
          : '<span style="color: #9ca3af;">Regular edge</span>'}
        </div>
        <div style="font-size: 11px; opacity: 0.9; max-width: 250px;">
          ${(edgeData.description || 'No description').substring(0, 150)}${edgeData.description?.length > 150 ? '...' : ''}
        </div>
        ${isHyperedge ? `
          <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(251, 191, 36, 0.3);">
            <div style="font-size: 10px; color: #fbbf24;">Connected entities:</div>
            <div style="font-size: 10px; opacity: 0.8; margin-top: 2px;">
              ${entities.slice(0, 3).map((e: unknown) => String(e).replace(/"/g, '')).join(', ')}${entities.length > 3 ? '...' : ''}
            </div>
          </div>
        ` : ''}
      `;
      tooltip.style.display = 'block';
    };

    const handleEdgeMouseout = () => {
      tooltip.style.display = 'none';
    };

    const handleEdgeMousemove = (evt: cytoscape.EventObject) => {
      const event = evt.originalEvent as MouseEvent;
      tooltip.style.left = `${event.pageX + 10}px`;
      tooltip.style.top = `${event.pageY + 10}px`;
    };

    // 点击背景取消选择
    const handleBackgroundTap = (evt: cytoscape.EventObject) => {
      // 只有点击背景时才触发（不是节点或边）
      if (evt.target === cy) {
        // 取消所有选择
        cy.elements().unselect();
        // 清空选择状态（通过传递 null）
        if (onNodeClick) {
          onNodeClick(null as any);
        }
        if (onEdgeClick) {
          onEdgeClick(null as any);
        }
      }
    };

    cy.on('tap', handleBackgroundTap);
    cy.on('tap', 'node', handleNodeTap);
    cy.on('dbltap', 'node', handleNodeDoubleTap);
    cy.on('tap', 'edge', handleEdgeTap);
    cy.on('mouseover', 'node', handleNodeMouseover);
    cy.on('mouseout', 'node', handleNodeMouseout);
    cy.on('mousemove', 'node', handleNodeMousemove);
    cy.on('mouseover', 'edge', handleEdgeMouseover);
    cy.on('mouseout', 'edge', handleEdgeMouseout);
    cy.on('mousemove', 'edge', handleEdgeMousemove);

    // 移动端手势支持
    let touchStartDistance = 0;
    let touchStartZoom = 1;
    let longPressTimer: ReturnType<typeof setTimeout> | null = null;
    let longPressTarget: NodeSingular | null = null;

    // 双指缩放 (Pinch Zoom)
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        // 双指触摸开始
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        touchStartDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        touchStartZoom = cy.zoom();
        e.preventDefault();
      } else if (e.touches.length === 1) {
        // 单指触摸 - 检测长按
        const touch = e.touches[0];
        const rect = cy.container()!.getBoundingClientRect();
        const renderedPosition = {
          x: touch.clientX - rect.left,
          y: touch.clientY - rect.top
        };

        // 使用 Cytoscape 的 API 查找触摸位置的元素
        const target = cy.elements().filter((ele) => {
          if (!ele.isNode()) return false;
          const bb = ele.renderedBoundingBox();
          return (
            renderedPosition.x >= bb.x1 &&
            renderedPosition.x <= bb.x2 &&
            renderedPosition.y >= bb.y1 &&
            renderedPosition.y <= bb.y2
          );
        }).first();

        if (target && target.isNode()) {
          longPressTarget = target as NodeSingular;
          longPressTimer = setTimeout(() => {
            // 长按触发 - 显示上下文菜单或详情
            if (longPressTarget) {
              // 触发震动反馈（如果支持）
              if (navigator.vibrate) {
                navigator.vibrate(50);
              }
              // 选中节点并显示详情
              cy.elements().unselect();
              longPressTarget.select();
              if (onNodeClick) {
                const nodeData = longPressTarget.data();
                onNodeClick({
                  id: nodeData.id,
                  label: nodeData.label,
                  type: nodeData.type,
                  description: nodeData.description,
                  weight: nodeData.weight,
                  relevanceScore: nodeData.relevanceScore,
                });
              }
            }
          }, 500); // 500ms 长按阈值
        }
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        // 双指缩放
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );

        if (touchStartDistance > 0) {
          const scale = currentDistance / touchStartDistance;
          const newZoom = touchStartZoom * scale;

          // 限制缩放范围
          const clampedZoom = Math.max(0.1, Math.min(10, newZoom));

          // 计算缩放中心点（两指中点）
          const centerX = (touch1.clientX + touch2.clientX) / 2;
          const centerY = (touch1.clientY + touch2.clientY) / 2;
          const rect = cy.container()!.getBoundingClientRect();
          const renderedPosition = {
            x: centerX - rect.left,
            y: centerY - rect.top
          };

          cy.zoom({
            level: clampedZoom,
            renderedPosition: renderedPosition
          });
        }
        e.preventDefault();
      }

      // 取消长按
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
        longPressTarget = null;
      }
    };

    const handleTouchEnd = () => {
      touchStartDistance = 0;
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
        longPressTarget = null;
      }
    };

    // 添加触摸事件监听
    const container = cy.container();
    if (container) {
      container.addEventListener('touchstart', handleTouchStart, { passive: false });
      container.addEventListener('touchmove', handleTouchMove, { passive: false });
      container.addEventListener('touchend', handleTouchEnd);
      container.addEventListener('touchcancel', handleTouchEnd);
    }

    // 清理事件监听器
    return () => {
      if (cy && !cy.destroyed()) {
        cy.off('tap', 'node', handleNodeTap);
        cy.off('dbltap', 'node', handleNodeDoubleTap);
        cy.off('tap', 'edge', handleEdgeTap);
        cy.off('mouseover', 'node', handleNodeMouseover);
        cy.off('mouseout', 'node', handleNodeMouseout);
        cy.off('mousemove', 'node', handleNodeMousemove);
        cy.off('mouseover', 'edge', handleEdgeMouseover);
        cy.off('mouseout', 'edge', handleEdgeMouseout);
        cy.off('mousemove', 'edge', handleEdgeMousemove);
      }
      if (tooltip && tooltip.parentNode) {
        document.body.removeChild(tooltip);
      }
      // 清理触摸事件监听器
      if (container) {
        container.removeEventListener('touchstart', handleTouchStart);
        container.removeEventListener('touchmove', handleTouchMove);
        container.removeEventListener('touchend', handleTouchEnd);
        container.removeEventListener('touchcancel', handleTouchEnd);
      }
      // 清理长按定时器
      if (longPressTimer) {
        clearTimeout(longPressTimer);
      }
    };
  }, [onNodeClick, onEdgeClick, onNodeDoubleClick]);

  // 聚焦到特定节点
  useEffect(() => {
    if (!cyRef.current || !focusNodeId) return;

    const cy = cyRef.current;

    // 检查实例是否已销毁
    if (cy.destroyed()) return;

    const node = cy.getElementById(focusNodeId);

    if (node.length > 0) {
      // 取消之前的选择
      cy.elements().unselect();

      // 选中节点
      node.select();

      // 平滑移动到节点位置，使用合理的缩放级别
      const currentZoom = cy.zoom();
      const targetZoom = currentZoom < 0.8 ? 1.0 : currentZoom; // 如果太小就放大到 1.0，否则保持当前缩放

      cy.animate({
        center: {
          eles: node
        },
        zoom: targetZoom,
        duration: 400,
        easing: 'ease-in-out'
      });

      // 触发点击事件显示详情
      if (onNodeClick) {
        const nodeData = node.data();
        onNodeClick({
          id: nodeData.id,
          label: nodeData.label,
          type: nodeData.type,
          description: nodeData.description,
          weight: nodeData.weight,
          relevanceScore: nodeData.relevanceScore,
        });
      }
    }
  }, [focusNodeId]); // 移除 onNodeClick 依赖，避免无限循环

  // 高亮查询路径（支持动画）
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;

    // 检查实例是否已销毁
    if (cy.destroyed()) return;

    // 移除之前的高亮
    cy.elements().removeClass('query-path query-path-low query-path-medium query-path-high query-path-high query-mode-local query-mode-global query-mode-both');

    // 重置所有节点的样式
    cy.nodes().forEach(node => {
      const originalSize = node.data('size') || 30;
      node.style('width', originalSize);
      node.style('height', originalSize);
      node.style('opacity', 1);
    });

    if (!queryPath || !queryPath.nodes || queryPath.nodes.length === 0) {
      return;
    }

    // 确定要高亮的节点范围（用于动画）
    let nodesToHighlight = animationStep !== null && animationStep !== undefined
      ? queryPath.nodes.slice(0, animationStep + 1) // 动画模式：只显示到当前步骤
      : queryPath.nodes; // 非动画模式：显示所有节点

    // 在 hybrid 模式下，根据 showLocalPath 和 showGlobalPath 过滤节点
    if (queryMode === 'hybrid' && queryPath.nodeTypes) {
      nodesToHighlight = nodesToHighlight.filter(nodeId => {
        const nodeType = queryPath.nodeTypes![nodeId];
        if (!nodeType) return true; // 如果没有类型信息，默认显示

        if (nodeType === 'both') return true; // 两种模式都检索到的节点总是显示
        if (nodeType === 'local' && !showLocalPath) return false;
        if (nodeType === 'global' && !showGlobalPath) return false;

        return true;
      });
    }

    // 高亮路径中的节点，根据相关性得分和查询模式设置不同的样式
    nodesToHighlight.forEach((nodeId, index) => {
      const node = cy.getElementById(nodeId);
      if (node.length > 0) {
        const score = queryPath.scores[nodeId] || 0;
        const nodeType = queryPath.nodeTypes?.[nodeId];

        // 如果是 hybrid 模式且有 nodeTypes 信息，使用模式颜色
        if (queryMode === 'hybrid' && nodeType) {
          // 使用查询模式颜色
          if (nodeType === 'local') {
            node.addClass('query-mode-local');
          } else if (nodeType === 'global') {
            node.addClass('query-mode-global');
          } else if (nodeType === 'both') {
            node.addClass('query-mode-both');
          }
        } else {
          // 使用相关性得分颜色（非 hybrid 模式或没有 nodeTypes 信息）
          let highlightClass = 'query-path-low';

          if (score >= 0.7) {
            highlightClass = 'query-path-high';
          } else if (score >= 0.4) {
            highlightClass = 'query-path-medium';
          }

          node.addClass(highlightClass);
        }

        // 根据相关性得分动态调整节点大小
        let sizeMultiplier = 1.2;
        if (score >= 0.7) {
          sizeMultiplier = 1.5;
        } else if (score >= 0.4) {
          sizeMultiplier = 1.35;
        }

        const originalSize = node.data('size') || 30;
        const newSize = originalSize * sizeMultiplier;

        // 在动画模式下，当前步骤的节点使用脉冲效果
        if (animationStep !== null && animationStep !== undefined && index === animationStep) {
          node.animate({
            style: {
              'width': newSize * 1.2,
              'height': newSize * 1.2,
              'opacity': 1,
            }
          }, {
            duration: 300,
            easing: 'ease-out',
          });
        } else {
          node.style('width', newSize);
          node.style('height', newSize);

          // 根据得分设置透明度（0.6 到 1.0）
          const opacity = Math.max(0.6, Math.min(1.0, 0.5 + score * 0.5));
          node.style('opacity', opacity);
        }
      }
    });

    // 高亮路径中的边，根据边的权重设置不同样式
    // 在动画模式下，只显示已访问节点之间的边
    queryPath.edges.forEach(edgeId => {
      const edge = cy.getElementById(edgeId);
      if (edge.length > 0) {
        const source = edge.data('source');
        const target = edge.data('target');

        // 检查边的两端节点是否都已被访问
        const sourceVisited = nodesToHighlight.includes(source);
        const targetVisited = nodesToHighlight.includes(target);

        if (sourceVisited && targetVisited) {
          const weight = edge.data('weight') || 0;

          // 高权重边使用更明显的高亮
          if (weight >= 0.7) {
            edge.addClass('query-path-high');
          } else {
            edge.addClass('query-path');
          }
        }
      }
    });

    // 如果有路径节点，聚焦到所有高亮的元素
    if (nodesToHighlight.length > 0) {
      const highlightedElements = cy.elements('.query-path-low, .query-path-medium, .query-path-high, .query-path, .query-path-high');

      if (highlightedElements.length > 0) {
        // 在动画模式下，聚焦到当前节点
        if (animationStep !== null && animationStep !== undefined && animationStep < queryPath.nodes.length) {
          const currentNode = cy.getElementById(queryPath.nodes[animationStep]);
          if (currentNode.length > 0) {
            cy.animate({
              center: {
                eles: currentNode
              },
              zoom: Math.max(cy.zoom(), 1.0),
              duration: 400,
              easing: 'ease-in-out'
            });
          }
        } else if (animationStep === null || animationStep === undefined) {
          // 非动画模式：适配所有高亮元素
          cy.animate({
            fit: {
              eles: highlightedElements,
              padding: 50,
            },
            duration: 600,
            easing: 'ease-in-out'
          });
        }
      }
    }
  }, [queryPath, animationStep, showLocalPath, showGlobalPath, queryMode]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-white transition-all duration-300 ease-in-out"
      style={{ minHeight: '400px' }}
    />
  );
});

GraphCanvas.displayName = 'GraphCanvas';

export default GraphCanvas;
