# HyperGraphRAG Visualization - 快速参考

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境
cp .env.example .env
# 编辑 .env 设置 OPENAI_API_KEY

# 3. 生成数据
python script_construct.py

# 4. 启动 API
python api/main.py
# 或
./scripts/start_api.sh

# 5. 访问文档
open http://localhost:8000/docs
```

---

## 📡 API 端点

### Graph API

```bash
# 获取统计信息
GET /api/graph/stats

# 获取节点列表
GET /api/graph/nodes?limit=100&offset=0

# 获取单个节点
GET /api/graph/nodes/{node_id}

# 获取边列表
GET /api/graph/edges?limit=100&min_weight=0.5

# 搜索节点
GET /api/graph/search?keyword=test&limit=20

# 获取子图
GET /api/graph/subgraph?center_node_id=xxx&depth=1
```

### Query API

```bash
# 执行查询
POST /api/query/
{
  "query": "What is hypertension?",
  "mode": "hybrid",
  "top_k": 60
}

# 获取历史
GET /api/query/history?limit=10

# 清空历史
DELETE /api/query/history
```

---

## 🧪 测试

```bash
# 运行所有测试
./scripts/run_tests.sh

# 单元测试
pytest tests/test_models.py -v

# 集成测试
pytest tests/test_api_integration.py -v

# 性能测试
pytest tests/test_performance.py -v -s
```

---

## 📁 项目结构

```
api/
├── main.py              # 应用入口
├── models/              # 数据模型
├── routes/              # API 路由
├── services/            # 业务逻辑
└── middleware/          # 中间件

tests/
├── test_models.py       # 单元测试
├── test_api_integration.py  # 集成测试
└── test_performance.py  # 性能测试

docs/visualization/
├── API_QUICKSTART.md    # 快速开始
├── API_REFERENCE.md     # API 参考
├── PHASE1_SUMMARY.md    # Phase 1 总结
└── DEPLOYMENT.md        # 部署指南
```

---

## 🔧 常用命令

```bash
# 启动 API（开发模式）
python api/main.py

# 启动 API（生产模式）
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# 测试 API
python scripts/test_api.py

# 测试 GraphService
python scripts/test_graph_service.py

# 测试端点
python scripts/test_api_endpoints.py

# 测试查询
python scripts/test_query_api.py
```

---

## 🐳 Docker

```bash
# 构建镜像
docker build -t hypergraphrag-api .

# 运行容器
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY=xxx \
  hypergraphrag-api

# 使用 Docker Compose
docker-compose up -d
```

---

## 📊 性能指标

| 端点 | 目标响应时间 |
|------|------------|
| /api/graph/stats | < 1s |
| /api/graph/nodes | < 2s |
| /api/graph/edges | < 2s |
| /api/graph/search | < 3s |
| /api/query/ | < 30s |

---

## 🔗 链接

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **GitHub**: https://github.com/tao-hpu/HyperGraphRAG

---

## 📝 下一步

### Phase 2: 前端开发
- [ ] React + Vite 项目搭建
- [ ] shadcn/ui + Tailwind CSS
- [ ] Cytoscape.js 图渲染
- [ ] 交互功能实现

### Phase 3: 查询可视化
- [ ] 查询界面
- [ ] 路径可视化
- [ ] 动画效果

---

**版本**: 1.0.0 (Phase 1 完成)  
**更新**: 2025-10-21
