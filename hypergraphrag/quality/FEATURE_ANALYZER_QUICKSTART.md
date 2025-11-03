# Feature Analyzer 快速入门

## 5 分钟快速开始

### 1. 导入模块

```python
from hypergraphrag.quality import QualityScorer, FeatureAnalyzer
```

### 2. 创建分析器

```python
# 假设你已经有了 graph 和 embedding_func
scorer = QualityScorer(graph, embedding_func, config)
analyzer = FeatureAnalyzer(scorer)
```

### 3. 准备数据

```python
# 超边ID列表
hyperedge_ids = ['he_1', 'he_2', 'he_3', ...]

# 真实质量标签（0-1，需要人工标注）
ground_truth = {
    'he_1': 0.8,  # 高质量
    'he_2': 0.6,  # 中等质量
    'he_3': 0.9,  # 高质量
    ...
}
```

### 4. 运行分析

```python
import asyncio

async def run_analysis():
    # 特征重要性分析
    result = await analyzer.analyze_feature_importance(
        hyperedge_ids,
        ground_truth,
        method='model_based'  # 最快的方法
    )
    
    if result['success']:
        print("特征重要性:")
        for feature, importance in sorted(
            result['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {feature}: {importance:.4f}")
    
    # 生成可视化
    analyzer.plot_feature_importance(result['feature_importance'])
    
    # 生成报告
    analyzer.generate_analysis_report(result)

# 运行
asyncio.run(run_analysis())
```

## 三种分析方法对比

| 方法 | 速度 | 准确性 | 需要额外依赖 | 推荐场景 |
|------|------|--------|--------------|----------|
| `model_based` | ⚡⚡⚡ 最快 | ⭐⭐ 中等 | ❌ 否 | 快速分析、生产环境 |
| `permutation` | ⚡⚡ 中等 | ⭐⭐⭐ 较好 | ❌ 否 | 平衡选择 |
| `shap` | ⚡ 较慢 | ⭐⭐⭐⭐ 最好 | ✅ 是 (pip install shap) | 研究分析、论文 |

## 常见问题

### Q1: 需要多少标注样本？
**A**: 建议至少 50 个，越多越好。100+ 个样本可以得到可靠的结果。

### Q2: 如何获取 ground_truth 标签？
**A**: 需要人工标注。可以使用标注界面（Task 16）或手动标注。标签应该是 0-1 之间的浮点数，表示超边的质量。

### Q3: SHAP 安装失败怎么办？
**A**: 使用 `method='model_based'` 或 `method='permutation'`，不需要 SHAP 库。

### Q4: 分析结果如何解读？
**A**: 
- 重要性高的特征对质量预测贡献大
- 如果某个特征重要性 > 0.4，说明它是主导特征
- 如果某个特征重要性 < 0.1，可以考虑在轻量级版本中移除

### Q5: 如何使用分析结果优化系统？
**A**:
1. 调整 QualityScorer 的特征权重
2. 在轻量级版本中移除低重要性特征
3. 重点优化高重要性特征的计算准确性

## 完整示例

```python
import asyncio
from hypergraphrag.quality import QualityScorer, FeatureAnalyzer

async def complete_analysis():
    # 1. 创建评分器和分析器
    scorer = QualityScorer(graph, embedding_func, config)
    analyzer = FeatureAnalyzer(scorer)
    
    # 2. 准备数据
    hyperedge_ids = get_hyperedge_ids()  # 你的函数
    ground_truth = load_ground_truth()   # 你的函数
    
    # 3. 特征重要性分析
    print("分析特征重要性...")
    importance_result = await analyzer.analyze_feature_importance(
        hyperedge_ids,
        ground_truth,
        method='shap'  # 或 'permutation', 'model_based'
    )
    
    # 4. 特征相关性分析
    print("分析特征相关性...")
    correlation_result = await analyzer.analyze_feature_correlation(
        hyperedge_ids
    )
    
    # 5. 生成所有可视化
    print("生成可视化...")
    analyzer.plot_feature_importance(
        importance_result['feature_importance'],
        save_path='expr/analysis/feature_importance.png'
    )
    
    if 'shap_values' in importance_result:
        # 需要特征矩阵 X
        X = ...  # 从 importance_result 中获取或重新计算
        analyzer.plot_shap_summary(
            importance_result['shap_values'],
            X,
            save_path='expr/analysis/shap_summary.png'
        )
    
    analyzer.plot_correlation_heatmap(
        correlation_result['correlation_array'],
        save_path='expr/analysis/correlation_heatmap.png'
    )
    
    # 6. 生成综合报告
    print("生成报告...")
    report_path = analyzer.generate_analysis_report(
        importance_result,
        correlation_result,
        save_path='expr/analysis/feature_analysis_report.md'
    )
    
    print(f"\n✅ 分析完成！")
    print(f"📊 报告: {report_path}")
    print(f"📈 图表: expr/analysis/")
    
    return importance_result, correlation_result

# 运行完整分析
results = asyncio.run(complete_analysis())
```

## 输出文件位置

```
expr/analysis/
├── feature_importance.png      # 特征重要性条形图
├── shap_summary.png           # SHAP 摘要图（如果使用 SHAP）
├── correlation_heatmap.png    # 特征相关性热力图
└── feature_analysis_report.md # 综合分析报告
```

## 下一步

1. 查看生成的报告 `feature_analysis_report.md`
2. 根据特征重要性调整 QualityScorer 的权重
3. 识别并移除冗余特征
4. 在论文中使用生成的图表

## 更多信息

- 详细文档: `hypergraphrag/quality/README_ANALYZER.md`
- 设计文档: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- 任务总结: `.kiro/specs/dynhyperrag-quality-aware/TASK_5_SUMMARY.md`
