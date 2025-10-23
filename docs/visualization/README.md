# HyperGraphRAG 可视化文档

欢迎来到 HyperGraphRAG 可视化系统文档中心！

## 📚 文档导航

### 用户文档

适合最终用户和初学者：

- **[快速开始指南](./QUICKSTART.md)** - 5 分钟快速上手
  - 安装和启动
  - 界面概览
  - 基础功能
  - 常见问题

- **[功能使用教程](./TUTORIAL.md)** - 详细的功能教程
  - 探索超图
  - 执行查询
  - 分析路径
  - 自定义可视化
  - 导出和分享

- **[常见问题解答](./FAQ.md)** - 问题和解决方案
  - 安装问题
  - 使用问题
  - 性能优化
  - 故障排除

### 开发者文档

适合开发者和贡献者：

- **[架构文档](./ARCHITECTURE.md)** - 系统架构和设计
  - 整体架构
  - 后端设计
  - 前端设计
  - 数据流
  - 性能优化

- **[贡献指南](./CONTRIBUTING.md)** - 如何贡献代码
  - 开发环境设置
  - 代码规范
  - 提交规范
  - Pull Request 流程

- **[代码风格指南](./CODE_STYLE.md)** - 代码风格规范
  - Python 规范
  - TypeScript 规范
  - 命名规范
  - 最佳实践

### API 文档

适合 API 使用者：

- **[API 参考文档](../api/README.md)** - REST API 完整参考
  - 端点列表
  - 请求/响应格式
  - 错误处理
  - 使用示例

- **[交互式 API 文档](http://localhost:3401/docs)** - Swagger UI
  - 在线测试 API
  - 自动生成的文档

### 部署文档

适合运维人员：

- **[部署指南](./DEPLOYMENT.md)** - 生产环境部署
  - Docker 部署
  - Kubernetes 部署
  - 配置说明

- **[部署设置](./DEPLOYMENT_SETUP.md)** - 详细的部署步骤
  - 环境准备
  - 配置文件
  - 启动脚本

### 技术文档

深入了解技术细节：

- **[超图可视化策略](./HYPERGRAPH_VISUALIZATION_STRATEGIES.md)** - 可视化方案
  - 二部图结构
  - 转换策略
  - 实现方案

- **[Cytoscape 功能](./CYTOSCAPE_FEATURES.md)** - 图渲染引擎
  - 功能特性
  - 使用方法

- **[可视化框架对比](./VISUALIZATION_FRAMEWORK_COMPARISON.md)** - 技术选型
  - 框架对比
  - 选择理由

---

## 🚀 快速链接

### 新用户

1. 阅读 [快速开始指南](./QUICKSTART.md)
2. 跟随 [功能使用教程](./TUTORIAL.md)
3. 查看 [常见问题](./FAQ.md)

### 开发者

1. 阅读 [架构文档](./ARCHITECTURE.md)
2. 查看 [贡献指南](./CONTRIBUTING.md)
3. 遵循 [代码风格指南](./CODE_STYLE.md)

### API 用户

1. 阅读 [API 文档](../api/README.md)
2. 访问 [Swagger UI](http://localhost:3401/docs)
3. 查看示例代码

---

## 📖 文档结构

```
docs/
├── api/                          # API 文档
│   └── README.md                # API 参考文档
│
└── visualization/               # 可视化文档
    ├── README.md               # 本文件（文档导航）
    │
    ├── 用户文档/
    │   ├── QUICKSTART.md       # 快速开始
    │   ├── TUTORIAL.md         # 功能教程
    │   └── FAQ.md              # 常见问题
    │
    ├── 开发者文档/
    │   ├── ARCHITECTURE.md     # 架构文档
    │   ├── CONTRIBUTING.md     # 贡献指南
    │   └── CODE_STYLE.md       # 代码风格
    │
    ├── 部署文档/
    │   ├── DEPLOYMENT.md       # 部署指南
    │   └── DEPLOYMENT_SETUP.md # 部署设置
    │
    └── 技术文档/
        ├── HYPERGRAPH_VISUALIZATION_STRATEGIES.md
        ├── CYTOSCAPE_FEATURES.md
        └── VISUALIZATION_FRAMEWORK_COMPARISON.md
```

---

## 🎯 按角色查找文档

### 我是最终用户

**目标**：使用可视化系统探索知识图谱

**推荐阅读**：
1. [快速开始指南](./QUICKSTART.md) - 了解如何安装和使用
2. [功能使用教程](./TUTORIAL.md) - 学习各项功能
3. [常见问题](./FAQ.md) - 解决使用中的问题

### 我是前端开发者

**目标**：开发或修改前端功能

**推荐阅读**：
1. [架构文档](./ARCHITECTURE.md) - 了解前端架构
2. [代码风格指南](./CODE_STYLE.md) - TypeScript 规范
3. [贡献指南](./CONTRIBUTING.md) - 开发流程

**相关代码**：
- `web_ui/src/components/` - React 组件
- `web_ui/src/stores/` - Zustand 状态管理
- `web_ui/src/services/` - API 客户端

### 我是后端开发者

**目标**：开发或修改后端 API

**推荐阅读**：
1. [架构文档](./ARCHITECTURE.md) - 了解后端架构
2. [API 文档](../api/README.md) - API 设计
3. [代码风格指南](./CODE_STYLE.md) - Python 规范

**相关代码**：
- `api/routes/` - API 路由
- `api/services/` - 业务逻辑
- `api/models/` - 数据模型

### 我是数据科学家

**目标**：使用 API 进行数据分析

**推荐阅读**：
1. [API 文档](../api/README.md) - API 使用方法
2. [快速开始指南](./QUICKSTART.md) - 系统概览
3. [超图可视化策略](./HYPERGRAPH_VISUALIZATION_STRATEGIES.md) - 数据结构

**示例代码**：
```python
import requests

# 获取节点数据
response = requests.get('http://localhost:3401/api/graph/nodes')
nodes = response.json()

# 执行查询
query_data = {
    "query": "What is hypertension?",
    "mode": "hybrid"
}
response = requests.post('http://localhost:3401/api/query/', json=query_data)
result = response.json()
```

### 我是运维工程师

**目标**：部署和维护系统

**推荐阅读**：
1. [部署指南](./DEPLOYMENT.md) - 部署方法
2. [部署设置](./DEPLOYMENT_SETUP.md) - 详细步骤
3. [架构文档](./ARCHITECTURE.md) - 系统架构

**相关文件**：
- `docker-compose.yml` - Docker 配置
- `api/Dockerfile` - 后端镜像
- `web_ui/Dockerfile` - 前端镜像

---

## 🔍 按主题查找文档

### 安装和启动

- [快速开始 - 快速启动](./QUICKSTART.md#快速启动)
- [部署指南](./DEPLOYMENT.md)

### 基础使用

- [快速开始 - 基础功能](./QUICKSTART.md#基础功能)
- [教程 1 - 探索超图](./TUTORIAL.md#教程-1探索医疗知识图谱)

### 查询功能

- [快速开始 - 查询功能](./QUICKSTART.md#查询功能)
- [教程 2 - 执行查询](./TUTORIAL.md#教程-2执行复杂查询)
- [教程 3 - 分析路径](./TUTORIAL.md#教程-3分析查询路径)

### 自定义和配置

- [快速开始 - 高级功能](./QUICKSTART.md#高级功能)
- [教程 4 - 自定义可视化](./TUTORIAL.md#教程-4自定义可视化)

### 导出和分享

- [教程 5 - 导出和分享](./TUTORIAL.md#教程-5导出和分享)

### 性能优化

- [架构文档 - 性能优化](./ARCHITECTURE.md#性能优化)
- [教程 - 最佳实践](./TUTORIAL.md#最佳实践)

### API 使用

- [API 文档](../api/README.md)
- [Swagger UI](http://localhost:3401/docs)

### 开发和贡献

- [贡献指南](./CONTRIBUTING.md)
- [代码风格指南](./CODE_STYLE.md)
- [架构文档](./ARCHITECTURE.md)

### 故障排除

- [常见问题](./FAQ.md)
- [快速开始 - 常见问题](./QUICKSTART.md#常见问题)

---

## 💡 学习路径

### 初学者路径

```
1. 快速开始指南
   ↓
2. 功能使用教程（教程 1-2）
   ↓
3. 常见问题
   ↓
4. 高级功能（教程 3-5）
```

### 开发者路径

```
1. 快速开始指南
   ↓
2. 架构文档
   ↓
3. 代码风格指南
   ↓
4. 贡献指南
   ↓
5. 开始贡献！
```

### API 用户路径

```
1. API 文档
   ↓
2. Swagger UI 实践
   ↓
3. 集成到项目
```

---

## 📝 文档贡献

发现文档问题或想要改进？

1. 提交 Issue 描述问题
2. 或直接提交 Pull Request
3. 参考 [贡献指南](./CONTRIBUTING.md)

---

## 🔗 相关资源

### 外部文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)
- [Cytoscape.js 文档](https://js.cytoscape.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)

### 项目资源

- [GitHub 仓库](https://github.com/your-org/HyperGraphRAG)
- [Issue 追踪](https://github.com/your-org/HyperGraphRAG/issues)
- [讨论区](https://github.com/your-org/HyperGraphRAG/discussions)

---

## 📧 获取帮助

- 📖 首先查看文档
- 🔍 搜索 GitHub Issues
- 💬 在讨论区提问
- 📧 联系技术支持

---

## 📅 文档更新

- **最后更新**: 2025-10-22
- **版本**: 1.0.0

---

**祝您使用愉快！** 🎉

如有任何问题或建议，欢迎反馈！
