/**
 * Layout Worker
 * Web Worker for offloading layout calculations
 * 将布局计算移到 Web Worker 以避免阻塞主线程
 */

// Worker 消息类型
export interface LayoutWorkerMessage {
  type: 'calculate' | 'stop';
  data?: {
    nodes: Array<{ id: string; x?: number; y?: number }>;
    edges: Array<{ source: string; target: string; weight?: number }>;
    options: LayoutOptions;
  };
}

export interface LayoutWorkerResponse {
  type: 'progress' | 'complete' | 'error';
  data?: {
    positions?: Record<string, { x: number; y: number }>;
    progress?: number;
    error?: string;
  };
}

export interface LayoutOptions {
  algorithm: 'force-directed' | 'grid' | 'circle';
  iterations: number;
  idealEdgeLength: number;
  nodeRepulsion: number;
  gravity: number;
  damping: number;
}

// 简单的力导向布局算法实现
class ForceDirectedLayout {
  private nodes: Map<string, { id: string; x: number; y: number; vx: number; vy: number }>;
  private edges: Array<{ source: string; target: string; weight: number }>;
  private options: LayoutOptions;
  private stopped: boolean = false;

  constructor(
    nodes: Array<{ id: string; x?: number; y?: number }>,
    edges: Array<{ source: string; target: string; weight?: number }>,
    options: LayoutOptions
  ) {
    this.options = options;
    this.edges = edges.map(e => ({ ...e, weight: e.weight || 1 }));

    // 初始化节点位置（如果没有提供）
    this.nodes = new Map();
    nodes.forEach((node, index) => {
      const angle = (index / nodes.length) * 2 * Math.PI;
      const radius = 100;
      this.nodes.set(node.id, {
        id: node.id,
        x: node.x ?? Math.cos(angle) * radius,
        y: node.y ?? Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      });
    });
  }

  stop(): void {
    this.stopped = true;
  }

  async calculate(onProgress?: (progress: number) => void): Promise<Record<string, { x: number; y: number }>> {
    const { iterations, idealEdgeLength, nodeRepulsion, gravity, damping } = this.options;

    for (let iter = 0; iter < iterations; iter++) {
      if (this.stopped) break;

      // 计算斥力（节点之间）
      const nodeArray = Array.from(this.nodes.values());
      for (let i = 0; i < nodeArray.length; i++) {
        for (let j = i + 1; j < nodeArray.length; j++) {
          const node1 = nodeArray[i];
          const node2 = nodeArray[j];

          const dx = node2.x - node1.x;
          const dy = node2.y - node1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;

          // Coulomb's law: F = k / r^2
          const force = nodeRepulsion / (distance * distance);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;

          node1.vx -= fx;
          node1.vy -= fy;
          node2.vx += fx;
          node2.vy += fy;
        }
      }

      // 计算引力（边）
      this.edges.forEach(edge => {
        const source = this.nodes.get(edge.source);
        const target = this.nodes.get(edge.target);

        if (!source || !target) return;

        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const distance = Math.sqrt(dx * dx + dy * dy) || 1;

        // Hooke's law: F = k * (x - l)
        const force = (distance - idealEdgeLength) * 0.1 * edge.weight;
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;

        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      });

      // 应用重力（向中心）
      nodeArray.forEach(node => {
        node.vx -= node.x * gravity;
        node.vy -= node.y * gravity;
      });

      // 更新位置并应用阻尼
      nodeArray.forEach(node => {
        node.vx *= damping;
        node.vy *= damping;
        node.x += node.vx;
        node.y += node.vy;
      });

      // 报告进度
      if (onProgress && iter % 10 === 0) {
        const progress = (iter / iterations) * 100;
        onProgress(progress);
      }

      // 每 100 次迭代让出控制权
      if (iter % 100 === 0) {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }

    // 返回最终位置
    const positions: Record<string, { x: number; y: number }> = {};
    this.nodes.forEach((node, id) => {
      positions[id] = { x: node.x, y: node.y };
    });

    return positions;
  }
}

// 网格布局
function calculateGridLayout(
  nodes: Array<{ id: string }>,
  options: { spacing: number }
): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};
  const cols = Math.ceil(Math.sqrt(nodes.length));
  const spacing = options.spacing || 100;

  nodes.forEach((node, index) => {
    const row = Math.floor(index / cols);
    const col = index % cols;
    positions[node.id] = {
      x: col * spacing,
      y: row * spacing,
    };
  });

  return positions;
}

// 圆形布局
function calculateCircleLayout(
  nodes: Array<{ id: string }>,
  options: { radius: number }
): Record<string, { x: number; y: number }> {
  const positions: Record<string, { x: number; y: number }> = {};
  const radius = options.radius || 200;

  nodes.forEach((node, index) => {
    const angle = (index / nodes.length) * 2 * Math.PI;
    positions[node.id] = {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
    };
  });

  return positions;
}

// Worker 全局变量
let currentLayout: ForceDirectedLayout | null = null;

// Worker 消息处理
self.onmessage = async (event: MessageEvent<LayoutWorkerMessage>) => {
  const { type, data } = event.data;

  if (type === 'stop') {
    if (currentLayout) {
      currentLayout.stop();
      currentLayout = null;
    }
    return;
  }

  if (type === 'calculate' && data) {
    try {
      const { nodes, edges, options } = data;

      let positions: Record<string, { x: number; y: number }>;

      if (options.algorithm === 'force-directed') {
        currentLayout = new ForceDirectedLayout(nodes, edges, options);
        
        positions = await currentLayout.calculate((progress) => {
          // 发送进度更新
          const response: LayoutWorkerResponse = {
            type: 'progress',
            data: { progress },
          };
          self.postMessage(response);
        });

        currentLayout = null;
      } else if (options.algorithm === 'grid') {
        positions = calculateGridLayout(nodes, { spacing: options.idealEdgeLength });
      } else if (options.algorithm === 'circle') {
        positions = calculateCircleLayout(nodes, { radius: options.idealEdgeLength * 2 });
      } else {
        throw new Error(`Unknown algorithm: ${options.algorithm}`);
      }

      // 发送完成消息
      const response: LayoutWorkerResponse = {
        type: 'complete',
        data: { positions },
      };
      self.postMessage(response);
    } catch (error) {
      // 发送错误消息
      const response: LayoutWorkerResponse = {
        type: 'error',
        data: { error: error instanceof Error ? error.message : String(error) },
      };
      self.postMessage(response);
    }
  }
};

// 导出类型供主线程使用
export type { };
