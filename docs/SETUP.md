# HyperGraphRAG 安装与配置指南

## 项目概述

HyperGraphRAG 是一个基于超图结构的知识检索增强生成（RAG）系统，发表于 NeurIPS 2025。

## 环境要求

- Python 3.11
- Conda（推荐用于环境管理）
- 至少 10GB 可用磁盘空间（用于安装 PyTorch 等依赖）

## 快速安装

### 1. 创建 Conda 环境

```bash
# 创建 Python 3.11 环境
conda create -n hypergraphrag python=3.11

# 激活环境
conda activate hypergraphrag
```

### 2. 安装依赖包

#### 方法一：使用兼容版本（推荐）

```bash
cd HyperGraphRAG
pip install -r requirements-compatible.txt
```

#### 方法二：使用原始 requirements

如果遇到 `torch==2.3.0` 版本不可用的错误，说明你的 PyPI 源没有该版本。请使用方法一。

```bash
pip install -r requirements.txt
```

**注意**：
- 依赖包较大（包含 PyTorch），安装可能需要 10-30 分钟
- torch 2.3.0 可能在某些环境下不可用，使用 2.0.0+ 版本也能正常运行

### 3. 配置 OpenAI API

#### 方法一：使用环境变量（推荐）

```bash
# 设置自定义 OpenAI API 地址和密钥
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_BASE_URL="https://your-custom-api-host.com/v1"
```

#### 方法二：在代码中配置

修改脚本文件，设置自定义 API 地址：

```python
import os
from hypergraphrag import HyperGraphRAG

# 配置 API 密钥和自定义地址
os.environ["OPENAI_API_KEY"] = "your_api_key_here"

# 创建 RAG 实例，指定自定义 base_url
rag = HyperGraphRAG(
    working_dir=f"expr/example",
    llm_model_kwargs={
        "base_url": "https://your-custom-api-host.com/v1",  # 自定义 API 地址
        "api_key": "your_api_key_here"  # 也可以在这里指定密钥
    }
)
```

#### 方法三：使用自定义 embedding 函数

如果需要更精细的控制，可以自定义 embedding 函数：

```python
import os
from hypergraphrag import HyperGraphRAG
from hypergraphrag.llm import openai_embedding
from functools import partial

# 设置 API 密钥
os.environ["OPENAI_API_KEY"] = "your_api_key_here"

# 创建自定义 embedding 函数
custom_embedding_func = partial(
    openai_embedding,
    base_url="https://your-custom-api-host.com/v1",
    api_key="your_api_key_here"
)

# 初始化 RAG
rag = HyperGraphRAG(
    working_dir=f"expr/example",
    embedding_func=custom_embedding_func,
    llm_model_kwargs={
        "base_url": "https://your-custom-api-host.com/v1",
        "api_key": "your_api_key_here"
    }
)
```

## 使用示例

### 1. 构建知识超图

创建文件 `script_construct.py`：

```python
import os
import json
from hypergraphrag import HyperGraphRAG

# 配置 API
os.environ["OPENAI_API_KEY"] = "your_api_key_here"

# 初始化 RAG（使用自定义 API 地址）
rag = HyperGraphRAG(
    working_dir=f"expr/example",
    llm_model_kwargs={
        "base_url": "https://your-custom-api-host.com/v1"
    }
)

# 加载文档数据
with open(f"example_contexts.json", mode="r") as f:
    unique_contexts = json.load(f)

# 插入文档并构建知识图谱
rag.insert(unique_contexts)
```

运行：

```bash
python script_construct.py
```

### 2. 查询知识库

创建文件 `script_query.py`：

```python
import os
from hypergraphrag import HyperGraphRAG

# 配置 API
os.environ["OPENAI_API_KEY"] = "your_api_key_here"

# 初始化 RAG（使用同样的工作目录）
rag = HyperGraphRAG(
    working_dir=f"expr/example",
    llm_model_kwargs={
        "base_url": "https://your-custom-api-host.com/v1"
    }
)

# 执行查询
query_text = '''How strong is the evidence supporting a systolic BP target
of 120–129 mmHg in elderly or frail patients, considering potential risks
like orthostatic hypotension?'''

result = rag.query(query_text)
print(result)
```

运行：

```bash
python script_query.py
```

## 自定义 OpenAI API 配置详解

### 配置位置说明

代码中支持在以下位置配置自定义 API：

1. **LLM 调用**：在 `llm.py:51-64` 中的 `openai_complete_if_cache` 函数
   - 支持 `base_url` 参数
   - 通过 `llm_model_kwargs` 传递

2. **Embedding 调用**：在 `llm.py:771-786` 中的 `openai_embedding` 函数
   - 支持 `base_url` 参数
   - 通过自定义 `embedding_func` 传递

### 完整配置示例

```python
import os
from hypergraphrag import HyperGraphRAG
from hypergraphrag.llm import openai_embedding
from functools import partial

# API 配置
API_KEY = "your_api_key_here"
BASE_URL = "https://your-custom-api-host.com/v1"

# 设置环境变量（作为后备）
os.environ["OPENAI_API_KEY"] = API_KEY

# 创建自定义 embedding 函数
custom_embedding = partial(
    openai_embedding,
    base_url=BASE_URL,
    api_key=API_KEY,
    model="text-embedding-3-small"  # 可选：指定模型
)

# 初始化 RAG 系统
rag = HyperGraphRAG(
    working_dir="expr/my_project",

    # 配置 embedding
    embedding_func=custom_embedding,

    # 配置 LLM
    llm_model_kwargs={
        "base_url": BASE_URL,
        "api_key": API_KEY,
    },

    # 其他可选配置
    chunk_token_size=1200,  # 文本切块大小
    chunk_overlap_token_size=100,  # 切块重叠大小
    log_level="INFO"  # 日志级别：DEBUG, INFO, WARNING, ERROR
)
```

## 主要依赖说明

```
torch==2.3.0              # 深度学习框架（约 2GB）
transformers              # HuggingFace 模型库
openai                    # OpenAI API 客户端
tiktoken                  # Token 计数工具
networkx                  # 图处理库
neo4j                     # 图数据库支持（可选）
pymongo                   # MongoDB 支持（可选）
pymilvus                  # Milvus 向量数据库（可选）
```

## 常见问题

### 1. torch 版本不可用错误

如果遇到 `ERROR: No matching distribution found for torch==2.3.0`：

```bash
# 方法一：使用兼容版本文件（推荐）
pip install -r requirements-compatible.txt

# 方法二：手动安装可用的 torch 版本
pip install torch>=2.0.0
pip install -r requirements.txt

# 方法三：使用 conda 安装 torch
conda install pytorch -c pytorch
pip install -r requirements-compatible.txt
```

### 2. Python 版本问题

项目推荐 Python 3.11，但 3.9+ 也可以运行：

```bash
# 查看当前 Python 版本
python --version

# 如果版本过低，创建新环境
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag
```

### 3. hnswlib 编译失败

如果遇到 `'iostream' file not found` 或 `Failed building wheel for hnswlib`：

**原因**：hnswlib 是 C++ 扩展库，需要编译，但系统缺少 C++ 标准库头文件。

**解决方案 A：使用 conda 安装（最简单）**

```bash
conda install -c conda-forge hnswlib -y
```

**解决方案 B：设置编译器环境变量**

```bash
export CXXFLAGS="-stdlib=libc++"
export LDFLAGS="-stdlib=libc++"
pip install hnswlib --no-cache-dir
```

**解决方案 C：跳过 hnswlib（使用替代方案）**

hnswlib 用于向量检索，可以用 nano-vectordb 替代：

```bash
# 安装除 hnswlib 外的所有依赖
pip install torch>=2.0.0 accelerate aioboto3 aiohttp graspologic nano-vectordb neo4j networkx ollama openai oracledb pymilvus pymongo pymysql pyvis sqlalchemy tenacity tiktoken transformers xxhash jsonlines nltk PyPDF2
```

**解决方案 D：重新安装 Xcode Command Line Tools**

```bash
# 删除旧的工具
sudo rm -rf /Library/Developer/CommandLineTools

# 重新安装
xcode-select --install

# 等待安装完成后，重试
export CXXFLAGS="-stdlib=libc++"
export LDFLAGS="-stdlib=libc++"
pip install hnswlib
```

### 4. API 连接错误

确认以下配置：
- API 密钥是否正确
- Base URL 是否包含 `/v1` 后缀
- 网络是否可以访问 API 地址

### 3. 内存不足

PyTorch 和模型较大，建议：
- 至少 8GB RAM
- 使用 GPU 可提升性能（可选）

### 4. 模块导入错误

```bash
# 确保在正确的环境中
conda activate hypergraphrag
python -c "from hypergraphrag import HyperGraphRAG; print('OK')"
```

## 进阶配置

### 使用其他 LLM 模型

```python
from hypergraphrag.llm import ollama_model_complete

rag = HyperGraphRAG(
    working_dir="expr/example",
    llm_model_func=ollama_model_complete,  # 使用 Ollama
    llm_model_name="llama3.2",
    llm_model_kwargs={"host": "http://localhost:11434"}
)
```

### 使用多个 API Key（负载均衡）

```python
from hypergraphrag.llm import Model, MultiModel, openai_complete_if_cache

# 配置多个模型实例
models = [
    Model(
        gen_func=openai_complete_if_cache,
        kwargs={"model": "gpt-4o-mini", "api_key": "key1", "base_url": "url1"}
    ),
    Model(
        gen_func=openai_complete_if_cache,
        kwargs={"model": "gpt-4o-mini", "api_key": "key2", "base_url": "url2"}
    ),
]

multi_model = MultiModel(models)

rag = HyperGraphRAG(
    working_dir="expr/example",
    llm_model_func=multi_model.llm_model_func
)
```

## 验证安装

运行以下测试脚本：

```python
import os
from hypergraphrag import HyperGraphRAG

os.environ["OPENAI_API_KEY"] = "your_api_key_here"

rag = HyperGraphRAG(
    working_dir="test_install",
    llm_model_kwargs={"base_url": "https://your-api.com/v1"}
)

print("✅ HyperGraphRAG 安装成功！")
```

## 参考资源

- 项目主页：https://github.com/HKUDS/HyperGraphRAG
- 论文链接：https://arxiv.org/abs/2503.21322
- 评估指南：`./evaluation/README.md`
