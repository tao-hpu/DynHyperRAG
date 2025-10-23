// 可视化配置类型定义

export interface LayoutSettings {
  // 力导向布局参数
  idealEdgeLength: number;
  nodeRepulsion: number;
  gravity: number;
  numIter: number;
}

export interface NodeSettings {
  // 节点大小
  minSize: number;
  maxSize: number;
  // 标签字体
  fontSize: number;
  fontWeight: number;
}

export interface ColorScheme {
  // 节点颜色（按类型）
  person: string;
  organization: string;
  location: string;
  event: string;
  concept: string;
  default: string;
  // 边颜色
  edge: string;
  hyperedge: string;
  // 查询路径颜色
  queryPathLow: string;
  queryPathMedium: string;
  queryPathHigh: string;
}

export interface VisualizationSettings {
  layout: LayoutSettings;
  node: NodeSettings;
  colorScheme: ColorScheme;
}

// 默认配置
export const defaultSettings: VisualizationSettings = {
  layout: {
    idealEdgeLength: 120,
    nodeRepulsion: 6000,
    gravity: 0.5,
    numIter: 2500,
  },
  node: {
    minSize: 20,
    maxSize: 60,
    fontSize: 12,
    fontWeight: 500,
  },
  colorScheme: {
    person: '#10b981',
    organization: '#f59e0b',
    location: '#8b5cf6',
    event: '#ec4899',
    concept: '#06b6d4',
    default: '#3b82f6',
    edge: '#9ca3af',
    hyperedge: '#fb923c',
    queryPathLow: '#fef3c7',
    queryPathMedium: '#fbbf24',
    queryPathHigh: '#f59e0b',
  },
};

// 预设颜色方案
export const colorSchemePresets: Record<string, ColorScheme> = {
  default: defaultSettings.colorScheme,
  vibrant: {
    person: '#22c55e',
    organization: '#f97316',
    location: '#a855f7',
    event: '#f43f5e',
    concept: '#14b8a6',
    default: '#3b82f6',
    edge: '#94a3b8',
    hyperedge: '#fb923c',
    queryPathLow: '#fef3c7',
    queryPathMedium: '#fbbf24',
    queryPathHigh: '#f59e0b',
  },
  pastel: {
    person: '#86efac',
    organization: '#fdba74',
    location: '#c4b5fd',
    event: '#fda4af',
    concept: '#5eead4',
    default: '#93c5fd',
    edge: '#cbd5e1',
    hyperedge: '#fdba74',
    queryPathLow: '#fef3c7',
    queryPathMedium: '#fde68a',
    queryPathHigh: '#fcd34d',
  },
  monochrome: {
    person: '#71717a',
    organization: '#52525b',
    location: '#3f3f46',
    event: '#27272a',
    concept: '#18181b',
    default: '#52525b',
    edge: '#d4d4d8',
    hyperedge: '#a1a1aa',
    queryPathLow: '#f4f4f5',
    queryPathMedium: '#e4e4e7',
    queryPathHigh: '#d4d4d8',
  },
};
