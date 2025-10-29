# 数据迁移指南

## 概述

本指南说明如何从医疗示例数据迁移到 CAIL2019 法律数据集和 PubMed/AMiner 学术数据集。

## 当前状态

- **可视化界面**：已完成，支持任意领域数据
- **当前数据**：医疗领域示例数据（`expr/example/`）
- **数据格式**：HyperGraphRAG 标准格式

## 迁移策略

### 选项 1：完全替换（推荐用于论文实验）

**适用场景**：专注于法律领域研究，不需要保留医疗数据

```bash
# 1. 备份原数据
mv expr/example expr/example_medical_backup

# 2. 下载 CAIL2019
wget https://cail.oss-cn-qingdao.aliyuncs.com/CAIL2019.zip
unzip CAIL2019.zip -d data/cail2019_raw/

# 3. 清洗数据
python -m hypergraphrag.data.cail2019_loader \
  --input data/cail2019_raw/ \
  --output data/cail2019_cleaned/

# 4. 构建知识图谱
python script_construct.py \
  --input data/cail2019_cleaned/train.json \
  --output expr/cail2019/ \
  --domain legal

# 5. 更新配置
# 修改 .env 或 config.py
WORKING_DIR=expr/cail2019
DOMAIN=legal

# 6. 启动服务
python -m uvicorn api.main:app --reload
cd web_ui && pnpm dev
```

### 选项 2：多数据集并存（推荐用于开发调试）

**适用场景**：需要在不同领域间切换，保留 demo 数据

```bash
# 目录结构
expr/
├── medical/          # 医疗数据（demo）
├── cail2019/         # 法律数据（主实验）
└── pubmed/           # 学术数据（对比实验）

# 1. 重命名原数据
mv expr/example expr/medical

# 2. 构建 CAIL2019
mkdir -p expr/cail2019
python script_construct.py \
  --input data/cail2019_cleaned/train.json \
  --output expr/cail2019/ \
  --domain legal

# 3. 构建 PubMed
mkdir -p expr/pubmed
python script_construct.py \
  --input data/pubmed_cleaned/ \
  --output expr/pubmed/ \
  --domain academic

# 4. 切换数据集（通过环境变量）
export WORKING_DIR=expr/cail2019
export DOMAIN=legal

# 或通过符号链接
ln -sf expr/cail2019 expr/current
```

## 数据集准备

### CAIL2019（法律数据）

**1. 下载数据**
```bash
# 官方下载地址
wget https://cail.oss-cn-qingdao.aliyuncs.com/CAIL2019.zip

# 或从 GitHub
git clone https://github.com/alumik/cail2019.git
```

**2. 数据格式**
```json
{
  "fact": "2015年11月5日上午，被告人胡某在...",
  "meta": {
    "accusation": ["故意伤害"],
    "relevant_articles": [234],
    "term_of_imprisonment": {"death_penalty": false, "life_imprisonment": false, "imprisonment": 12}
  }
}
```

**3. 清洗脚本**
```python
from hypergraphrag.data.cail2019_loader import CAIL2019Loader

loader = CAIL2019Loader('data/cail2019_raw/')
data = loader.load_and_clean()

# 输出
# data['train']: 训练集 (70%)
# data['val']: 验证集 (15%)
# data['test']: 测试集 (15%)
```

**4. 实体类型**
- `law`: 法律名称（如"刑法"）
- `article`: 法律条款（如"第234条"）
- `court`: 法院名称
- `party`: 当事人（被告、原告）
- `crime`: 罪名（如"故意伤害罪"）
- `penalty`: 刑罚（如"有期徒刑12个月"）

### PubMed/AMiner（学术数据）

**1. 下载数据**
```bash
# PubMed
wget ftp://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed*.xml.gz

# 或 AMiner
wget https://www.aminer.cn/data/
```

**2. 数据格式**
```json
{
  "title": "Deep Learning for Natural Language Processing",
  "authors": ["John Doe", "Jane Smith"],
  "institution": "Stanford University",
  "keywords": ["deep learning", "NLP", "transformer"],
  "conference": "ACL 2023"
}
```

**3. 清洗脚本**
```python
from hypergraphrag.data.academic_loader import AcademicLoader

loader = AcademicLoader('data/pubmed_raw/')
data = loader.load_and_clean()
```

**4. 实体类型**
- `paper`: 论文标题
- `author`: 作者姓名
- `institution`: 机构名称
- `keyword`: 关键词
- `conference`: 会议/期刊名称

## 可视化界面适配

### 1. 领域配置

可视化界面已支持多领域，配置文件：`web_ui/src/config/domains.ts`

```typescript
export const DOMAIN_CONFIGS = {
  medical: { ... },
  legal: { ... },
  academic: { ... }
};
```

### 2. 切换领域

**方法 1：环境变量**
```bash
# .env
REACT_APP_DEFAULT_DOMAIN=legal
```

**方法 2：UI 选择器**（需要实现）
```typescript
// 在 web UI 中添加领域选择下拉框
<Select value={domain} onChange={setDomain}>
  <Option value="medical">医疗领域</Option>
  <Option value="legal">法律领域</Option>
  <Option value="academic">学术领域</Option>
</Select>
```

### 3. 实体类型颜色

系统会自动根据领域配置应用不同颜色：

```typescript
import { getEntityTypeColor } from '@/config/domains';

const color = getEntityTypeColor('law', 'legal'); // 返回 '#dc2626'
```

## 后端 API 适配

### 1. 多数据集支持

修改 `api/main.py` 支持数据集参数：

```python
@app.get("/api/graph/nodes")
async def get_nodes(
    dataset: str = Query("cail2019", description="数据集名称"),
    skip: int = 0,
    limit: int = 100
):
    # 根据 dataset 参数加载对应数据
    working_dir = f"expr/{dataset}"
    graph_service = GraphService(working_dir)
    return await graph_service.get_nodes(skip, limit)
```

### 2. 配置管理

```python
# config.py
DATASETS = {
    'medical': {
        'working_dir': 'expr/medical',
        'domain': 'medical',
        'entity_types': ['disease', 'symptom', 'treatment', 'drug']
    },
    'cail2019': {
        'working_dir': 'expr/cail2019',
        'domain': 'legal',
        'entity_types': ['law', 'article', 'court', 'party', 'crime', 'penalty']
    },
    'pubmed': {
        'working_dir': 'expr/pubmed',
        'domain': 'academic',
        'entity_types': ['paper', 'author', 'institution', 'keyword']
    }
}
```

## 验证迁移

### 1. 检查数据完整性

```bash
# 检查文件是否存在
ls -lh expr/cail2019/
# 应该看到：
# - kv_store_*.json
# - vdb_*.json
# - graph_chunk_entity_relation.graphml

# 检查数据统计
python -c "
from hypergraphrag import HyperGraphRAG
rag = HyperGraphRAG(working_dir='expr/cail2019')
print(f'Entities: {len(rag.entities_vdb.client_storage)}')
print(f'Hyperedges: {len(rag.hyperedges_vdb.client_storage)}')
"
```

### 2. 测试查询

```bash
# 测试法律查询
python script_query.py \
  --working_dir expr/cail2019 \
  --query "故意伤害罪的量刑标准是什么？"

# 测试学术查询
python script_query.py \
  --working_dir expr/pubmed \
  --query "深度学习在自然语言处理中的应用"
```

### 3. 测试可视化

```bash
# 启动后端
python -m uvicorn api.main:app --reload --port 3401

# 启动前端
cd web_ui && pnpm dev

# 访问 http://localhost:3400
# 检查：
# - 节点类型是否正确（law, article, court 等）
# - 颜色是否正确应用
# - 查询功能是否正常
```

## 常见问题

### Q1: 医疗数据还能用吗？

**A**: 可以！有两个选择：
1. 保留在 `expr/medical/` 作为 demo
2. 通过数据集切换功能随时切换回去

### Q2: 可视化界面需要重新开发吗？

**A**: 不需要！只需要：
1. 更新领域配置（已完成）
2. 切换数据源（环境变量或 API 参数）

### Q3: 如何同时展示多个数据集？

**A**: 在 UI 中添加数据集选择器：
```typescript
const [dataset, setDataset] = useState('cail2019');

// 查询时带上 dataset 参数
fetch(`/api/graph/nodes?dataset=${dataset}`)
```

### Q4: 数据迁移会影响已有功能吗？

**A**: 不会！因为：
- 数据格式相同（都是超图）
- API 接口不变
- 只是实体类型和内容不同

## 时间规划

- **Week 11**：CAIL2019 数据准备和迁移
- **Week 12**：PubMed 数据准备
- **Week 13-14**：在新数据上运行实验
- **Week 15-16**：结果分析和论文撰写

---

**最后更新**：2025-01-30
