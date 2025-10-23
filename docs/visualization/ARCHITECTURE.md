# HyperGraphRAG 可视化系统架构文档

## 概述

本文档描述 HyperGraphRAG 可视化系统的技术架构、设计决策和实现细节，面向开发者和贡献者。

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Browser (前端)                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  React Application (web_ui/)                        │   │
│  │  ├─ Components (UI 组件)                            │   │
│  │  ├─ Stores (Zustand 状态管理)                       │   │
│  │  ├─ Services (API 客户端)                           │   │
│  │  └─ Cytoscape.js (图渲染引擎)                       │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST API
                         │ JSON
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend (后端)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API Layer (api/)                                   │   │
│  │  ├─ Routes (路由处理)                               │   │
│  │  ├─ Services (业务逻辑)                             │   │
│  │  ├─ Models (数据模型)                               │   │
│  │  └─ Middleware (中间件)                             │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ Direct Import
┌────────────────────────▼────────────────────────────────────┐
│              HyperGraphRAG Core (核心库)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  hypergraphrag/                                     │   │
│  │  ├─ HyperGraphRAG (主类)                           │   │
│  │  ├─ Storage (存储层)                               │   │
│  │  ├─ Operate (操作层)                               │   │
│  │  └─ LLM (语言模型接口)                             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

#### 后端
- **框架**: FastAPI 0.104+
- **ASGI 服务器**: Uvicorn
- **数据验证**: Pydantic v2
- **图处理**: NetworkX
- **向量搜索**: NanoVectorDB
- **LLM**: OpenAI API

#### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **可视化**: Cytoscape.js
- **UI 组件**: shadcn/ui + Radix UI
- **样式**: Tailwind CSS
- **状态管理**: Zustand
- **HTTP 客户端**: Axios

---

## 后端架构

### 目录结构

```
api/
├── main.py                 # FastAPI 应用入口
├── routes/                 # API 路由
│   ├── graph.py           # 图数据 API
│   └── query.py           # 查询 API
├── services/              # 业务逻辑层
│   ├── graph_service.py   # 图数据服务
│   └── query_service.py   # 查询服务
├── models/                # 数据模型
│   ├── graph.py           # 图数据模型
│   └── query.py           # 查询模型
└── middleware/            # 中间件
    └── error_handler.py   # 错误处理
```

### 核心组件

#### 1. FastAPI 应用 (main.py)

**职责**：
- 应用初始化和配置
- 路由注册
- 中间件配置（CORS、错误处理）
- 生命周期管理

**关键代码**：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化服务
    await graph_service.initialize()
    await query_service.initialize(graph_service.rag)
    yield
    # 关闭时清理资源
```


#### 2. GraphService (services/graph_service.py)

**职责**：
- 管理 HyperGraphRAG 实例
- 提供图数据访问接口
- 实现搜索和过滤逻辑

**关键方法**：
- `initialize()`: 初始化 HyperGraphRAG
- `get_nodes()`: 获取节点列表（分页、过滤）
- `get_edges()`: 获取边列表（转换二部图）
- `get_stats()`: 计算图统计信息
- `get_subgraph()`: BFS 提取子图
- `search_nodes()`: 向量语义搜索

**数据转换**：
```python
# 二部图 → 普通图转换
# Entity ↔ Hyperedge ↔ Entity
# 转换为
# Entity ↔ Entity (边包含超边信息)
```

#### 3. QueryService (services/query_service.py)

**职责**：
- 执行 RAG 查询
- 提取查询路径信息
- 管理查询历史

**关键方法**：
- `execute()`: 执行查询并提取路径
- `get_history()`: 获取查询历史
- `clear_history()`: 清除历史

**查询路径提取**：
```python
# 从 HyperGraphRAG 响应中提取：
# - 访问的节点 ID
# - 访问的边 ID
# - 相关性得分
```

### 数据模型

#### Node (实体节点)
```python
class Node(BaseModel):
    id: str                    # 唯一标识
    label: str                 # 显示名称
    type: str                  # 实体类型
    description: str           # 描述
    weight: float              # 权重 (0.0-1.0)
    relevanceScore: Optional[float]  # 相关性得分
```

#### Edge (边/超边)
```python
class Edge(BaseModel):
    id: str                    # 唯一标识
    source: str                # 源节点 ID
    target: str                # 目标节点 ID
    relation: str              # 关系类型
    description: str           # 关系描述
    weight: float              # 权重
    entities: List[str]        # 所有连接的实体
    isHyperedge: bool          # 是否为超边 (3+ 实体)
```

### API 端点设计

#### Graph API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/graph/nodes` | GET | 获取节点列表 |
| `/api/graph/nodes/{id}` | GET | 获取单个节点 |
| `/api/graph/edges` | GET | 获取边列表 |
| `/api/graph/edges/{id}` | GET | 获取单个边 |
| `/api/graph/stats` | GET | 获取统计信息 |
| `/api/graph/subgraph` | GET | 获取子图 |
| `/api/graph/search` | GET | 搜索节点 |

#### Query API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/query/` | POST | 执行查询 |
| `/api/query/history` | GET | 获取历史 |
| `/api/query/history` | DELETE | 清除历史 |

---

## 前端架构

### 目录结构

```
web_ui/src/
├── components/            # React 组件
│   ├── GraphCanvas.tsx   # 图画布（核心）
│   ├── SearchBar.tsx     # 搜索栏
│   ├── FilterPanel.tsx   # 过滤面板
│   ├── QueryPanel.tsx    # 查询面板
│   ├── QueryInterface.tsx
│   ├── QueryResult.tsx
│   ├── SettingsPanel.tsx # 设置面板
│   ├── ExportPanel.tsx   # 导出面板
│   └── ui/               # shadcn/ui 组件
├── stores/               # Zustand 状态管理
│   ├── graphStore.ts     # 图数据状态
│   ├── queryStore.ts     # 查询状态
│   └── settingsStore.ts  # 设置状态
├── services/             # API 客户端
│   ├── graphService.ts   # 图 API
│   └── queryService.ts   # 查询 API
├── types/                # TypeScript 类型
│   ├── graph.ts
│   ├── query.ts
│   └── settings.ts
├── utils/                # 工具函数
│   ├── api.ts            # Axios 配置
│   └── exportUtils.ts    # 导出工具
└── App.tsx               # 主应用组件
```

### 核心组件

#### 1. GraphCanvas (图画布)

**职责**：
- 初始化 Cytoscape 实例
- 渲染节点和边
- 处理用户交互（点击、拖拽、缩放）
- 应用布局算法

**关键功能**：
```typescript
// 初始化 Cytoscape
const cy = cytoscape({
  container: containerRef.current,
  elements: [...nodes, ...edges],
  style: cytoscapeStyles,
  layout: { name: 'cose' }
});

// 事件处理
cy.on('tap', 'node', handleNodeClick);
cy.on('dblclick', 'node', handleNodeExpand);
```

**性能优化**：
- 视口裁剪（只渲染可见节点）
- 懒加载（分批加载节点）
- 防抖/节流（减少重绘）

#### 2. 状态管理 (Zustand)

**graphStore**：
```typescript
interface GraphStore {
  nodes: Node[];
  edges: Edge[];
  stats: GraphStats;
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  
  // Actions
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  selectNode: (node: Node) => void;
  // ...
}
```

**queryStore**：
```typescript
interface QueryStore {
  currentQuery: string;
  queryMode: QueryMode;
  queryResult: QueryResponse | null;
  queryHistory: QueryHistoryItem[];
  isLoading: boolean;
  
  // Actions
  executeQuery: (query: string) => Promise<void>;
  // ...
}
```

**settingsStore**：
```typescript
interface SettingsStore {
  layout: LayoutSettings;
  colors: ColorScheme;
  nodeStyle: NodeStyle;
  edgeStyle: EdgeStyle;
  
  // Actions
  updateLayout: (settings: Partial<LayoutSettings>) => void;
  // ...
}
```

#### 3. API 服务层

**graphService.ts**：
```typescript
export const graphService = {
  getNodes: (params: GetNodesParams) => 
    api.get<Node[]>('/graph/nodes', { params }),
  
  getEdges: (params: GetEdgesParams) => 
    api.get<Edge[]>('/graph/edges', { params }),
  
  searchNodes: (keyword: string, limit: number) =>
    api.get<Node[]>('/graph/search', { params: { keyword, limit } }),
  
  // ...
};
```

### 数据流

```
User Action
    ↓
Component Event Handler
    ↓
Store Action
    ↓
API Service Call
    ↓
Backend API
    ↓
Response
    ↓
Store Update
    ↓
Component Re-render
```

### 组件通信

```
App.tsx
  ├─ GraphCanvas (订阅 graphStore)
  │    ├─ 读取 nodes, edges
  │    └─ 调用 selectNode, selectEdge
  │
  ├─ SearchBar (订阅 graphStore)
  │    └─ 调用 graphService.searchNodes
  │
  ├─ FilterPanel (订阅 graphStore, settingsStore)
  │    └─ 更新过滤条件
  │
  └─ QueryPanel (订阅 queryStore)
       └─ 调用 queryService.executeQuery
```

---

## 数据存储

### 文件存储结构

```
expr/example/
├── vdb_entities.json              # 实体向量数据库
├── vdb_hyperedges.json            # 超边向量数据库
├── graph_chunk_entity_relation.graphml  # 图结构
├── kv_store_text_chunks.json     # 文本块
└── kv_store_llm_response_cache.json  # LLM 缓存
```

### 数据加载流程

```
1. HyperGraphRAG.__init__()
   ↓
2. 自动加载 working_dir 下的所有文件
   ↓
3. 初始化存储实例：
   - entities_vdb (NanoVectorDB)
   - relationships_vdb (NanoVectorDB)
   - chunk_entity_relation_graph (NetworkX)
   - text_chunks (JsonKVStorage)
   ↓
4. 数据加载到内存
   ↓
5. GraphService 访问数据
```

### 二部图结构

**原始结构**：
```
Entity Node (role="entity")
    ↓ edge
Hyperedge Node (role="hyperedge")
    ↓ edge
Entity Node (role="entity")
```

**转换后**：
```
Entity Node
    ↓ edge (包含超边信息)
Entity Node
```

---

## 关键设计决策

### 1. 为什么选择 FastAPI？

**优势**：
- 原生异步支持（与 HyperGraphRAG 一致）
- 自动生成 OpenAPI 文档
- Pydantic 数据验证
- 高性能（基于 Starlette）
- 易于开发和测试

### 2. 为什么选择 Cytoscape.js？

**对比**：
- **Cytoscape.js**: 专为图可视化设计，性能好，支持复合节点
- **D3.js**: 更灵活但开发成本高
- **G6**: 功能强大但文档较少

**选择理由**：
- 专业的图可视化库
- 丰富的布局算法
- 良好的性能（10,000+ 节点）
- 活跃的社区

### 3. 为什么使用 Zustand？

**对比**：
- **Redux**: 功能强大但样板代码多
- **MobX**: 响应式但学习曲线陡
- **Zustand**: 轻量、简单、TypeScript 友好

**选择理由**：
- 最小化样板代码
- 优秀的 TypeScript 支持
- 易于测试
- 性能好

### 4. 为什么不使用数据库？

**原因**：
- HyperGraphRAG 使用文件存储
- 中小规模数据（< 100,000 实体）
- 简化部署和维护
- 快速原型开发

**扩展性**：
- 可后续升级到 Neo4j（图数据库）
- 可使用 Milvus（向量数据库）
- 保持 API 接口不变

---

## 性能优化

### 后端优化

#### 1. 响应缓存
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_graph_stats():
    # 缓存统计信息
    pass
```

#### 2. 分页查询
```python
# 强制分页，避免一次返回过多数据
limit: int = Query(100, le=10000)
offset: int = Query(0, ge=0)
```

#### 3. 异步处理
```python
# 所有 I/O 操作使用 async/await
async def get_nodes(...):
    # 异步处理
    pass
```

### 前端优化

#### 1. 虚拟化渲染
```typescript
// 只渲染视口内的节点
const visibleNodes = nodes.filter(node => 
  isInViewport(node.position, viewport)
);
```

#### 2. 防抖/节流
```typescript
// 搜索输入防抖
const debouncedSearch = useMemo(
  () => debounce(handleSearch, 300),
  []
);
```

#### 3. 懒加载
```typescript
// 初始只加载核心节点
const [loadedNodes, setLoadedNodes] = useState(
  nodes.slice(0, 1000)
);

// 滚动时加载更多
const loadMore = () => {
  setLoadedNodes(prev => [
    ...prev,
    ...nodes.slice(prev.length, prev.length + 1000)
  ]);
};
```

#### 4. Web Worker
```typescript
// 将布局计算移到 Worker
const worker = new Worker('layout-worker.js');
worker.postMessage({ nodes, edges });
worker.onmessage = (e) => {
  const layout = e.data;
  applyLayout(layout);
};
```

---

## 测试策略

### 后端测试

#### 单元测试
```python
# tests/unit/test_graph_service.py
@pytest.mark.asyncio
async def test_get_nodes():
    service = GraphService()
    await service.initialize()
    nodes = await service.get_nodes(10, 0, None)
    assert len(nodes) <= 10
```

#### 集成测试
```python
# tests/integration/test_api.py
def test_get_nodes_endpoint():
    response = client.get("/api/graph/nodes?limit=10")
    assert response.status_code == 200
    assert len(response.json()) <= 10
```

### 前端测试

#### 组件测试
```typescript
// tests/components/GraphCanvas.test.tsx
test('renders graph canvas', () => {
  render(<GraphCanvas data={mockData} />);
  expect(screen.getByTestId('graph-canvas')).toBeInTheDocument();
});
```

#### E2E 测试
```typescript
// tests/e2e/visualization.spec.ts
test('can search and select node', async ({ page }) => {
  await page.goto('http://localhost:3400');
  await page.fill('input[placeholder="Search"]', 'hypertension');
  await page.click('.search-result:first-child');
  expect(await page.locator('.node-details').isVisible()).toBeTruthy();
});
```

---

## 部署架构

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./api
    ports:
      - "3401:3401"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./expr:/app/expr
  
  frontend:
    build: ./web_ui
    ports:
      - "3400:80"
    depends_on:
      - backend
```

### 生产部署

```
┌─────────────────────────────────────┐
│         Load Balancer (Nginx)       │
└────────┬────────────────────┬───────┘
         │                    │
    ┌────▼────┐          ┌────▼────┐
    │ Backend │          │ Backend │
    │ (API)   │          │ (API)   │
    └─────────┘          └─────────┘
         │                    │
    ┌────▼────────────────────▼────┐
    │     Shared File Storage      │
    │     (expr/example/)          │
    └──────────────────────────────┘
```

---

## 扩展指南

### 添加新的 API 端点

1. **定义数据模型** (`api/models/`)
```python
class NewModel(BaseModel):
    field1: str
    field2: int
```

2. **实现业务逻辑** (`api/services/`)
```python
class NewService:
    async def new_method(self):
        # 实现逻辑
        pass
```

3. **创建路由** (`api/routes/`)
```python
@router.get("/new-endpoint")
async def new_endpoint():
    return await new_service.new_method()
```

4. **注册路由** (`api/main.py`)
```python
app.include_router(new_router, prefix="/api/new", tags=["new"])
```

5. **编写测试**
```python
def test_new_endpoint():
    response = client.get("/api/new-endpoint")
    assert response.status_code == 200
```

### 添加新的前端组件

1. **创建组件** (`web_ui/src/components/`)
```typescript
export const NewComponent: React.FC = () => {
  return <div>New Component</div>;
};
```

2. **添加到 Store** (如需要)
```typescript
interface NewStore {
  newState: string;
  setNewState: (state: string) => void;
}
```

3. **集成到应用**
```typescript
// App.tsx
<NewComponent />
```

4. **编写测试**
```typescript
test('renders new component', () => {
  render(<NewComponent />);
  expect(screen.getByText('New Component')).toBeInTheDocument();
});
```

---

## 贡献指南

### 代码规范

#### Python
- 使用 Black 格式化
- 使用 Type Hints
- 遵循 PEP 8
- 编写 Docstrings

#### TypeScript
- 使用 ESLint + Prettier
- 严格模式 (`strict: true`)
- 函数式组件 + Hooks
- 避免 `any` 类型

### Git 工作流

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m "feat: add new feature"`
4. 推送分支：`git push origin feature/new-feature`
5. 创建 Pull Request

### Commit 规范

使用 Conventional Commits：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

---

## 常见问题

### 如何调试后端？

```python
# 启用 DEBUG 日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用 pdb
import pdb; pdb.set_trace()
```

### 如何调试前端？

- 使用浏览器 DevTools（F12）
- 查看 Console 和 Network 标签
- 使用 React DevTools 扩展

### 如何添加新的布局算法？

1. 在 Cytoscape.js 中注册布局
2. 在设置面板添加选项
3. 更新 `settingsStore`

---

## 参考资源

### 文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Cytoscape.js 文档](https://js.cytoscape.org/)
- [React 文档](https://react.dev/)
- [Zustand 文档](https://github.com/pmndrs/zustand)

### 工具
- [Swagger UI](http://localhost:3401/docs)
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Postman](https://www.postman.com/)

---

## 更新日志

### v1.0.0 (2025-10-22)
- 初始版本
- 完整的图可视化功能
- RAG 查询支持
- 导出和配置功能

---

## 联系方式

- GitHub Issues
- 技术支持邮箱
- 开发者社区

---

**最后更新**: 2025-10-22
