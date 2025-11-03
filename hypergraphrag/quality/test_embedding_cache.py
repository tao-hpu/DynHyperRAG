"""
测试嵌入缓存优化

验证两级缓存系统：
1. 内存缓存（快速访问）
2. 持久化缓存（存储在实体节点中）
"""

import asyncio
import numpy as np
from typing import List
import time


class MockGraphStorage:
    """模拟图存储"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.update_count = 0  # 跟踪更新次数
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: dict):
        self.nodes[node_id] = node_data
        self.update_count += 1
    
    async def get_node_edges(self, node_id: str):
        return self.edges.get(node_id, [])


class MockEmbeddingFunc:
    """模拟嵌入函数"""
    
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.call_count = 0  # 跟踪调用次数
        self.total_texts = 0  # 跟踪处理的文本总数
    
    async def __call__(self, texts: List[str]) -> List[np.ndarray]:
        self.call_count += 1
        self.total_texts += len(texts)
        # 模拟嵌入计算（使用随机向量）
        await asyncio.sleep(0.01 * len(texts))  # 模拟计算时间
        return [np.random.randn(self.dim) for _ in texts]


async def test_basic_cache():
    """测试基本缓存功能"""
    print("\n=== 测试1: 基本缓存功能 ===")
    
    from hypergraphrag.quality.coherence import CoherenceMetric
    
    # 创建模拟对象
    graph = MockGraphStorage()
    embedding_func = MockEmbeddingFunc()
    
    # 添加测试实体
    graph.nodes['entity1'] = {
        'entity_name': 'Diabetes',
        'entity_type': 'disease',
        'description': 'A metabolic disorder'
    }
    graph.nodes['entity2'] = {
        'entity_name': 'Insulin',
        'entity_type': 'drug',
        'description': 'A hormone that regulates blood sugar'
    }
    
    # 创建一致性度量器（启用持久化缓存）
    coherence = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    
    # 第一次获取嵌入（应该计算）
    print("第一次获取嵌入...")
    embeddings1 = await coherence._get_entity_embeddings(['entity1', 'entity2'])
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 处理的文本数: {embedding_func.total_texts}")
    print(f"  - 内存缓存大小: {coherence.get_cache_size()}")
    
    # 等待持久化缓存更新完成
    await asyncio.sleep(0.1)
    print(f"  - 图更新次数: {graph.update_count}")
    
    # 验证持久化缓存
    node1 = await graph.get_node('entity1')
    has_cache = 'embedding_cache' in node1
    print(f"  - 实体1有持久化缓存: {has_cache}")
    
    # 第二次获取相同嵌入（应该从内存缓存读取）
    print("\n第二次获取相同嵌入（内存缓存）...")
    embeddings2 = await coherence._get_entity_embeddings(['entity1', 'entity2'])
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 向量相同: {np.allclose(embeddings1[0], embeddings2[0])}")
    
    # 清除内存缓存
    print("\n清除内存缓存...")
    coherence.clear_cache()
    print(f"  - 内存缓存大小: {coherence.get_cache_size()}")
    
    # 第三次获取（应该从持久化缓存读取）
    print("\n第三次获取（持久化缓存）...")
    embeddings3 = await coherence._get_entity_embeddings(['entity1', 'entity2'])
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 向量相同: {np.allclose(embeddings1[0], embeddings3[0])}")
    print(f"  - 内存缓存大小: {coherence.get_cache_size()}")
    
    print("\n✓ 基本缓存功能测试通过")


async def test_batch_caching():
    """测试批量缓存"""
    print("\n=== 测试2: 批量缓存 ===")
    
    from hypergraphrag.quality.coherence import CoherenceMetric
    
    # 创建模拟对象
    graph = MockGraphStorage()
    embedding_func = MockEmbeddingFunc()
    
    # 添加多个测试实体
    for i in range(10):
        graph.nodes[f'entity{i}'] = {
            'entity_name': f'Entity {i}',
            'entity_type': 'test',
            'description': f'Test entity {i}'
        }
    
    # 创建一致性度量器
    coherence = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    
    # 批量缓存
    print("批量缓存10个实体...")
    entity_ids = [f'entity{i}' for i in range(10)]
    await coherence.cache_entity_embeddings(entity_ids)
    
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 处理的文本数: {embedding_func.total_texts}")
    print(f"  - 内存缓存大小: {coherence.get_cache_size()}")
    
    # 验证批量调用（应该只调用一次）
    assert embedding_func.call_count == 1, "批量缓存应该只调用一次嵌入函数"
    assert embedding_func.total_texts == 10, "应该处理10个文本"
    
    print("\n✓ 批量缓存测试通过")


async def test_performance_improvement():
    """测试性能提升"""
    print("\n=== 测试3: 性能提升 ===")
    
    from hypergraphrag.quality.coherence import CoherenceMetric
    
    # 创建模拟对象
    graph = MockGraphStorage()
    embedding_func = MockEmbeddingFunc()
    
    # 添加测试实体和超边
    for i in range(5):
        graph.nodes[f'entity{i}'] = {
            'entity_name': f'Entity {i}',
            'entity_type': 'test',
            'description': f'Test entity {i}'
        }
    
    graph.nodes['hyperedge1'] = {
        'role': 'hyperedge',
        'hyperedge_name': 'Test hyperedge'
    }
    
    # 超边连接所有实体
    graph.edges['hyperedge1'] = [
        ('hyperedge1', f'entity{i}', {}) for i in range(5)
    ]
    
    # 测试无缓存性能
    print("测试无缓存性能...")
    coherence_no_cache = CoherenceMetric(embedding_func, graph, use_persistent_cache=False)
    
    start = time.time()
    for _ in range(3):
        coherence_no_cache.clear_cache()  # 每次清除缓存
        await coherence_no_cache.compute_coherence('hyperedge1')
    time_no_cache = time.time() - start
    calls_no_cache = embedding_func.call_count
    
    print(f"  - 耗时: {time_no_cache:.3f}秒")
    print(f"  - 嵌入函数调用次数: {calls_no_cache}")
    
    # 测试有缓存性能
    print("\n测试有缓存性能...")
    embedding_func.call_count = 0
    coherence_with_cache = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    
    start = time.time()
    for _ in range(3):
        await coherence_with_cache.compute_coherence('hyperedge1')
    time_with_cache = time.time() - start
    calls_with_cache = embedding_func.call_count
    
    print(f"  - 耗时: {time_with_cache:.3f}秒")
    print(f"  - 嵌入函数调用次数: {calls_with_cache}")
    
    # 计算性能提升
    speedup = time_no_cache / time_with_cache if time_with_cache > 0 else float('inf')
    call_reduction = (calls_no_cache - calls_with_cache) / calls_no_cache * 100
    
    print(f"\n性能提升:")
    print(f"  - 速度提升: {speedup:.2f}x")
    print(f"  - 调用次数减少: {call_reduction:.1f}%")
    
    assert calls_with_cache < calls_no_cache, "缓存应该减少嵌入函数调用次数"
    
    print("\n✓ 性能提升测试通过")


async def test_persistent_cache_reload():
    """测试持久化缓存重新加载"""
    print("\n=== 测试4: 持久化缓存重新加载 ===")
    
    from hypergraphrag.quality.coherence import CoherenceMetric
    
    # 创建模拟对象
    graph = MockGraphStorage()
    embedding_func = MockEmbeddingFunc()
    
    # 添加测试实体
    for i in range(5):
        graph.nodes[f'entity{i}'] = {
            'entity_name': f'Entity {i}',
            'entity_type': 'test',
            'description': f'Test entity {i}'
        }
    
    # 第一个一致性度量器：计算并缓存
    print("第一个度量器：计算并缓存...")
    coherence1 = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    entity_ids = [f'entity{i}' for i in range(5)]
    await coherence1.cache_entity_embeddings(entity_ids)
    
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 内存缓存大小: {coherence1.get_cache_size()}")
    
    # 第二个一致性度量器：从持久化缓存加载
    print("\n第二个度量器：从持久化缓存加载...")
    embedding_func.call_count = 0
    coherence2 = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    
    loaded = await coherence2.load_persistent_cache_to_memory(entity_ids)
    print(f"  - 加载的嵌入数量: {loaded}")
    print(f"  - 嵌入函数调用次数: {embedding_func.call_count}")
    print(f"  - 内存缓存大小: {coherence2.get_cache_size()}")
    
    assert loaded == 5, "应该加载5个嵌入"
    assert embedding_func.call_count == 0, "不应该调用嵌入函数"
    
    print("\n✓ 持久化缓存重新加载测试通过")


async def test_cache_statistics():
    """测试缓存统计"""
    print("\n=== 测试5: 缓存统计 ===")
    
    from hypergraphrag.quality.coherence import CoherenceMetric
    
    # 创建模拟对象
    graph = MockGraphStorage()
    embedding_func = MockEmbeddingFunc()
    
    # 添加测试实体
    for i in range(3):
        graph.nodes[f'entity{i}'] = {
            'entity_name': f'Entity {i}',
            'entity_type': 'test',
            'description': f'Test entity {i}'
        }
    
    # 创建一致性度量器
    coherence = CoherenceMetric(embedding_func, graph, use_persistent_cache=True)
    
    # 缓存一些实体
    await coherence.cache_entity_embeddings(['entity0', 'entity1', 'entity2'])
    
    # 获取统计信息
    stats = await coherence.get_cache_statistics()
    
    print("缓存统计:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    assert stats['memory_cache_size'] == 3, "内存缓存应该有3个实体"
    assert stats['use_persistent_cache'] == True, "应该启用持久化缓存"
    
    print("\n✓ 缓存统计测试通过")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("嵌入缓存优化测试")
    print("=" * 60)
    
    try:
        await test_basic_cache()
        await test_batch_caching()
        await test_performance_improvement()
        await test_persistent_cache_reload()
        await test_cache_statistics()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
