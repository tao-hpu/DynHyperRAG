# HyperGraphRAG 项目设计与架构详解

> 本文档详细介绍 HyperGraphRAG 项目的核心设计思想、架构巧妙之处以及实现原理，帮助读者快速理解项目的作用与构思。

---

## 📚 目录

- [项目简介](#项目简介)
- [核心概念](#核心概念)
- [技术架构](#技术架构)
- [设计巧思](#设计巧思)
- [工作流程](#工作流程)
- [与传统 RAG 的区别](#与传统-rag-的区别)
- [适用场景](#适用场景)

---

## 项目简介

### 🎯 这是什么？

**HyperGraphRAG** 是一个基于**超图结构**的检索增强生成（RAG）系统，由北京邮电大学等机构联合开发，论文被 **NeurIPS 2025** 收录。

### 💡 解决什么问题？

传统 RAG 系统在处理复杂知识时存在局限：
- **传统图 RAG**: 只能表示**二元关系**（实体A → 关系 → 实体B）
- **向量 RAG**: 缺乏结构化知识，检索精度有限

**HyperGraphRAG** 通过**超图**表示多元关系，一个超边可以同时连接多个实体，更符合真实世界的知识结构。

### 📄 论文信息

- **标题**: HyperGraphRAG: Retrieval-Augmented Generation via Hypergraph-Structured Knowledge Representation
- **会议**: NeurIPS 2025
- **论文**: [arXiv:2503.21322](https://arxiv.org/abs/2503.21322)
- **作者**: 罗浩然等（北京邮电大学、新加坡南洋理工大学）

---

## 核心概念

### 1. 什么是超图？

#### 传统图 vs 超图

```
传统图（二元关系）:
实体A ──关系1──> 实体B
实体B ──关系2──> 实体C

超图（多元关系）:
              超边1（知识片段）
             /    |    \
        实体A  实体B  实体C

              超边2
             /    \
        实体B  实体D
```

#### 举个例子

**文本**: "张三、李四和王五在北京成立了一家科技公司"

**传统图表示**（需要拆分为多个二元关系）:
- 张三 → 参与 → 成立公司
- 李四 → 参与 → 成立公司
- 王五 → 参与 → 成立公司
- 公司 → 位于 → 北京

**超图表示**（一个超边完整描述）:
```
超边: "张三、李四和王五在北京成立了一家科技公司"
  ├─ 张三
  ├─ 李四
  ├─ 王五
  ├─ 北京
  └─ 科技公司
```

### 2. 为什么用超图？

| 优势 | 说明 | 示例 |
|------|------|------|
| **语义完整** | 保留原始文本的完整语义 | 不需要拆分复杂句子 |
| **多元关系** | 一个事件涉及多个实体 | "三国会谈"涉及3个国家 |
| **减少歧义** | 避免拆分导致的信息丢失 | "A、B、C共同完成X"不会误读为单独行为 |
| **检索精准** | 可以同时检索相关的多个实体 | 查询"合作项目"能找到所有参与者 |

---

## 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户输入文档                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │  1. 文档分块 (Chunking)        │
         │  - 按 token 大小切分           │
         │  - 保持语义完整性               │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │  2. 实体与超边提取 (LLM)       │
         │  - 识别实体                    │
         │  - 提取知识片段作为超边         │
         │  - 建立实体-超边连接            │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │  3. 知识存储                   │
         │  ┌─────────────────────────┐  │
         │  │ NetworkX (图存储)        │  │
         │  │ - 实体节点 (role=entity) │  │
         │  │ - 超边节点 (role=hyperedge)│ │
         │  └─────────────────────────┘  │
         │  ┌─────────────────────────┐  │
         │  │ 向量数据库                │  │
         │  │ - 实体向量               │  │
         │  │ - 超边向量               │  │
         │  │ - 文本块向量             │  │
         │  └─────────────────────────┘  │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │  4. 查询处理                   │
         │  - 提取查询关键词               │
         │  - 向量检索相关实体和超边        │
         │  - 构建上下文                   │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │  5. 生成答案 (LLM)             │
         │  - 基于检索到的知识             │
         │  - 生成准确回答                 │
         └───────────────────────────────┘
```

### 核心组件

#### 1. 超图存储层

**文件**: `hypergraphrag/storage.py`

使用 **NetworkX** (普通图库) + **自定义数据结构** 实现超图：

```python
# 实体节点
{
    "role": "entity",
    "entity_name": "张三",
    "entity_type": "人物",
    "description": "某公司创始人",
    "source_id": "chunk-001"
}

# 超边节点
{
    "role": "hyperedge",
    "hyperedge_name": "<hyperedge>张三、李四成立公司",
    "weight": 1.0,
    "source_id": "chunk-001"
}

# 连接边
实体节点 ──边──> 超边节点
```

#### 2. LLM 调用层

**文件**: `hypergraphrag/llm.py`

支持多种 LLM 后端：
- ✅ OpenAI (GPT-4o, GPT-4o-mini)
- ✅ Azure OpenAI
- ✅ Ollama (本地部署)
- ✅ HuggingFace 模型
- ✅ AWS Bedrock
- ✅ 智谱 AI (ChatGLM)

**两个核心功能**：
1. **文本生成**: 提取实体、回答问题
2. **向量嵌入**: 将文本转为向量用于检索

#### 3. 知识提取层

**文件**: `hypergraphrag/operate.py`

核心函数：
```python
async def extract_entities(
    chunks: dict,
    knowledge_graph_inst: BaseGraphStorage,
    entity_vdb: BaseVectorStorage,
    hyperedge_vdb: BaseVectorStorage,
    global_config: dict,
) -> BaseGraphStorage:
    """
    从文本块中提取：
    1. 实体 (entities)
    2. 超边 (hyperedges) - 知识片段
    3. 实体-超边连接关系
    """
```

#### 4. 查询处理层

**文件**: `hypergraphrag/operate.py`

支持三种查询模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **local** | 基于实体的局部检索 | 查询具体实体信息 |
| **global** | 基于超边的全局检索 | 查询宏观知识、关系 |
| **hybrid** | 混合检索 | 复杂查询（**推荐**） |

---

## 设计巧思

### 🎨 巧思1: 用普通图模拟超图

**问题**: Python 没有成熟的超图库，现有的 HyperNetX、DHG 等要么太重，要么不适配 RAG 场景。

**解决方案**: 用 **二部图 (Bipartite Graph)** 模拟超图

```python
# 超图的数学定义
H = (V, E)
V = 节点集合
E = 超边集合，每条超边连接多个节点

# 二部图模拟
G = (V1 ∪ V2, E)
V1 = 实体节点 (role=entity)
V2 = 超边节点 (role=hyperedge)
E = 实体与超边之间的连接
```

**示意图**:

```
真实的超图:
         超边1
        /  |  \
    实体A 实体B 实体C

二部图表示:
实体A ────┐
实体B ────┼──── 超边1 (作为节点)
实体C ────┘
```

**代码实现** (`hypergraphrag/operate.py:134-164`):

```python
async def _merge_hyperedges_then_upsert(
    hyperedge_name: str,
    nodes_data: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
):
    # 1. 将超边作为一个特殊节点插入图中
    node_data = dict(
        role="hyperedge",  # 标记为超边
        weight=weight,
        source_id=source_id,
    )
    await knowledge_graph_inst.upsert_node(
        hyperedge_name,
        node_data=node_data,
    )
```

**优势**:
- ✅ 复用 NetworkX 的成熟功能（遍历、度计算等）
- ✅ 无需引入新依赖
- ✅ 代码简洁，易于维护
- ✅ 与 LightRAG 基础设施完全兼容

---

### 🎨 巧思2: 继承 LightRAG 架构

**问题**: 从零开发 RAG 系统工作量大，且容易有 bug。

**解决方案**: 基于 [LightRAG](https://github.com/HKUDS/LightRAG) 改进

```
LightRAG (轻量级图 RAG)
    ↓ 继承基础设施
    ├─ NetworkX 图存储
    ├─ 向量检索机制
    ├─ 文本分块策略
    └─ LLM 调用框架

    ↓ 扩展创新点
HyperGraphRAG
    ├─ 超图结构 (二部图模拟)
    ├─ 多元关系表示
    ├─ 混合检索策略
    └─ NeurIPS 2025 论文算法
```

**改动点**:

| 组件 | LightRAG | HyperGraphRAG |
|------|----------|---------------|
| 图结构 | 实体→关系→实体 | 实体→超边←实体 |
| 节点类型 | 仅实体 | 实体 + 超边 |
| 提取方式 | 二元关系提取 | 知识片段提取 |
| 检索策略 | 局部/全局 | 局部/全局/混合 |

**优势**:
- ✅ 站在巨人的肩膀上
- ✅ 快速迭代，降低风险
- ✅ 复用社区生态
- ✅ 学术创新 + 工程务实

---

### 🎨 巧思3: 三层向量检索

**问题**: 只用图结构检索不够精准，纯向量检索丢失结构信息。

**解决方案**: **图结构 + 向量检索** 混合

```python
# 三个向量数据库
self.entities_vdb        # 实体向量
self.hyperedges_vdb      # 超边向量
self.chunks_vdb          # 原始文本块向量
```

**检索流程**:

```
用户查询: "张三参与了哪些项目？"
    │
    ├─> 向量检索相似实体
    │   └─> ["张三", "李四", ...]
    │
    ├─> 图结构遍历
    │   └─> 获取张三相关的超边
    │       └─> ["<hyperedge>张三、李四成立公司", ...]
    │
    └─> 回溯原始文本
        └─> 找到来源文本块作为证据
```

**优势**:
- ✅ **语义检索**: 向量能找到相似但用词不同的内容
- ✅ **结构检索**: 图能找到相关联的实体和关系
- ✅ **证据追溯**: 原始文本提供可验证性

---

### 🎨 巧思4: 提示工程（Prompt Engineering）

**文件**: `hypergraphrag/prompt.py`

项目内置精心设计的 Prompt 模板：

```python
PROMPTS = {
    "entity_extraction": """
    -Goal-
    Given a text document, identify all entities and their relationships.

    -Steps-
    1. Identify all entities with types and descriptions
    2. Identify knowledge fragments that connect multiple entities
    3. Format as (hyper-relation|knowledge_fragment|weight)
           followed by (entity|name|type|description|weight)
    ...
    """,

    "rag_response": """
    ---Role---
    You are an expert answering questions based on the given context.

    ---Goal---
    Generate a comprehensive answer using ONLY the provided context.

    ---Context---
    {context_data}

    ---Target response length and format---
    {response_type}
    ...
    """
}
```

**设计亮点**:
- 🎯 **Few-shot 示例**: 内置示例指导 LLM 输出格式
- 🌍 **多语言支持**: 可配置中英文 Prompt
- 📝 **结构化输出**: 强制 LLM 按固定格式输出，便于解析
- 🔄 **迭代提取**: 使用 "gleaning" 机制多轮提取，提高召回率

---

### 🎨 巧思5: 灵活的存储后端

**问题**: 不同用户有不同的存储需求（性能、成本、部署方式）。

**解决方案**: 抽象存储接口 + 多种实现

```python
# 基类定义 (hypergraphrag/base.py)
class BaseKVStorage:      # 键值存储
class BaseVectorStorage:  # 向量存储
class BaseGraphStorage:   # 图存储
```

**支持的存储后端**:

| 存储类型 | 本地方案 | 云端方案 | 企业方案 |
|---------|---------|---------|---------|
| **图存储** | NetworkX | Neo4j | Neo4j, Oracle |
| **向量存储** | NanoVectorDB | Milvus, Chroma | TiDB Vector, Oracle |
| **KV存储** | JSON 文件 | MongoDB | TiDB, Oracle |

**使用示例**:

```python
# 默认：本地文件存储
rag = HyperGraphRAG(
    kv_storage="JsonKVStorage",
    vector_storage="NanoVectorDBStorage",
    graph_storage="NetworkXStorage"
)

# 生产环境：分布式存储
rag = HyperGraphRAG(
    kv_storage="MongoKVStorage",
    vector_storage="MilvusVectorDBStorge",
    graph_storage="Neo4JStorage"
)
```

**优势**:
- ✅ 快速原型开发（本地 JSON）
- ✅ 生产环境部署（云数据库）
- ✅ 自由切换，无需改代码

---

### 🎨 巧思6: 配置管理

**文件**: `config.py`

**问题**: 硬编码配置难以管理，容易泄露 API Key。

**解决方案**: `.env` 文件 + 配置类

```python
# .env 文件
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini

# config.py 自动加载
class Config:
    def __init__(self):
        self._load_env_file()
        self.openai_api_key = self._get_env("OPENAI_API_KEY")
        self.embedding_model = self._get_env("EMBEDDING_MODEL")
```

**优势**:
- ✅ 分离配置和代码
- ✅ 避免 API Key 泄露到 Git
- ✅ 环境变量优先级（支持 Docker、CI/CD）
- ✅ 友好的错误提示

---

## 工作流程

### 完整流程图

```
┌────────────────────────────────────────────────────────────┐
│                    阶段1: 知识图谱构建                       │
└────────────────────────────────────────────────────────────┘

输入文档 (example_contexts.json)
    │
    ▼
[文档分块]
    │ 按 1200 tokens 切分，重叠 100 tokens
    │
    ▼
[LLM 实体提取]
    │ Prompt: "提取实体和知识片段"
    │ 输出: (hyper-relation|片段|权重)
    │      (entity|名称|类型|描述|权重)
    │
    ▼
[构建超图]
    │ ┌──────────────┐
    │ │ 实体节点     │ role=entity
    │ │ 超边节点     │ role=hyperedge
    │ │ 连接边       │ 实体 ─── 超边
    │ └──────────────┘
    │
    ▼
[向量化]
    │ ┌──────────────┐
    │ │ 实体 → 向量  │
    │ │ 超边 → 向量  │
    │ │ 文本 → 向量  │
    │ └──────────────┘
    │
    ▼
[持久化存储]
    ├─ expr/example/kv_store_*.json        (键值数据)
    ├─ expr/example/vdb_*.json             (向量索引)
    └─ expr/example/graph_*.graphml        (图结构)

┌────────────────────────────────────────────────────────────┐
│                    阶段2: 知识检索与回答                      │
└────────────────────────────────────────────────────────────┘

用户查询: "张三参与了哪些项目？"
    │
    ▼
[关键词提取]
    │ LLM 提取: 低层关键词 (实体名)
    │          高层关键词 (知识片段)
    │
    ▼
[混合检索]
    │
    ├─ Local Search (实体级)
    │  │ 1. 向量检索相似实体
    │  │ 2. 获取实体描述
    │  │ 3. 遍历相关超边
    │  │ 4. 回溯原始文本
    │  │
    │  └─> 局部上下文
    │
    ├─ Global Search (超边级)
    │  │ 1. 向量检索相似超边
    │  │ 2. 获取超边连接的实体
    │  │ 3. 回溯原始文本
    │  │
    │  └─> 全局上下文
    │
    └─> 合并去重
    │
    ▼
[上下文构建]
    │ -----Entities-----
    │ id | entity | type | description
    │ -----Relationships-----
    │ id | hyperedge | related_entities
    │ -----Sources-----
    │ id | content
    │
    ▼
[LLM 生成答案]
    │ System Prompt + 上下文 + 用户问题
    │
    ▼
最终答案
```

### 时间复杂度分析

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 文档分块 | O(n) | n = 文档总字符数 |
| 实体提取 | O(k) | k = 文本块数量（并发） |
| 向量检索 | O(log m) | m = 向量总数（近似最近邻） |
| 图遍历 | O(d) | d = 节点平均度数 |

---

## 与传统 RAG 的区别

### 对比表

| 维度 | 传统向量 RAG | 图 RAG (LightRAG) | 超图 RAG (HyperGraphRAG) |
|------|-------------|-------------------|------------------------|
| **知识表示** | 向量 | 实体-关系图 | 实体-超边图 |
| **关系类型** | 无结构 | 二元关系 | 多元关系 |
| **检索方式** | 纯向量相似度 | 图遍历 + 向量 | 超图遍历 + 向量 |
| **语义保留** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **复杂查询** | ❌ 弱 | ✅ 较强 | ✅ 强 |
| **可解释性** | ❌ 黑盒 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **推理能力** | ❌ 无 | ⭐⭐ | ⭐⭐⭐⭐ |

### 具体案例

**查询**: "张三、李四和王五合作过什么项目？"

#### 传统向量 RAG
```
1. 向量检索 top-k 相似文本块
2. 直接送给 LLM 生成答案

问题：
- 可能检索不到同时包含三个人的文本
- 无法理解"合作"关系
```

#### 图 RAG (LightRAG)
```
1. 识别实体: 张三、李四、王五
2. 查询图: 张三→项目A, 李四→项目A, 王五→项目B

问题：
- 无法判断是否"共同"参与
- 三个独立的二元关系
```

#### 超图 RAG (HyperGraphRAG)
```
1. 识别实体: 张三、李四、王五
2. 检索超边: 找到连接这三人的超边
   超边1: "<hyperedge>张三、李四、王五共同创立X公司"
3. 获取完整语义和原始文本

优势：
✅ 明确表示"共同"关系
✅ 完整保留原始语义
✅ 结果准确可解释
```

---

## 适用场景

### ✅ 适合的场景

#### 1. 多方协作分析
- **法律文书**: 多方合同、涉及多个主体的案件
- **商业情报**: 多公司合作、产业链分析
- **学术研究**: 多作者论文、跨学科研究

**为什么**: 超边天然表示多方关系

#### 2. 事件理解
- **新闻分析**: 一个事件涉及多个实体
- **历史研究**: 复杂历史事件的多方参与
- **医疗诊断**: 多症状、多病因的关联

**为什么**: 事件是天然的超边

#### 3. 复杂问答
- **多跳推理**: "A和B的共同朋友是谁？"
- **关系推理**: "哪些项目同时涉及技术和商业？"
- **场景理解**: "在什么情况下X和Y会同时出现？"

**为什么**: 超图的全局视角支持复杂推理

#### 4. 知识密集型领域
- **医学**: 疾病-症状-治疗的多元关系
- **金融**: 多主体交易关系
- **科研**: 多因素实验结果

**为什么**: 知识往往是多元的

### ❌ 不适合的场景

#### 1. 简单 QA
- **FAQ 问答**: 简单的一问一答
- **文档检索**: 只需要找到相关段落

**为什么**: 大材小用，传统 RAG 更快

#### 2. 实时性要求极高
- **在线客服**: 需要毫秒级响应
- **流式生成**: 需要逐字输出

**为什么**: 超图构建和检索有一定开销

#### 3. 文档数量极少
- **单文档**: 只有几页文档
- **小规模**: 少于 100 条文本

**为什么**: 超图优势无法体现

---

## 性能优化建议

### 1. 构建阶段优化

```python
# 1. 增加并发数
rag = HyperGraphRAG(
    llm_model_max_async=32,      # LLM 并发数
    embedding_func_max_async=16, # embedding 并发数
)

# 2. 调整分块大小
rag = HyperGraphRAG(
    chunk_token_size=800,         # 更小的块 → 更快
    chunk_overlap_token_size=50,  # 更小的重叠
)

# 3. 减少提取轮次
rag = HyperGraphRAG(
    entity_extract_max_gleaning=1,  # 默认2轮，改为1轮
)
```

### 2. 查询阶段优化

```python
# 1. 减少检索数量
result = rag.query(query, param=QueryParam(
    top_k=30,  # 默认 60，可减少到 30
))

# 2. 限制上下文长度
result = rag.query(query, param=QueryParam(
    max_token_for_text_unit=2000,    # 原始文本
    max_token_for_local_context=2000, # 局部上下文
    max_token_for_global_context=2000,# 全局上下文
))

# 3. 使用单一模式
result = rag.query(query, param=QueryParam(
    mode="local",  # 只用局部检索，不用混合
))
```

### 3. 存储优化

```python
# 生产环境使用高性能存储
rag = HyperGraphRAG(
    kv_storage="MongoKVStorage",          # MongoDB 替代 JSON
    vector_storage="MilvusVectorDBStorge", # Milvus 替代 NanoVectorDB
    graph_storage="Neo4JStorage",          # Neo4j 替代 NetworkX
)
```

---

## 扩展阅读

### 相关论文
1. **HyperGraphRAG** (NeurIPS 2025): [arXiv:2503.21322](https://arxiv.org/abs/2503.21322)
2. **LightRAG**: [GitHub](https://github.com/HKUDS/LightRAG)
3. **GraphRAG** (Microsoft): [arXiv:2404.16130](https://arxiv.org/abs/2404.16130)

### 超图理论
- Berge, C. (1973). *Graphs and Hypergraphs*
- Feng, Y. et al. (2019). *Hypergraph Neural Networks*

### RAG 技术
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*
- Gao, Y. et al. (2023). *Retrieval-Augmented Generation for Large Language Models: A Survey*

---

## 总结

HyperGraphRAG 的核心价值：

1. **学术创新**: NeurIPS 2025 论文，超图理论在 RAG 的首次系统应用
2. **工程务实**: 基于 LightRAG，复用成熟组件，降低开发风险
3. **巧妙实现**: 用二部图模拟超图，既保留理论优势，又保持工程简洁
4. **灵活扩展**: 支持多种 LLM、多种存储后端、多种检索策略
5. **实用性强**: 适合复杂知识场景，提供更准确的检索和推理

**一句话总结**: 这是一个将**前沿学术理论**（超图 RAG）与**成熟工程实践**（LightRAG + NetworkX）完美结合的项目，实现了**1+1>2** 的效果！

---

## 联系方式

- **项目地址**: [GitHub](https://github.com/LHRLAB/HyperGraphRAG)
- **论文地址**: [arXiv:2503.21322](https://arxiv.org/abs/2503.21322)
- **问题反馈**: haoran.luo@ieee.org

---

**最后更新**: 2025-10-12
