import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
// @ts-ignore - cytoscape-cose-bilkent 没有类型定义
import coseBilkent from 'cytoscape-cose-bilkent';
import type { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import type { GraphData, Node, Edge } from '@/types/graph';

// 注册 cose-bilkent 布局插件
cytoscape.use(coseBilkent);

interface GraphCanvasProps {
  data: GraphData;
  onNodeClick?: (node: Node) => void;
  onEdgeClick?: (edge: Edge) => void;
  onNodeDoubleClick?: (nodeId: string) => void;
  focusNodeId?: string | null;
}

const GraphCanvas = ({ data, onNodeClick, onEdgeClick, onNodeDoubleClick, focusNodeId }: GraphCanvasProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

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
      ],

      // 初始布局（后续会应用力导向布局）
      layout: {
        name: 'preset',
      },

      // 交互配置
      minZoom: 0.1,
      maxZoom: 10,

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
    window.addEventListener('resize', resizeOverlay);

    // 清理函数
    return () => {
      window.removeEventListener('resize', resizeOverlay);
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

  // 转换数据并渲染图
  useEffect(() => {
    if (!cyRef.current || !data) return;

    const cy = cyRef.current;

    // 检查实例是否已销毁
    if (cy.destroyed()) return;

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
        size: Math.max(20, Math.min(60, 20 + node.weight * 20)),
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

    // 应用 cose-bilkent 高质量力导向布局
    const layout = cy.layout({
      name: 'cose-bilkent',
      // @ts-ignore - cose-bilkent 特定选项
      animate: 'end',
      animationDuration: 1000,
      // 布局参数优化
      idealEdgeLength: 120,
      nodeRepulsion: 6000,
      gravity: 0.5,
      numIter: 2500,
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

  }, [data]);

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

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-white"
      style={{ minHeight: '600px' }}
    />
  );
};

export default GraphCanvas;
