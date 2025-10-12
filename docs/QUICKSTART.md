# HyperGraphRAG 快速启动指南

## 📋 前置要求

- Python 3.11
- Conda 环境管理器

## 🚀 快速开始（5 步骤）

### 1️⃣ 创建并激活环境

```bash
# 创建 Python 3.11 环境
conda create -n hypergraphrag python=3.11

# 激活环境
conda activate hypergraphrag
```

### 2️⃣ 安装依赖

```bash
cd HyperGraphRAG
pip install -r requirements.txt
```

> ⏱️ 安装时间：约 10-30 分钟（包含 PyTorch 等大型依赖）

### 3️⃣ 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置
nano .env  # 或使用任何文本编辑器
```

在 `.env` 文件中配置：

```bash
# OpenAI API 配置
OPENAI_API_KEY=你的API密钥
OPENAI_BASE_URL=https://你的API地址.com/v1

# 可选配置
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

### 4️⃣ 构建知识超图

```bash
python script_construct.py
```

预期输出：
```
🔧 Loading configuration...
✅ Loaded configuration from .env
✅ Configuration validated successfully
   API Base URL: https://你的API地址.com/v1
   ...
⚙️  Building knowledge hypergraph...
✅ Knowledge hypergraph construction completed!
```

### 5️⃣ 查询知识库

```bash
python script_query.py
```

预期输出：
```
🔧 Loading configuration...
🚀 Initializing HyperGraphRAG...
🔍 Querying knowledge base...

📝 Query Result:
================================================================================
[查询结果将在这里显示]
================================================================================
```

## 🧪 验证安装

运行配置测试脚本：

```bash
python config.py
```

预期输出：
```
✅ Loaded configuration from .env
✅ Configuration validated successfully
   API Base URL: https://你的API地址.com/v1
   Embedding Model: text-embedding-3-small
   LLM Model: gpt-4o-mini

📋 Current Configuration:
   API Key: sk-xxxxx...xxxx
   Base URL: https://你的API地址.com/v1
   Embedding Model: text-embedding-3-small
   LLM Model: gpt-4o-mini
```

## 📁 项目结构

```
HyperGraphRAG/
├── .env                      # 配置文件（需要创建，不会提交到 git）
├── .env.example              # 配置文件示例
├── config.py                 # 配置加载器
├── script_construct.py       # 构建知识超图脚本
├── script_query.py           # 查询脚本
├── example_contexts.json     # 示例文档数据
├── requirements.txt          # Python 依赖
└── expr/                     # 工作目录（自动创建）
    └── example/              # 示例项目的数据存储
```

## 🔧 配置说明

### 必需配置

| 参数 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-xxx...` |
| `OPENAI_BASE_URL` | API 地址 | `https://api.openai.com/v1` |

### 可选配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `EMBEDDING_MODEL` | Embedding 模型名称 | `text-embedding-3-small` |
| `LLM_MODEL` | 大语言模型名称 | `gpt-4o-mini` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 💡 使用自定义数据

### 准备数据

创建你自己的 JSON 文件（格式参考 `example_contexts.json`）：

```json
[
  "你的第一段文本内容...",
  "你的第二段文本内容...",
  "更多文本..."
]
```

### 修改脚本

编辑 `script_construct.py`，修改以下内容：

```python
# 修改工作目录名称
rag = HyperGraphRAG(
    working_dir="expr/my_project",  # 改为你的项目名
    ...
)

# 修改数据文件路径
with open("my_data.json", mode="r", encoding="utf-8") as f:
    unique_contexts = json.load(f)
```

## 🎯 进阶功能

### 查询模式选择

在 `script_query.py` 中可以选择不同的查询模式：

```python
from hypergraphrag import QueryParam

result = rag.query(query_text, param=QueryParam(
    mode="hybrid",    # 可选: local, global, hybrid, naive
    top_k=60,         # 检索数量
    max_token_for_text_unit=4000,       # 原始文本 token 数
    max_token_for_local_context=4000,   # 实体描述 token 数
    max_token_for_global_context=4000   # 关系描述 token 数
))
```

### 查询模式说明

- **local**: 基于实体的本地查询
- **global**: 基于关系的全局查询
- **hybrid**: 混合模式（推荐）
- **naive**: 基础向量检索

## ❓ 常见问题

### 1. 配置文件未找到

```
⚠️  No .env file found
```

**解决方案**：
```bash
cp .env.example .env
# 然后编辑 .env 文件
```

### 2. API 密钥未配置

```
ValueError: OPENAI_API_KEY is not configured properly
```

**解决方案**：检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确设置

### 3. hnswlib 编译失败

```
fatal error: 'iostream' file not found
ERROR: Failed building wheel for hnswlib
```

**原因**：hnswlib 需要编译 C++ 扩展，但 C++ 标准库头文件缺失。

**解决方案**：

```bash
# 方案 1：设置编译器标志后安装
export CXXFLAGS="-stdlib=libc++"
export LDFLAGS="-stdlib=libc++"
pip install hnswlib --no-cache-dir

# 方案 2：使用 conda 安装（推荐）
conda install -c conda-forge hnswlib -y

# 方案 3：跳过 hnswlib，安装其他依赖
pip install accelerate aioboto3 aiohttp graspologic nano-vectordb neo4j networkx ollama openai oracledb pymilvus pymongo pymysql pyvis sqlalchemy tenacity tiktoken transformers xxhash jsonlines nltk PyPDF2 torch>=2.0.0
```

**注意**：hnswlib 用于向量检索，如果无法安装，可以使用其他向量数据库（如 nano-vectordb，已包含在上面的命令中）。

### 4. 依赖包缺失

```
ModuleNotFoundError: No module named 'xxx'
```

**解决方案**：
```bash
conda activate hypergraphrag
pip install -r requirements-compatible.txt
```

### 4. 内存不足

**解决方案**：
- 减小 `chunk_token_size` 参数
- 分批处理文档
- 增加系统内存

## 📚 更多资源

- [完整安装指南](./SETUP.md)
- [项目 README](./README.md)
- [评估指南](./evaluation/README.md)
- [论文链接](https://arxiv.org/abs/2503.21322)

## 🐛 问题反馈

如遇到问题，请检查：
1. Python 版本是否为 3.11
2. 所有依赖是否安装完整
3. `.env` 配置是否正确
4. API 地址是否可访问

---

**祝使用愉快！🎉**
