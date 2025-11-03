# Feedback Extractor - 反馈信号提取器

## 概述

FeedbackExtractor 是 DynHyperRAG 动态更新模块的核心组件，用于从 LLM 生成的答案中提取反馈信号，识别哪些检索到的超边实际对答案生成有贡献。

## 核心功能

### 四种提取方法

#### 1. 基于嵌入的反馈（Embedding-based）
- **原理**：计算答案与超边的语义相似度
- **优点**：鲁棒性强，能捕获语义相似性
- **适用场景**：答案改写了超边内容，但保留了语义

```python
config = {'method': 'embedding', 'similarity_threshold': 0.7}
extractor = FeedbackExtractor(embedding_func, config)
```

#### 2. 基于引用的反馈（Citation-based）
- **原理**：检测超边内容是否在答案中被直接引用
- **优点**：可解释性强，直观
- **适用场景**：答案直接引用了超边内容

```python
config = {'method': 'citation', 'citation_threshold': 0.8}
extractor = FeedbackExtractor(embedding_func, config)
```

#### 3. 混合方法（Hybrid）
- **原理**：结合嵌入和引用两种方法
- **策略**：引用优先，嵌入回退
- **适用场景**：需要平衡可解释性和鲁棒性

```python
config = {'method': 'hybrid'}
extractor = FeedbackExtractor(embedding_func, config)
```

#### 4. 基于注意力的反馈（Attention-based）⭐ 可选
- **原理**：分析 LLM 注意力权重，识别模型关注的超边
- **优点**：直接反映模型决策，最准确
- **适用场景**：LLM 支持输出注意力权重
- **要求**：需要 LLM 支持注意力权重提取

```python
config = {'method': 'attention', 'attention_threshold': 0.1}
extractor = FeedbackExtractor(embedding_func, config)

# 需要在 metadata 中提供注意力数据
metadata = {
    'hyperedge_attention': {
        'he1': 0.45,  # 高注意力
        'he2': 0.05   # 低注意力
    }
}
feedback = await extractor.extract_feedback(answer, hyperedges, metadata)
```

**详细文档**：[README_ATTENTION_FEEDBACK.md](./README_ATTENTION_FEEDBACK.md)

## 快速开始

### 基本使用

```python
from hypergraphrag.dynamic import FeedbackExtractor

# 1. 配置
config = {
    'method': 'embedding',
    'similarity_threshold': 0.7,
    'positive_feedback': 1.0,
    'negative_feedback': 0.3,
}

# 2. 创建提取器
extractor = FeedbackExtractor(embedding_func, config)

# 3. 提取反馈
answer = "Entity A and Entity B are closely related."
retrieved_hyperedges = [
    {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'},
    {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'}
]

feedback = await extractor.extract_feedback(answer, retrieved_hyperedges)
# 返回: {'he1': 0.85, 'he2': 0.3}
```

### 批量处理

```python
# 批量提取多个查询的反馈
answers = ["Answer 1", "Answer 2"]
hyperedges_list = [
    [{'id': 'he1', 'hyperedge': 'text1'}],
    [{'id': 'he2', 'hyperedge': 'text2'}]
]

feedback_list = await extractor.batch_extract_feedback(
    answers, hyperedges_list
)
```

## 配置参数

### 完整配置示例

```python
config = {
    # 提取方法
    'method': 'embedding',  # 'embedding', 'citation', 'hybrid'
    
    # 阈值设置
    'similarity_threshold': 0.7,   # 嵌入相似度阈值 (0-1)
    'citation_threshold': 0.8,     # 引用匹配阈值 (0-1)
    
    # 反馈值设置
    'positive_feedback': 1.0,      # 正面反馈（超边有用）
    'negative_feedback': 0.3,      # 负面反馈（超边无用）
    'neutral_feedback': 0.5,       # 中性反馈（不确定）
}
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `method` | str | 'embedding' | 提取方法：'embedding', 'citation', 'hybrid', 'attention' |
| `similarity_threshold` | float | 0.7 | 嵌入相似度阈值，高于此值为正面反馈 |
| `citation_threshold` | float | 0.8 | 引用匹配阈值，高于此值认为被引用 |
| `attention_threshold` | float | 0.1 | 注意力权重阈值，高于此值为正面反馈 |
| `positive_feedback` | float | 1.0 | 正面反馈值（超边有用） |
| `negative_feedback` | float | 0.3 | 负面反馈值（超边无用） |
| `neutral_feedback` | float | 0.5 | 中性反馈值（不确定） |

## 反馈信号解释

### 信号范围：0.0 - 1.0

- **0.9 - 1.0**：高度有用
  - 超边被直接引用
  - 或与答案高度相似（> 0.9）

- **0.7 - 0.9**：有用
  - 超边内容与答案相关
  - 相似度在阈值以上

- **0.5 - 0.7**：中性
  - 不确定是否有用
  - 相似度接近阈值

- **0.3 - 0.5**：可能无用
  - 相似度较低
  - 未被引用

- **0.0 - 0.3**：无用
  - 完全不相关
  - 相似度很低

## 与 WeightUpdater 集成

### 完整工作流

```python
from hypergraphrag.dynamic import FeedbackExtractor, WeightUpdater

# 1. 初始化
feedback_extractor = FeedbackExtractor(embedding_func, feedback_config)
weight_updater = WeightUpdater(graph, weight_config)

# 2. 查询和生成答案
retrieved_hyperedges = await retrieve_hyperedges(query)
answer = await generate_answer(query, retrieved_hyperedges)

# 3. 提取反馈
feedback_signals = await feedback_extractor.extract_feedback(
    answer, retrieved_hyperedges
)

# 4. 更新权重
for he_id, feedback in feedback_signals.items():
    await weight_updater.update_weights(he_id, feedback)
```

### 异步更新（推荐）

```python
# 在查询流程中异步更新，不阻塞响应
async def query_with_feedback(query):
    # 检索和生成
    hyperedges = await retrieve_hyperedges(query)
    answer = await generate_answer(query, hyperedges)
    
    # 异步更新权重（不等待完成）
    asyncio.create_task(
        update_weights_async(answer, hyperedges)
    )
    
    return answer

async def update_weights_async(answer, hyperedges):
    feedback = await feedback_extractor.extract_feedback(answer, hyperedges)
    await weight_updater.batch_update_weights([
        {'hyperedge_id': he_id, 'feedback_signal': signal}
        for he_id, signal in feedback.items()
    ])
```

## 性能优化

### 1. 答案嵌入缓存

FeedbackExtractor 自动缓存答案嵌入：

```python
# 第一次计算
feedback1 = await extractor.extract_feedback(answer, hyperedges1)

# 相同答案，使用缓存（快速）
feedback2 = await extractor.extract_feedback(answer, hyperedges2)

# 清除缓存
extractor.clear_cache()
```

### 2. 批量处理

批量处理多个查询更高效：

```python
# 并行处理多个查询
feedback_list = await extractor.batch_extract_feedback(
    answers, hyperedges_list
)
```

### 3. 性能建议

- **使用批量处理**：减少函数调用开销
- **定期清理缓存**：避免内存占用过大
- **选择合适方法**：
  - 嵌入方法：需要 embedding API 调用
  - 引用方法：纯文本处理，更快
  - 混合方法：平衡性能和准确率

## 统计和分析

### 获取统计信息

```python
# 提取器统计
stats = extractor.get_statistics()
print(f"方法: {stats['method']}")
print(f"缓存大小: {stats['cache_size']}")

# 反馈信号统计
from hypergraphrag.dynamic.feedback_extractor import compute_feedback_statistics

feedback_stats = compute_feedback_statistics(feedback_signals)
print(f"平均反馈: {feedback_stats['mean']:.3f}")
print(f"正面反馈数: {feedback_stats['positive_count']}")
print(f"负面反馈数: {feedback_stats['negative_count']}")
```

### 分布分析

```python
from hypergraphrag.dynamic.feedback_extractor import analyze_feedback_distribution

# 分析多个查询的反馈分布
distribution = analyze_feedback_distribution(feedback_list)
print(f"总反馈数: {distribution['total_feedbacks']}")
print(f"正面比例: {distribution['positive_ratio']:.2%}")
print(f"负面比例: {distribution['negative_ratio']:.2%}")
```

## 方法选择指南

### 何时使用嵌入方法？

✅ **适用场景：**
- 答案改写了超边内容
- 需要捕获语义相似性
- 有可靠的嵌入模型

❌ **不适用场景：**
- 嵌入模型质量差
- 需要严格的可解释性
- API 调用成本高

### 何时使用引用方法？

✅ **适用场景：**
- 答案直接引用超边
- 需要可解释的反馈
- 无嵌入模型或成本敏感

❌ **不适用场景：**
- 答案改写了内容
- 需要捕获语义相似性

### 何时使用混合方法？

✅ **适用场景：**
- 需要平衡准确率和可解释性
- 答案可能引用或改写超边
- 不确定哪种方法更好

✅ **推荐作为默认选择**

## 调试和故障排除

### 启用详细日志

```python
import logging
logging.getLogger('hypergraphrag').setLevel(logging.DEBUG)
```

### 常见问题

#### 1. 所有反馈都是中性值（0.5）

**可能原因：**
- 嵌入函数失败
- 超边格式不正确

**解决方法：**
```python
# 检查嵌入函数
embeddings = await embedding_func(["test"])
print(embeddings)

# 检查超边格式
print(retrieved_hyperedges[0])
# 应该包含 'id' 和 'hyperedge' 字段
```

#### 2. 引用方法检测不到引用

**可能原因：**
- 文本格式不匹配
- 阈值设置过高

**解决方法：**
```python
# 降低阈值
config['citation_threshold'] = 0.6

# 或使用混合方法
config['method'] = 'hybrid'
```

#### 3. 性能慢

**可能原因：**
- 未使用批量处理
- 嵌入 API 调用慢

**解决方法：**
```python
# 使用批量处理
feedback_list = await extractor.batch_extract_feedback(...)

# 或使用引用方法（无需 API 调用）
config['method'] = 'citation'
```

## 最佳实践

### 1. 选择合适的方法

```python
# 生产环境推荐：混合方法
config = {
    'method': 'hybrid',
    'similarity_threshold': 0.7,
    'citation_threshold': 0.8,
}
```

### 2. 异步更新权重

```python
# 不阻塞查询响应
asyncio.create_task(update_weights_async(answer, hyperedges))
```

### 3. 定期分析反馈

```python
# 定期分析反馈分布，调整阈值
stats = compute_feedback_statistics(feedback_signals)
if stats['positive_count'] < 0.1 * stats['count']:
    # 正面反馈太少，可能需要降低阈值
    logger.warning("Too few positive feedbacks, consider lowering threshold")
```

### 4. 监控性能

```python
# 监控缓存大小
if extractor.get_cache_size() > 100:
    extractor.clear_cache()
```

## 示例代码

### 完整示例：集成到查询流程

```python
from hypergraphrag.dynamic import FeedbackExtractor, WeightUpdater
import asyncio

class DynHyperRAGQuery:
    def __init__(self, graph, embedding_func):
        self.graph = graph
        
        # 初始化反馈提取器
        self.feedback_extractor = FeedbackExtractor(
            embedding_func,
            {
                'method': 'hybrid',
                'similarity_threshold': 0.7,
                'citation_threshold': 0.8,
            }
        )
        
        # 初始化权重更新器
        self.weight_updater = WeightUpdater(
            graph,
            {
                'strategy': 'ema',
                'update_alpha': 0.1,
                'decay_factor': 0.99,
            }
        )
    
    async def query(self, query_text):
        # 1. 检索超边
        retrieved_hyperedges = await self.retrieve_hyperedges(query_text)
        
        # 2. 生成答案
        answer = await self.generate_answer(query_text, retrieved_hyperedges)
        
        # 3. 异步更新权重（不阻塞响应）
        asyncio.create_task(
            self._update_weights_async(answer, retrieved_hyperedges)
        )
        
        return answer
    
    async def _update_weights_async(self, answer, hyperedges):
        try:
            # 提取反馈
            feedback = await self.feedback_extractor.extract_feedback(
                answer, hyperedges
            )
            
            # 更新权重
            await self.weight_updater.batch_update_weights([
                {'hyperedge_id': he_id, 'feedback_signal': signal}
                for he_id, signal in feedback.items()
            ])
            
            # 记录统计
            stats = compute_feedback_statistics(feedback)
            logger.info(f"Updated weights: avg_feedback={stats['mean']:.3f}")
            
        except Exception as e:
            logger.error(f"Weight update failed: {e}")
    
    async def retrieve_hyperedges(self, query):
        # 实现检索逻辑
        pass
    
    async def generate_answer(self, query, hyperedges):
        # 实现答案生成逻辑
        pass
```

## 参考资料

- [设计文档](../../.kiro/specs/dynhyperrag-quality-aware/design.md)
- [需求文档](../../.kiro/specs/dynhyperrag-quality-aware/requirements.md)
- [WeightUpdater 文档](./README_WEIGHT_UPDATER.md)
- [测试文件](../../test_feedback_extractor.py)

## 更新日志

### v1.1.0 (2025)
- ✅ 实现基于注意力的反馈提取（可选）
- ✅ 支持多种注意力数据格式
- ✅ 自动回退到嵌入方法

### v1.0.0 (2025)
- ✅ 实现基于嵌入的反馈提取
- ✅ 实现基于引用的反馈提取
- ✅ 实现混合方法
- ✅ 实现批量处理
- ✅ 实现答案嵌入缓存
- ✅ 完整的测试覆盖
