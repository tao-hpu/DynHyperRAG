# HyperGraphRAG 可视化项目

## 🎉 项目状态

**Phase 1 (后端 API)**: ✅ 已完成  
**Phase 2 (前端开发)**: ⏳ 待开始  
**Phase 3 (查询可视化)**: ⏳ 待开始

---

## 📚 文档导航

### 快速开始
- **[快速参考](../../QUICKREF.md)** - 一页纸快速参考
- **[API 快速开始](./API_QUICKSTART.md)** - 5 分钟上手指南

### API 文档
- **[API 参考](./API_REFERENCE.md)** - 完整的 API 端点文档
- **[交互式文档](http://localhost:8000/docs)** - OpenAPI 自动生成（需启动服务）

### 项目文档
- **[Phase 1 总结](./PHASE1_SUMMARY.md)** - 后端开发完成总结
- **[进度跟踪](./PROGRESS.md)** - 实时开发进度
- **[部署指南](./DEPLOYMENT.md)** - 生产环境部署

### Spec 文档
- **[需求文档](../../.kiro/specs/hypergraph-visualization/requirements.md)** - 功能需求
- **[设计文档](../../.kiro/specs/hypergraph-visualization/design.md)** - 技术设计
- **[任务列表](../../.kiro/specs/hypergraph-visualization/tasks.md)** - 开发任务

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────┐
│         Browser (前端 - 待开发)          │
│  React + TypeScript + Cytoscape.js     │
└────────────────┬────────────────────────┘
                 │ HTTP REST API
┌────────────────▼────────────────────────┐
│         FastAPI Backend (✅ 完成)        │
│  ├─ Graph API (7 endpoints)            │
│  └─ Query API (3 endpoints)            │
└────────────────┬────────────────────────┘
                 │ Direct Import
┌────────────────▼────────────────────────┐
│      HyperGraphRAG Core (现有)          │
│  NetworkX + NanoVectorDB + OpenAI      │
└─────────────────────────────────────────┘
```

---

## ✨ 已实现功能

### Graph API (7 个端点)
- ✅ 获取节点列表（分页、过滤）
- ✅ 获取单个节点详情
- ✅ 获取边列表（权重过滤）
- ✅ 获取单个边详情
- ✅ 获取图统计信息
- ✅ 获取子图（BFS）
- ✅ 搜索节点（语义搜索）

### Query API (3 个端点)
- ✅ 执行 RAG 查询（4 种模式）
- ✅ 获取查询历史
- ✅ 清空查询历史

### 测试
- ✅ 24 个单元测试
- ✅ 40+ 集成测试
- ✅ 10+ 性能测试

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 设置 OPENAI_API_KEY
```

### 2. 生成数据

```bash
python script_construct.py
```

### 3. 启动 API

```bash
# 方式 1: 使用脚本
./scripts/start_api.sh

# 方式 2: 直接运行
python api/main.py
```

### 4. 访问

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

---

## 📖 使用示例

### Python

```python
import requests

# 获取图统计
response = requests.get("http://localhost:8000/api/graph/stats")
stats = response.json()
print(f"Nodes: {stats['num_nodes']}, Edges: {stats['num_edges']}")

# 搜索节点
response = requests.get(
    "http://localhost:8000/api/graph/search",
    params={"keyword": "hypertension", "limit": 5}
)
results = response.json()

# 执行查询
response = requests.post(
    "http://localhost:8000/api/query/",
    json={
        "query": "What is hypertension?",
        "mode": "hybrid",
        "top_k": 60
    }
)
answer = response.json()["answer"]
```

### cURL

```bash
# 获取节点
curl "http://localhost:8000/api/graph/nodes?limit=10"

# 搜索
curl "http://localhost:8000/api/graph/search?keyword=test"

# 查询
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is hypertension?", "mode": "hybrid"}'
```

---

## 🧪 测试

```bash
# 运行所有测试
./scripts/run_tests.sh

# 单独运行
pytest tests/test_models.py -v              # 单元测试
pytest tests/test_api_integration.py -v     # 集成测试
pytest tests/test_performance.py -v -s      # 性能测试
```

---

## 📊 性能

| 指标 | 值 |
|------|-----|
| 节点查询 | < 2s |
| 边查询 | < 2s |
| 统计信息 | < 1s |
| 搜索 | < 3s |
| RAG 查询 | < 30s |
| 并发支持 | 10+ req/s |

---

## 🗺️ 路线图

### ✅ Phase 1: 后端 API（已完成）
- FastAPI 项目结构
- 数据模型层
- GraphService 业务逻辑
- Graph API 路由
- Query API
- 集成测试

### ⏳ Phase 2: 前端开发（下一步）
- React + Vite + TypeScript
- shadcn/ui + Tailwind CSS
- Cytoscape.js 图渲染
- 基础交互功能
- 搜索和过滤

### ⏳ Phase 3: 查询可视化
- 查询界面
- 查询结果显示
- 路径高亮
- 动画效果

---

## 🤝 贡献

欢迎贡献！请查看：
- [任务列表](../../.kiro/specs/hypergraph-visualization/tasks.md) - 待完成的任务
- [设计文档](../../.kiro/specs/hypergraph-visualization/design.md) - 技术设计

---

## 📝 许可

本项目基于原始 HyperGraphRAG 项目，遵循相同的许可协议。

---

## 📞 联系

- **维护者**: Tao An
- **GitHub**: https://github.com/tao-hpu/HyperGraphRAG
- **原始项目**: https://github.com/LHRLAB/HyperGraphRAG

---

**最后更新**: 2025-10-21  
**版本**: 1.0.0 (Phase 1)
