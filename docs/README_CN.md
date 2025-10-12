# HyperGraphRAG 使用说明

## 项目简介

HyperGraphRAG 是一个基于超图结构的知识检索增强生成（RAG）系统，发表于 NeurIPS 2025。

## 🎯 快速开始

### 最简安装步骤

```bash
# 1. 创建环境
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API
cp .env.example .env
# 编辑 .env 填入你的 API Key 和 Host

# 4. 运行
python script_construct.py  # 构建知识图谱
python script_query.py      # 查询
```

详细步骤请查看 [快速启动指南](./QUICKSTART.md)

## 📖 配置文件

本项目使用 `.env` 文件进行配置，支持自定义 OpenAI API 地址。

### 创建配置文件

```bash
cp .env.example .env
```

### 编辑配置

```bash
# .env 文件内容
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://你的API地址.com/v1
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

## 🔑 配置说明

### 支持的配置方式

#### 方式 1：使用 .env 文件（推荐）

这是最简单的方式，所有配置都在 `.env` 文件中：

```python
from config import setup_environment
from hypergraphrag import HyperGraphRAG

config = setup_environment()
rag = HyperGraphRAG(
    working_dir="expr/example",
    llm_model_kwargs=config.get_llm_kwargs()
)
```

#### 方式 2：环境变量

```bash
export OPENAI_API_KEY="your_key"
export OPENAI_BASE_URL="https://your-host.com/v1"
python script_construct.py
```

#### 方式 3：代码中直接配置

```python
from functools import partial
from hypergraphrag import HyperGraphRAG
from hypergraphrag.llm import openai_embedding

custom_embedding = partial(
    openai_embedding,
    base_url="https://your-host.com/v1",
    api_key="your_key"
)

rag = HyperGraphRAG(
    working_dir="expr/example",
    embedding_func=custom_embedding,
    llm_model_kwargs={
        "base_url": "https://your-host.com/v1",
        "api_key": "your_key"
    }
)
```

## 📁 核心文件说明

| 文件 | 说明 |
|------|------|
| `config.py` | 配置加载器，从 .env 读取配置 |
| `script_construct.py` | 构建知识超图 |
| `script_query.py` | 查询知识库 |
| `.env.example` | 配置文件模板 |
| `.env` | 实际配置文件（需自己创建，不会提交到 git） |

## 🚀 使用示例

### 1. 构建知识图谱

```python
from config import setup_environment
from hypergraphrag import HyperGraphRAG
import json

# 加载配置
config = setup_environment()

# 初始化 RAG
rag = HyperGraphRAG(
    working_dir="expr/my_project",
    llm_model_kwargs=config.get_llm_kwargs()
)

# 加载数据
with open("your_data.json", "r") as f:
    documents = json.load(f)

# 构建图谱
rag.insert(documents)
```

### 2. 查询知识库

```python
from config import setup_environment
from hypergraphrag import HyperGraphRAG, QueryParam

config = setup_environment()

rag = HyperGraphRAG(
    working_dir="expr/my_project",
    llm_model_kwargs=config.get_llm_kwargs()
)

result = rag.query("你的问题", param=QueryParam(
    mode="hybrid",  # local, global, hybrid, naive
    top_k=60
))

print(result)
```

## 🔧 配置项详解

### LLM 配置

- `OPENAI_API_KEY`: OpenAI API 密钥（必需）
- `OPENAI_BASE_URL`: API 地址（必需），支持自定义 Host
- `LLM_MODEL`: 使用的 LLM 模型名称

### Embedding 配置

- `EMBEDDING_MODEL`: Embedding 模型名称
- 同样使用 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`

### 其他配置

- `LOG_LEVEL`: 日志级别（DEBUG, INFO, WARNING, ERROR）

## 🎓 进阶使用

### 自定义查询参数

```python
from hypergraphrag import QueryParam

param = QueryParam(
    mode="hybrid",                      # 查询模式
    top_k=60,                          # 检索数量
    max_token_for_text_unit=4000,      # 原始文本 token 限制
    max_token_for_local_context=4000,  # 实体描述 token 限制
    max_token_for_global_context=4000  # 关系描述 token 限制
)

result = rag.query("问题", param=param)
```

### 使用不同的存储后端

```python
rag = HyperGraphRAG(
    working_dir="expr/example",
    kv_storage="JsonKVStorage",      # 键值存储
    vector_storage="NanoVectorDBStorage",  # 向量存储
    graph_storage="NetworkXStorage"   # 图存储
)
```

可选的存储后端：
- KV: `JsonKVStorage`, `MongoKVStorage`, `OracleKVStorage`
- Vector: `NanoVectorDBStorage`, `MilvusVectorDBStorge`, `ChromaVectorDBStorage`
- Graph: `NetworkXStorage`, `Neo4JStorage`, `OracleGraphStorage`

## 📊 评估和测试

评估脚本位于 `evaluation/` 目录，同样支持 `.env` 配置。

## 🐛 常见问题

### Q: 如何使用自己的 OpenAI API Host？

**A**: 在 `.env` 文件中配置 `OPENAI_BASE_URL`：

```bash
OPENAI_BASE_URL=https://your-custom-host.com/v1
```

### Q: 不想用 openai_api_key.txt 文件？

**A**: 对！现在统一使用 `.env` 文件，不再需要 `openai_api_key.txt`。

### Q: 如何验证配置是否正确？

**A**: 运行测试脚本：

```bash
python config.py
```

### Q: 支持哪些 API 兼容服务？

**A**: 所有兼容 OpenAI API 格式的服务都支持，包括：
- Azure OpenAI
- 自建 OpenAI 代理
- 其他兼容服务（如 LocalAI、vLLM 等）

## 📚 文档索引

- [快速启动指南](./QUICKSTART.md) - 5 步骤开始使用
- [详细安装指南](./SETUP.md) - 完整的安装和配置说明
- [原始 README](./README.md) - 项目官方文档
- [评估指南](./evaluation/README.md) - 如何评估模型性能

## 🎉 改进说明

相比原版，本配置方案的改进：

1. ✅ 统一使用 `.env` 文件配置
2. ✅ 支持自定义 OpenAI API Host
3. ✅ 移除了 `openai_api_key.txt` 的依赖
4. ✅ 更好的配置验证和错误提示
5. ✅ 配置文件自动加载，使用更简单
6. ✅ `.env` 文件已在 `.gitignore` 中，不会泄露密钥

## 📄 License

MIT License - 详见 [LICENSE](./LICENSE) 文件

## 📮 联系方式

- 项目主页: https://github.com/HKUDS/HyperGraphRAG
- 论文: https://arxiv.org/abs/2503.21322
- 问题反馈: haoran.luo@ieee.org
