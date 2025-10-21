# HyperGraphRAG Web UI

超图可视化前端应用，基于 React + TypeScript + Vite 构建。

## ✨ 核心特性

### 🎨 高级图可视化
- **Cytoscape.js 3.33.1** - 专业级图可视化引擎
- **cose-bilkent 布局** - 高质量力导向布局算法 ⭐⭐⭐⭐⭐
- **超边凸包渲染** - 使用 Graham Scan 算法绘制超边包围区域
- **类型着色系统** - 5 种实体类型自动着色
- **动态节点大小** - 根据权重自动调整

### 🖱️ 丰富交互
- 单击节点/边查看详情
- 双击节点展开邻居
- 拖拽节点调整位置
- 滚轮缩放、拖拽平移
- 悬停显示详细信息

### ⚡ 性能优化
- 视口外边隐藏
- 纹理渲染加速
- 运动模糊效果
- 批量更新优化

## 技术栈

- **框架**: React 19 + TypeScript
- **构建工具**: Vite 7
- **图可视化**: Cytoscape.js + cose-bilkent
- **UI 组件**: shadcn/ui + Radix UI
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **图标**: Lucide React

## 项目结构

```
src/
├── components/       # React 组件
│   └── ui/          # shadcn/ui 基础组件
├── hooks/           # 自定义 React Hooks
├── lib/             # 工具库
│   └── utils.ts     # Tailwind 工具函数
├── services/        # API 服务层
├── stores/          # Zustand 状态管理
│   ├── graphStore.ts    # 图数据状态
│   └── queryStore.ts    # 查询状态
├── types/           # TypeScript 类型定义
│   ├── graph.ts     # 图相关类型
│   └── query.ts     # 查询相关类型
├── utils/           # 工具函数
│   └── api.ts       # Axios 配置
├── App.tsx          # 主应用组件
└── main.tsx         # 应用入口
```

## 开发

### 安装依赖

```bash
pnpm install
```

### 启动开发服务器

```bash
pnpm dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
pnpm build
```

### 预览生产构建

```bash
pnpm preview
```

## 配置

### 环境变量

复制 `.env.example` 到 `.env` 并配置：

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### 路径别名

项目配置了 `@/` 路径别名指向 `src/` 目录：

```typescript
import { Button } from '@/components/ui/button';
import { useGraphStore } from '@/stores/graphStore';
```

## 状态管理

### Graph Store

管理图数据、选中状态、过滤器和视口状态：

```typescript
import { useGraphStore } from '@/stores/graphStore';

const { graphData, selectNode, highlightNodes } = useGraphStore();
```

### Query Store

管理查询状态、历史记录和配置：

```typescript
import { useQueryStore } from '@/stores/queryStore';

const { currentQuery, setCurrentQuery, addToHistory } = useQueryStore();
```

## API 客户端

使用配置好的 Axios 实例：

```typescript
import api from '@/utils/api';

const response = await api.get('/graph/nodes');
```

## 📚 文档

- [Cytoscape.js 特性文档](../docs/visualization/CYTOSCAPE_FEATURES.md)
- [实现清单](../docs/visualization/IMPLEMENTATION_CHECKLIST.md)
- [可视化策略](../docs/visualization/HYPERGRAPH_VISUALIZATION_STRATEGIES.md)

## 🎯 可视化特性详解

### 超边凸包渲染

超边（连接 3+ 个实体）使用凸包算法渲染：

```
传统方式：           凸包渲染：
A --- B              ╭─────────╮
 \   /               │  A   B  │ ← 半透明橙色区域
  \ /                │    C    │
   C                 ╰─────────╯
```

### 节点类型着色

| 类型 | 颜色 | 示例 |
|------|------|------|
| Person | 🟢 绿色 | 张三、李四 |
| Organization | 🟠 橙色 | 公司、机构 |
| Location | 🟣 紫色 | 城市、地点 |
| Event | 🩷 粉色 | 会议、事件 |
| Concept | 🔵 青色 | 概念、理论 |

### 布局算法

使用 **cose-bilkent** 高质量力导向布局：
- 节点斥力：4500
- 理想边长：100px
- 重力：0.25
- 迭代次数：2500

比默认 cose 布局质量更高，边交叉更少。

## 🚀 快速开始

### 1. 安装依赖（使用 pnpm）

```bash
pnpm install
```

### 2. 启动开发服务器

```bash
pnpm dev
```

访问 http://localhost:3400

### 3. 确保后端运行

```bash
cd ..
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload
```

## 🎮 使用指南

### 基本操作
1. **查看图谱**：页面加载后自动显示知识图谱
2. **搜索节点**：使用顶部搜索栏快速定位
3. **过滤数据**：右侧面板按类型和权重过滤
4. **查看详情**：点击节点或边查看详细信息

### 高级操作
1. **展开节点**：双击节点加载其邻居
2. **调整布局**：拖拽节点到理想位置
3. **识别超边**：橙色粗线 + 凸包区域标识
4. **缩放导航**：滚轮缩放，拖拽平移

## 🛠️ 开发指南

### 添加新的布局算法

```bash
# 安装插件
pnpm add cytoscape-fcose

# 在 GraphCanvas.tsx 中使用
import fcose from 'cytoscape-fcose';
cytoscape.use(fcose);

const layout = cy.layout({ name: 'fcose' });
```

### 自定义节点样式

编辑 `src/components/GraphCanvas.tsx`：

```typescript
{
  selector: 'node[type="custom"]',
  style: {
    'background-color': '#your-color',
    'border-color': '#your-border',
  }
}
```

## 📦 构建部署

### 构建生产版本

```bash
pnpm build
```

输出到 `dist/` 目录。

### 预览构建

```bash
pnpm preview
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:3401;
    }
}
```
