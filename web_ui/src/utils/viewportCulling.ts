/**
 * Viewport Culling Utilities
 * 视口裁剪工具 - 仅渲染视口内的节点和边
 */

import type { Core, NodeSingular, EdgeSingular, BoundingBox12 } from 'cytoscape';

export interface ViewportBounds {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/**
 * 计算当前视口范围（模型坐标）
 */
export function getViewportBounds(cy: Core): ViewportBounds {
  const extent = cy.extent();
  return {
    x1: extent.x1,
    y1: extent.y1,
    x2: extent.x2,
    y2: extent.y2,
  };
}

/**
 * 检查节点是否在视口内
 */
export function isNodeInViewport(
  node: NodeSingular,
  viewport: ViewportBounds,
  padding: number = 100
): boolean {
  const bb = node.boundingBox() as BoundingBox12;
  
  // 添加 padding 以提前加载即将进入视口的节点
  return !(
    bb.x2 + padding < viewport.x1 ||
    bb.x1 - padding > viewport.x2 ||
    bb.y2 + padding < viewport.y1 ||
    bb.y1 - padding > viewport.y2
  );
}

/**
 * 检查边是否在视口内（检查两端节点）
 */
export function isEdgeInViewport(
  edge: EdgeSingular,
  viewport: ViewportBounds,
  padding: number = 100
): boolean {
  const source = edge.source();
  const target = edge.target();
  
  // 如果任一端点在视口内，则边可见
  return (
    isNodeInViewport(source, viewport, padding) ||
    isNodeInViewport(target, viewport, padding)
  );
}

/**
 * 应用视口裁剪 - 隐藏视口外的元素
 */
export function applyViewportCulling(
  cy: Core,
  options: {
    enabled: boolean;
    padding?: number;
    minZoom?: number; // 最小缩放级别才启用裁剪
  } = { enabled: true }
): void {
  if (!options.enabled) {
    // 禁用裁剪 - 显示所有元素
    cy.elements().style('display', 'element');
    return;
  }

  const zoom = cy.zoom();
  const minZoom = options.minZoom || 0.5;
  
  // 只在缩小到一定程度时启用裁剪（放大时显示所有元素）
  if (zoom > minZoom) {
    cy.elements().style('display', 'element');
    return;
  }

  const viewport = getViewportBounds(cy);
  const padding = options.padding || 100;

  // 批量更新以提高性能
  cy.batch(() => {
    // 处理节点
    cy.nodes().forEach((node) => {
      const inViewport = isNodeInViewport(node, viewport, padding);
      node.style('display', inViewport ? 'element' : 'none');
    });

    // 处理边 - 只显示两端都可见的边
    cy.edges().forEach((edge) => {
      const source = edge.source();
      const target = edge.target();
      const sourceVisible = source.style('display') === 'element';
      const targetVisible = target.style('display') === 'element';
      
      edge.style('display', sourceVisible && targetVisible ? 'element' : 'none');
    });
  });
}

/**
 * 创建视口裁剪管理器
 */
export class ViewportCullingManager {
  private cy: Core;
  private enabled: boolean = true;
  private padding: number = 100;
  private minZoom: number = 0.5;
  private throttleTimer: ReturnType<typeof setTimeout> | null = null;
  private throttleDelay: number = 100; // 节流延迟（毫秒）

  constructor(cy: Core, options?: {
    enabled?: boolean;
    padding?: number;
    minZoom?: number;
    throttleDelay?: number;
  }) {
    this.cy = cy;
    if (options) {
      this.enabled = options.enabled ?? true;
      this.padding = options.padding ?? 100;
      this.minZoom = options.minZoom ?? 0.5;
      this.throttleDelay = options.throttleDelay ?? 100;
    }

    this.setupListeners();
  }

  private setupListeners(): void {
    // 监听视口变化事件（缩放、平移）
    this.cy.on('viewport', this.handleViewportChange);
    
    // 监听数据变化
    this.cy.on('add remove', this.handleDataChange);
  }

  private handleViewportChange = (): void => {
    if (!this.enabled) return;

    // 节流处理，避免频繁更新
    if (this.throttleTimer) {
      clearTimeout(this.throttleTimer);
    }

    this.throttleTimer = setTimeout(() => {
      this.update();
    }, this.throttleDelay);
  };

  private handleDataChange = (): void => {
    if (!this.enabled) return;
    this.update();
  };

  public update(): void {
    applyViewportCulling(this.cy, {
      enabled: this.enabled,
      padding: this.padding,
      minZoom: this.minZoom,
    });
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    this.update();
  }

  public setPadding(padding: number): void {
    this.padding = padding;
    this.update();
  }

  public setMinZoom(minZoom: number): void {
    this.minZoom = minZoom;
    this.update();
  }

  public destroy(): void {
    if (this.throttleTimer) {
      clearTimeout(this.throttleTimer);
    }
    this.cy.off('viewport', this.handleViewportChange);
    this.cy.off('add remove', this.handleDataChange);
  }

  public getStats(): {
    totalNodes: number;
    visibleNodes: number;
    totalEdges: number;
    visibleEdges: number;
  } {
    const totalNodes = this.cy.nodes().length;
    const visibleNodes = this.cy.nodes('[display = "element"]').length;
    const totalEdges = this.cy.edges().length;
    const visibleEdges = this.cy.edges('[display = "element"]').length;

    return {
      totalNodes,
      visibleNodes,
      totalEdges,
      visibleEdges,
    };
  }
}
