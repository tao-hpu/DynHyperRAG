# 嵌入缓存优化

## 概述

嵌入缓存优化通过两级缓存系统显著减少重复的嵌入计算，提升系统性能：

1. **内存缓存**：快速访问，存储在 `CoherenceMetric` 实例中
2. **持久化缓存**：存储在实体节点的 `embedding_cache` 字段中，跨会话持久化

## 性能提升

根据测试结果：
- **速度提升**：3x+ 
- **嵌入函数调用减少**：66.7%+
- **适用场景**：重复查询相同实体的场景

## 使用方法

### 基本使用

```python
from hypergraphrag.quality.coherence import CoherenceMetric

# 创建一致性度量器（默认启用持久化缓存）
coherence = CoherenceMetric(
    embedding_func=embedding_func,
    knowledge_graph_inst=graph,
    use_persistent_cache=True  # 启用持久化缓存
)

# 计算一致性（自动使用缓存）
score = await coherence.compute_coherence('hyperedge_id')
```

### 批量预缓存

对于已知会频繁访问的实体，可以预先缓存：

```python
# 批量缓存实体嵌入
entity_ids = ['entity1', 'entity2', 'entity3', ...]
await coherence.cache_entity_embeddings(entity_ids)
```

### 系统启动时预热缓存

从持久化缓存加载到内存，提升首次查询性能：

```python
# 加载持久化缓存到内存
loaded_count = await coherence.load_persistent_cache_to_memory(entity_ids)
print(f"预加载了 {loaded_count} 个嵌入")
```

### 缓存管理

```python
# 获取缓存大小
size = coherence.get_cache_size()
print(f"内存缓存大小: {size}")

# 获取缓存统计
stats = await coherence.get_cache_statistics()
print(stats)

# 清除内存缓存（不影响持久化缓存）
coherence.clear_cache()
```

## 工作原理

### 两级缓存架构

```
查询嵌入
    ↓
检查内存缓存
    ↓ (未命中)
检查持久化缓存（实体节点）
    ↓ (未命中)
批量计算嵌入
    ↓
存储到内存缓存
    ↓
异步存储到持久化缓存
```

### 缓存查找流程

1. **内存缓存查找**（最快）
   - 在 `_embedding_cache` 字典中查找
   - O(1) 时间复杂度

2. **持久化缓存查找**（中等速度）
   - 从实体节点的 `embedding_cache` 字段读取
   - 需要图存储查询

3. **计算嵌入**（最慢）
   - 调用嵌入函数计算
   - 批量计算以提高效率

### 批量优化

系统自动将多个未缓存的实体合并为一次批量嵌入调用：

```python
# 假设需要5个实体的嵌入
# - 2个在内存缓存中
# - 1个在持久化缓存中
# - 2个需要计算

# 系统会：
# 1. 从内存缓存获取2个（瞬时）
# 2. 从持久化缓存加载1个（快速）
# 3. 批量计算剩余2个（一次调用）
```

## 数据结构

### 实体节点扩展

```python
EntityNode = {
    'role': 'entity',
    'entity_name': str,
    'entity_type': str,
    'description': str,
    'source_id': str,
    
    # 新增：嵌入缓存
    'embedding_cache': List[float]  # 嵌入向量（可选）
}
```

### 内存缓存结构

```python
_embedding_cache = {
    'entity_id_1': np.ndarray([...]),  # 嵌入向量
    'entity_id_2': np.ndarray([...]),
    ...
}
```

## 配置选项

### 启用/禁用持久化缓存

```python
# 启用持久化缓存（推荐）
coherence = CoherenceMetric(
    embedding_func=embedding_func,
    knowledge_graph_inst=graph,
    use_persistent_cache=True
)

# 仅使用内存缓存
coherence = CoherenceMetric(
    embedding_func=embedding_func,
    knowledge_graph_inst=graph,
    use_persistent_cache=False
)
```

### 何时使用持久化缓存

**推荐使用**：
- 生产环境
- 大规模知识图谱
- 需要跨会话保持性能
- 嵌入计算成本高

**可以不使用**：
- 开发/测试环境
- 小规模图谱
- 实体频繁变化
- 存储空间受限

## 性能考虑

### 内存使用

每个嵌入向量的内存占用：
- 假设嵌入维度为 1536（OpenAI ada-002）
- 每个向量：1536 × 4 bytes = 6.1 KB
- 10,000个实体：约 61 MB

### 存储开销

持久化缓存存储在图数据库中：
- 每个实体节点增加 6-8 KB
- 对于 Neo4j/MongoDB 等数据库，这是可接受的开销

### 计算节省

假设：
- 嵌入计算时间：50ms/实体
- 图查询时间：5ms/实体
- 内存查询时间：0.01ms/实体

缓存命中率 80% 时：
- 无缓存：50ms × 100实体 = 5000ms
- 有缓存：50ms × 20 + 5ms × 80 = 1400ms
- **节省 72% 时间**

## 最佳实践

### 1. 系统启动时预热缓存

```python
# 获取常用实体列表
frequent_entities = get_frequent_entities()

# 预加载到内存
await coherence.load_persistent_cache_to_memory(frequent_entities)
```

### 2. 批量处理

```python
# 好：批量缓存
await coherence.cache_entity_embeddings(all_entity_ids)

# 不好：逐个缓存
for entity_id in all_entity_ids:
    await coherence._get_entity_embeddings([entity_id])
```

### 3. 定期清理内存缓存

```python
# 在长时间运行的服务中，定期清理内存缓存
if coherence.get_cache_size() > 100000:
    coherence.clear_cache()
    # 持久化缓存仍然保留
```

### 4. 监控缓存效果

```python
# 定期检查缓存统计
stats = await coherence.get_cache_statistics()
logger.info(f"缓存统计: {stats}")
```

## 故障排除

### 问题：持久化缓存未生效

**检查**：
```python
# 验证持久化缓存是否启用
assert coherence.use_persistent_cache == True

# 检查实体节点是否有缓存
node = await graph.get_node('entity_id')
print('embedding_cache' in node)
```

### 问题：内存占用过高

**解决方案**：
```python
# 定期清理内存缓存
coherence.clear_cache()

# 或者禁用持久化缓存，仅使用内存缓存
coherence = CoherenceMetric(
    embedding_func=embedding_func,
    knowledge_graph_inst=graph,
    use_persistent_cache=False
)
```

### 问题：缓存不一致

**原因**：实体描述更新后，缓存未更新

**解决方案**：
```python
# 更新实体后，清除其缓存
if entity_id in coherence._embedding_cache:
    del coherence._embedding_cache[entity_id]

# 或者清除整个缓存
coherence.clear_cache()
```

## 测试

运行嵌入缓存测试：

```bash
PYTHONPATH=. python hypergraphrag/quality/test_embedding_cache.py
```

测试覆盖：
- ✓ 基本缓存功能
- ✓ 批量缓存
- ✓ 性能提升验证
- ✓ 持久化缓存重新加载
- ✓ 缓存统计

## 相关文件

- `hypergraphrag/quality/coherence.py` - 一致性度量器（包含缓存逻辑）
- `hypergraphrag/models.py` - 数据模型定义
- `hypergraphrag/quality/test_embedding_cache.py` - 缓存测试

## 未来改进

1. **LRU缓存策略**：限制内存缓存大小，自动淘汰最少使用的项
2. **缓存预热策略**：基于查询历史智能预加载
3. **分布式缓存**：支持 Redis 等分布式缓存系统
4. **缓存版本控制**：跟踪实体更新，自动失效缓存
5. **压缩存储**：使用量化或压缩减少存储开销

## 总结

嵌入缓存优化通过两级缓存系统显著提升了 DynHyperRAG 的性能：

- **3x+ 速度提升**
- **66%+ 调用减少**
- **跨会话持久化**
- **自动批量优化**

这是一个简单但有效的优化，特别适合生产环境中的大规模知识图谱应用。
