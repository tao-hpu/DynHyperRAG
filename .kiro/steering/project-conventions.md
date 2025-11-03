---
inclusion: always
---

# HyperGraphRAG 项目规范

## 包管理器

**本项目使用 pnpm 作为 Node.js 包管理器**

### 前端开发命令

```bash
# 安装依赖
cd web_ui
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build

# 运行测试
pnpm test
```

### 重要提示

- ❌ 不要使用 `npm` 或 `yarn`
- ✅ 始终使用 `pnpm`
- 原因：pnpm 更快、更节省磁盘空间、依赖管理更严格

## 后端开发

### Python 环境

```bash
# 使用 Python 3.10+
python3 --version

# 安装依赖
pip install -r requirements.txt

# 启动 API 服务器
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload
```

## 数据结构说明

### 超图存储格式

HyperGraphRAG 使用**二部图（Bipartite Graph）**结构：

- **实体节点（Entity）**：`role="entity"`，有 `entity_type` 字段
- **超边节点（Hyperedge）**：`role="hyperedge"`，标签通常是 `<hyperedge>"描述文本"`
- **连接方式**：实体 ↔ 超边 ↔ 实体（没有直接的实体-实体边）

### 可视化策略

当前实现将二部图转换为普通图：
- 只显示实体节点
- 将超边转换为实体间的边
- 保留超边信息在边的 `description` 和 `entities` 字段

详见：`docs/visualization/HYPERGRAPH_VISUALIZATION_STRATEGIES.md`

## 端口配置

- **后端 API**：3401
- **前端开发服务器**：3400（Vite 默认）
- **前端生产环境**：80（Nginx）

## 代码风格

### TypeScript/React

- 使用 TypeScript strict 模式
- 组件使用函数式组件 + Hooks
- 状态管理使用 Zustand
- 样式使用 Tailwind CSS

### Python

- 使用 async/await 异步编程
- 类型注解（Type Hints）
- Pydantic 数据验证
- FastAPI 路由规范

## 文件结构

```
HyperGraphRAG/
├── api/                    # 后端 API
│   ├── main.py            # FastAPI 入口
│   ├── routes/            # API 路由
│   ├── services/          # 业务逻辑
│   └── models/            # 数据模型
├── web_ui/                # 前端应用
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── services/      # API 客户端
│   │   ├── stores/        # 状态管理
│   │   └── types/         # TypeScript 类型
│   ├── package.json
│   └── pnpm-lock.yaml     # pnpm 锁文件
├── hypergraphrag/         # 核心库
├── examples/              # 示例代码和配置文件
├── tests/                 # 测试文件
├── scripts/               # 构建和工具脚本
├── outputs/               # 生成的图片、报告等输出文件
├── docs/                  # 文档
│   └── summaries/         # 任务总结文档
├── expr/                  # 实验数据和配置
├── data/                  # 数据文件
├── logs/                  # 日志文件
└── reports/               # 分析报告
```

### 文件组织规范

- **示例文件**：所有 `example_*.py` 和相关配置文件放在 `examples/` 目录
- **测试文件**：所有 `test_*.py` 文件放在 `tests/` 目录
- **脚本文件**：构建、部署等脚本放在 `scripts/` 目录
- **输出文件**：生成的图片、JSON、CSV 等结果文件放在 `outputs/` 目录
- **文档总结**：任务总结等文档放在 `docs/summaries/` 目录

**重要**：新增文件时请按照上述规范放置，避免根目录混乱。

## Git 提交规范

使用 Conventional Commits：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具配置
```

示例：
```bash
git commit -m "feat: add hypergraph bipartite visualization"
git commit -m "fix: resolve empty entity type issue"
git commit -m "docs: add visualization strategies guide"
```
