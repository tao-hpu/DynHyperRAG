"""
示例：FeedbackExtractor 与 WeightUpdater 集成

演示如何在查询流程中使用反馈提取器和权重更新器
"""

import asyncio
import numpy as np
from hypergraphrag.dynamic import FeedbackExtractor, WeightUpdater


# 模拟图存储
class MockGraphStorage:
    def __init__(self):
        self.nodes = {
            'he1': {
                'role': 'hyperedge',
                'hyperedge': 'Entity A relates to Entity B in medical context',
                'weight': 1.0,
                'quality_score': 0.8,
                'dynamic_weight': 0.8,
                'feedback_count': 0,
            },
            'he2': {
                'role': 'hyperedge',
                'hyperedge': 'Entity C connects to Entity D in legal domain',
                'weight': 1.0,
                'quality_score': 0.6,
                'dynamic_weight': 0.6,
                'feedback_count': 0,
            },
            'he3': {
                'role': 'hyperedge',
                'hyperedge': 'Entity E is independent',
                'weight': 1.0,
                'quality_score': 0.5,
                'dynamic_weight': 0.5,
                'feedback_count': 0,
            }
        }
    
    async def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id, node_data):
        self.nodes[node_id] = node_data
    
    async def get_node_edges(self, node_id):
        return []
    
    async def node_degree(self, node_id):
        return 3


# 模拟嵌入函数
async def mock_embedding_func(texts):
    """简单的模拟嵌入函数"""
    embeddings = []
    for text in texts:
        text_lower = text.lower()
        emb = np.random.rand(128)
        
        # 为相似文本创建相似嵌入
        if 'entity a' in text_lower and 'entity b' in text_lower:
            emb[0:10] = 0.9
        elif 'entity c' in text_lower and 'entity d' in text_lower:
            emb[10:20] = 0.9
        elif 'entity e' in text_lower:
            emb[20:30] = 0.9
        
        embeddings.append(emb)
    
    return embeddings


async def simulate_query_with_feedback():
    """模拟一个完整的查询流程，包含反馈提取和权重更新"""
    
    print("=" * 70)
    print("DynHyperRAG 查询流程示例：反馈提取 + 权重更新")
    print("=" * 70)
    
    # 1. 初始化组件
    print("\n[1] 初始化组件...")
    graph = MockGraphStorage()
    
    feedback_config = {
        'method': 'hybrid',
        'similarity_threshold': 0.7,
        'citation_threshold': 0.8,
    }
    feedback_extractor = FeedbackExtractor(mock_embedding_func, feedback_config)
    
    weight_config = {
        'strategy': 'ema',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
    }
    weight_updater = WeightUpdater(graph, weight_config)
    
    print("✓ FeedbackExtractor 初始化完成")
    print("✓ WeightUpdater 初始化完成")
    
    # 2. 模拟查询和检索
    print("\n[2] 模拟查询和检索...")
    query = "What is the relationship between Entity A and Entity B?"
    
    retrieved_hyperedges = [
        {
            'id': 'he1',
            'hyperedge': 'Entity A relates to Entity B in medical context',
            'distance': 0.9
        },
        {
            'id': 'he2',
            'hyperedge': 'Entity C connects to Entity D in legal domain',
            'distance': 0.3
        },
        {
            'id': 'he3',
            'hyperedge': 'Entity E is independent',
            'distance': 0.2
        }
    ]
    
    print(f"查询: {query}")
    print(f"检索到 {len(retrieved_hyperedges)} 个超边")
    
    # 3. 模拟答案生成
    print("\n[3] 模拟答案生成...")
    answer = """
    Based on the retrieved information, Entity A relates to Entity B in medical context.
    This relationship is important for understanding medical knowledge graphs.
    """
    print(f"生成答案: {answer[:100]}...")
    
    # 4. 提取反馈信号
    print("\n[4] 提取反馈信号...")
    feedback_signals = await feedback_extractor.extract_feedback(
        answer, retrieved_hyperedges
    )
    
    print("反馈信号:")
    for he_id, signal in feedback_signals.items():
        print(f"  {he_id}: {signal:.3f}")
    
    # 5. 显示更新前的权重
    print("\n[5] 更新前的权重:")
    for he_id in ['he1', 'he2', 'he3']:
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, "
              f"feedback_count={node['feedback_count']}")
    
    # 6. 更新权重
    print("\n[6] 更新权重...")
    for he_id, feedback in feedback_signals.items():
        new_weight = await weight_updater.update_weights(he_id, feedback)
        print(f"  {he_id}: 反馈={feedback:.3f} -> 新权重={new_weight:.3f}")
    
    # 7. 显示更新后的权重
    print("\n[7] 更新后的权重:")
    for he_id in ['he1', 'he2', 'he3']:
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, "
              f"feedback_count={node['feedback_count']}")
    
    # 8. 统计信息
    print("\n[8] 统计信息:")
    
    from hypergraphrag.dynamic.feedback_extractor import compute_feedback_statistics
    feedback_stats = compute_feedback_statistics(feedback_signals)
    print(f"反馈统计:")
    print(f"  平均反馈: {feedback_stats['mean']:.3f}")
    print(f"  正面反馈数: {feedback_stats['positive_count']}")
    print(f"  负面反馈数: {feedback_stats['negative_count']}")
    
    # 9. 模拟第二次查询（观察权重变化）
    print("\n[9] 模拟第二次查询...")
    query2 = "Tell me about Entity C and Entity D"
    answer2 = "Entity C connects to Entity D in legal domain. This is a legal relationship."
    
    feedback_signals2 = await feedback_extractor.extract_feedback(
        answer2, retrieved_hyperedges
    )
    
    print(f"查询: {query2}")
    print("反馈信号:")
    for he_id, signal in feedback_signals2.items():
        print(f"  {he_id}: {signal:.3f}")
    
    # 更新权重
    for he_id, feedback in feedback_signals2.items():
        new_weight = await weight_updater.update_weights(he_id, feedback)
        print(f"  {he_id}: 反馈={feedback:.3f} -> 新权重={new_weight:.3f}")
    
    # 10. 最终权重
    print("\n[10] 最终权重（经过2次查询）:")
    for he_id in ['he1', 'he2', 'he3']:
        node = await graph.get_node(he_id)
        stats = await weight_updater.get_update_statistics(he_id)
        print(f"  {he_id}:")
        print(f"    dynamic_weight: {node['dynamic_weight']:.3f}")
        print(f"    feedback_count: {node['feedback_count']}")
        print(f"    avg_feedback: {stats.get('avg_feedback', 0):.3f}")
        print(f"    weight_trend: {stats.get('weight_trend', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✓ 示例完成！")
    print("=" * 70)
    
    # 11. 关键观察
    print("\n[关键观察]")
    print("1. he1 (Entity A-B) 在第一次查询中被引用，权重上升")
    print("2. he2 (Entity C-D) 在第二次查询中被引用，权重上升")
    print("3. he3 (Entity E) 两次都未被引用，权重下降")
    print("4. 动态权重反映了超边的实际有用性")


async def demonstrate_different_methods():
    """演示不同的反馈提取方法"""
    
    print("\n" + "=" * 70)
    print("演示不同的反馈提取方法")
    print("=" * 70)
    
    answer = "Entity A relates to Entity B in medical context."
    hyperedges = [
        {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B in medical context'},
        {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'}
    ]
    
    methods = ['embedding', 'citation', 'hybrid']
    
    for method in methods:
        print(f"\n[方法: {method}]")
        config = {'method': method, 'similarity_threshold': 0.7}
        extractor = FeedbackExtractor(mock_embedding_func, config)
        
        feedback = await extractor.extract_feedback(answer, hyperedges)
        
        for he_id, signal in feedback.items():
            print(f"  {he_id}: {signal:.3f}")


async def main():
    """运行所有示例"""
    
    # 示例1：完整查询流程
    await simulate_query_with_feedback()
    
    # 示例2：不同方法对比
    await demonstrate_different_methods()


if __name__ == "__main__":
    asyncio.run(main())
