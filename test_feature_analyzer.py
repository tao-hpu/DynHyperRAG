"""
测试特征重要性分析器

这个脚本演示如何使用 FeatureAnalyzer 进行特征重要性分析。
"""

import asyncio
import numpy as np
from hypergraphrag.quality import FeatureAnalyzer, QualityScorer


class MockGraph:
    """模拟图存储用于测试"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
    
    async def get_node(self, node_id):
        return self.nodes.get(node_id, {
            'hyperedge': 'test hyperedge',
            'role': 'hyperedge'
        })
    
    async def get_node_edges(self, node_id):
        return self.edges.get(node_id, [
            (node_id, f'entity_{i}', {}) for i in range(3)
        ])
    
    async def node_degree(self, node_id):
        return len(self.edges.get(node_id, []))
    
    async def upsert_node(self, node_id, node_data):
        self.nodes[node_id] = node_data


async def mock_embedding_func(texts):
    """模拟嵌入函数"""
    return [np.random.rand(128) for _ in texts]


async def test_feature_analyzer():
    """测试特征分析器"""
    
    print("=" * 60)
    print("测试特征重要性分析器")
    print("=" * 60)
    
    # 1. 创建模拟环境
    print("\n1. 创建模拟环境...")
    mock_graph = MockGraph()
    
    # 添加一些测试超边
    for i in range(20):
        he_id = f'hyperedge_{i}'
        mock_graph.nodes[he_id] = {
            'hyperedge': f'Test hyperedge {i}',
            'role': 'hyperedge'
        }
        mock_graph.edges[he_id] = [
            (he_id, f'entity_{j}', {}) for j in range(np.random.randint(2, 6))
        ]
    
    # 2. 创建质量评分器
    print("2. 创建质量评分器...")
    config = {
        'quality_mode': 'unsupervised',
        'quality_feature_weights': {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        }
    }
    
    scorer = QualityScorer(mock_graph, mock_embedding_func, config)
    
    # 3. 创建特征分析器
    print("3. 创建特征分析器...")
    analyzer = FeatureAnalyzer(scorer)
    
    # 4. 生成模拟的真实标签
    print("4. 生成模拟标签...")
    hyperedge_ids = [f'hyperedge_{i}' for i in range(20)]
    ground_truth = {
        he_id: np.random.rand() for he_id in hyperedge_ids
    }
    
    # 5. 测试特征重要性分析（使用 model_based 方法，不需要 shap）
    print("\n5. 分析特征重要性（model_based 方法）...")
    importance_result = await analyzer.analyze_feature_importance(
        hyperedge_ids,
        ground_truth,
        method='model_based'
    )
    
    if importance_result.get('success'):
        print("✅ 特征重要性分析成功！")
        print("\n特征重要性排序：")
        
        feature_importance = importance_result['feature_importance']
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for rank, (feature, importance) in enumerate(sorted_features, 1):
            print(f"  {rank}. {feature:20s}: {importance:.4f} ({importance*100:.2f}%)")
        
        if 'model_performance' in importance_result:
            perf = importance_result['model_performance']
            print(f"\n模型性能：")
            print(f"  训练集 R²: {perf['train_r2']:.4f}")
            print(f"  测试集 R²: {perf['test_r2']:.4f}")
    else:
        print(f"❌ 特征重要性分析失败: {importance_result.get('error')}")
        return
    
    # 6. 测试特征相关性分析
    print("\n6. 分析特征相关性...")
    correlation_result = await analyzer.analyze_feature_correlation(hyperedge_ids)
    
    if correlation_result.get('success'):
        print("✅ 特征相关性分析成功！")
        
        high_corr = correlation_result.get('high_correlation_pairs', [])
        if high_corr:
            print(f"\n发现 {len(high_corr)} 对高度相关的特征：")
            for pair in high_corr:
                print(f"  {pair['feature1']} <-> {pair['feature2']}: {pair['correlation']:.4f}")
        else:
            print("\n未发现高度相关的特征对（|相关系数| > 0.7）")
    else:
        print(f"❌ 特征相关性分析失败: {correlation_result.get('error')}")
        return
    
    # 7. 生成可视化
    print("\n7. 生成可视化...")
    try:
        # 特征重要性图
        importance_path = analyzer.plot_feature_importance(
            importance_result['feature_importance'],
            title="Feature Importance (Model-Based)"
        )
        print(f"✅ 特征重要性图: {importance_path}")
        
        # 相关性热力图
        if 'correlation_array' in correlation_result:
            heatmap_path = analyzer.plot_correlation_heatmap(
                correlation_result['correlation_array']
            )
            print(f"✅ 相关性热力图: {heatmap_path}")
    except Exception as e:
        print(f"⚠️  可视化生成失败: {e}")
    
    # 8. 生成分析报告
    print("\n8. 生成分析报告...")
    try:
        report_path = analyzer.generate_analysis_report(
            importance_result,
            correlation_result
        )
        print(f"✅ 分析报告: {report_path}")
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_feature_analyzer())
