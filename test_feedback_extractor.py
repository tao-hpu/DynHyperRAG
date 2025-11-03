"""
测试反馈信号提取器

验证 FeedbackExtractor 的基本功能：
1. 基于嵌入的反馈提取
2. 基于引用的反馈提取
3. 混合方法
"""

import asyncio
import numpy as np
from hypergraphrag.dynamic import FeedbackExtractor


# 模拟嵌入函数
async def mock_embedding_func(texts):
    """
    模拟嵌入函数
    为了测试，我们创建简单的嵌入：
    - 相似的文本有相似的嵌入
    - 不同的文本有不同的嵌入
    """
    embeddings = []
    for text in texts:
        # 简单的基于文本长度和内容的嵌入
        # 实际应用中会使用真实的嵌入模型
        text_lower = text.lower()
        
        # 创建128维嵌入
        emb = np.random.rand(128)
        
        # 如果文本包含特定关键词，调整嵌入使其相似
        if 'entity a' in text_lower and 'entity b' in text_lower:
            emb[0:10] = 0.9  # 特征1
        elif 'entity c' in text_lower and 'entity d' in text_lower:
            emb[10:20] = 0.9  # 特征2
        elif 'entity e' in text_lower:
            emb[20:30] = 0.9  # 特征3
        
        embeddings.append(emb)
    
    return embeddings


async def test_embedding_based_feedback():
    """测试基于嵌入的反馈提取"""
    print("\n=== 测试1: 基于嵌入的反馈提取 ===")
    
    # 配置
    config = {
        'method': 'embedding',
        'similarity_threshold': 0.7,
        'positive_feedback': 1.0,
        'negative_feedback': 0.3,
    }
    
    # 创建提取器
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # 模拟答案和检索到的超边
    answer = "Entity A and Entity B are closely related in the medical domain."
    
    retrieved_hyperedges = [
        {
            'id': 'he1',
            'hyperedge': 'Entity A relates to Entity B in medical context'
        },
        {
            'id': 'he2',
            'hyperedge': 'Entity C connects to Entity D in legal domain'
        },
        {
            'id': 'he3',
            'hyperedge': 'Entity E is independent'
        }
    ]
    
    # 提取反馈
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges)
    
    print(f"答案: {answer}")
    print(f"\n反馈信号:")
    for he_id, signal in feedback.items():
        print(f"  {he_id}: {signal:.3f}")
    
    # 验证
    assert 'he1' in feedback, "应该为 he1 生成反馈"
    assert 'he2' in feedback, "应该为 he2 生成反馈"
    assert 'he3' in feedback, "应该为 he3 生成反馈"
    
    print("\n✓ 基于嵌入的反馈提取测试通过")
    
    return feedback


async def test_citation_based_feedback():
    """测试基于引用的反馈提取"""
    print("\n=== 测试2: 基于引用的反馈提取 ===")
    
    # 配置
    config = {
        'method': 'citation',
        'citation_threshold': 0.8,
        'positive_feedback': 1.0,
        'negative_feedback': 0.3,
    }
    
    # 创建提取器
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # 模拟答案（包含对超边的引用）
    answer = """
    Based on the retrieved information, we can see that Entity A relates to Entity B 
    in medical context. This relationship is important for understanding the domain.
    """
    
    retrieved_hyperedges = [
        {
            'id': 'he1',
            'hyperedge': 'Entity A relates to Entity B in medical context'
        },
        {
            'id': 'he2',
            'hyperedge': 'Entity C connects to Entity D'
        },
        {
            'id': 'he3',
            'hyperedge': 'Unrelated information about Entity E'
        }
    ]
    
    # 提取反馈
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges)
    
    print(f"答案: {answer[:100]}...")
    print(f"\n反馈信号:")
    for he_id, signal in feedback.items():
        print(f"  {he_id}: {signal:.3f}")
    
    # 验证：he1 应该有高反馈（被引用），he2 和 he3 应该有低反馈
    assert feedback['he1'] >= 0.7, "he1 应该有高反馈（被引用）"
    assert feedback['he2'] < 0.7, "he2 应该有低反馈（未被引用）"
    assert feedback['he3'] < 0.7, "he3 应该有低反馈（未被引用）"
    
    print("\n✓ 基于引用的反馈提取测试通过")
    
    return feedback


async def test_hybrid_feedback():
    """测试混合方法"""
    print("\n=== 测试3: 混合方法 ===")
    
    # 配置
    config = {
        'method': 'hybrid',
        'similarity_threshold': 0.7,
        'citation_threshold': 0.8,
        'positive_feedback': 1.0,
        'negative_feedback': 0.3,
    }
    
    # 创建提取器
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # 模拟答案
    answer = "Entity A and Entity B are related. Entity C is also mentioned."
    
    retrieved_hyperedges = [
        {
            'id': 'he1',
            'hyperedge': 'Entity A relates to Entity B'  # 会被引用检测到
        },
        {
            'id': 'he2',
            'hyperedge': 'Entity C information'  # 部分匹配
        },
        {
            'id': 'he3',
            'hyperedge': 'Entity D unrelated'  # 不相关
        }
    ]
    
    # 提取反馈
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges)
    
    print(f"答案: {answer}")
    print(f"\n反馈信号:")
    for he_id, signal in feedback.items():
        print(f"  {he_id}: {signal:.3f}")
    
    # 验证
    assert 'he1' in feedback, "应该为 he1 生成反馈"
    assert 'he2' in feedback, "应该为 he2 生成反馈"
    assert 'he3' in feedback, "应该为 he3 生成反馈"
    
    print("\n✓ 混合方法测试通过")
    
    return feedback


async def test_batch_extraction():
    """测试批量提取"""
    print("\n=== 测试4: 批量反馈提取 ===")
    
    # 配置
    config = {
        'method': 'embedding',
        'similarity_threshold': 0.7,
    }
    
    # 创建提取器
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # 多个查询的答案和超边
    answers = [
        "Entity A relates to Entity B",
        "Entity C connects to Entity D"
    ]
    
    retrieved_hyperedges_list = [
        [
            {'id': 'he1', 'hyperedge': 'Entity A and Entity B relationship'},
            {'id': 'he2', 'hyperedge': 'Entity C information'}
        ],
        [
            {'id': 'he3', 'hyperedge': 'Entity C and Entity D connection'},
            {'id': 'he4', 'hyperedge': 'Entity A information'}
        ]
    ]
    
    # 批量提取
    feedback_list = await extractor.batch_extract_feedback(
        answers, retrieved_hyperedges_list
    )
    
    print(f"批量处理 {len(answers)} 个查询")
    for i, feedback in enumerate(feedback_list):
        print(f"\n查询 {i+1} 反馈:")
        for he_id, signal in feedback.items():
            print(f"  {he_id}: {signal:.3f}")
    
    # 验证
    assert len(feedback_list) == 2, "应该返回2个反馈字典"
    assert len(feedback_list[0]) == 2, "第一个查询应该有2个反馈"
    assert len(feedback_list[1]) == 2, "第二个查询应该有2个反馈"
    
    print("\n✓ 批量反馈提取测试通过")
    
    return feedback_list


async def test_statistics():
    """测试统计功能"""
    print("\n=== 测试5: 统计功能 ===")
    
    # 配置
    config = {
        'method': 'embedding',
        'similarity_threshold': 0.7,
    }
    
    # 创建提取器
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # 获取统计信息
    stats = extractor.get_statistics()
    
    print("提取器统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 验证
    assert stats['method'] == 'embedding', "方法应该是 embedding"
    assert stats['similarity_threshold'] == 0.7, "阈值应该是 0.7"
    assert 'cache_size' in stats, "应该包含缓存大小"
    
    print("\n✓ 统计功能测试通过")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("反馈信号提取器测试")
    print("=" * 60)
    
    try:
        # 运行测试
        await test_embedding_based_feedback()
        await test_citation_based_feedback()
        await test_hybrid_feedback()
        await test_batch_extraction()
        await test_statistics()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
