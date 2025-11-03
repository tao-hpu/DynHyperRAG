# Feature Importance Analyzer

## 概述

`FeatureAnalyzer` 模块提供了全面的特征重要性分析功能，用于理解哪些图结构特征最能预测超边质量。

## 主要功能

### 1. 特征重要性分析

支持三种分析方法：

- **SHAP (SHapley Additive exPlanations)**: 基于博弈论的特征重要性分析，提供最准确的特征贡献度量
- **Permutation Importance**: 通过随机打乱特征值测量性能下降来评估重要性
- **Model-Based**: 使用模型内置的特征重要性（如随机森林的 `feature_importances_`）

### 2. 特征相关性分析

- 计算特征之间的相关性矩阵
- 识别高度相关的特征对（冗余特征）
- 生成相关性热力图

### 3. 可视化

- 特征重要性条形图
- SHAP 摘要图
- 特征相关性热力图

### 4. 报告生成

自动生成包含以下内容的 Markdown 格式分析报告：
- 分析概览和模型性能
- 特征重要性排序
- 特征解释
- 相关性分析
- 优化建议

## 使用示例

### 基本用法

```python
import asyncio
from hypergraphrag.quality import QualityScorer, FeatureAnalyzer

async def analyze_features():
    # 1. 创建质量评分器
    scorer = QualityScorer(
        knowledge_graph_inst=graph,
        embedding_func=embedding_func,
        config={'quality_mode': 'unsupervised'}
    )
    
    # 2. 创建特征分析器
    analyzer = FeatureAnalyzer(scorer)
    
    # 3. 准备数据
    hyperedge_ids = ['he_1', 'he_2', 'he_3', ...]
    ground_truth = {
        'he_1': 0.8,  # 真实质量标签 (0-1)
        'he_2': 0.6,
        'he_3': 0.9,
        ...
    }
    
    # 4. 分析特征重要性
    result = await analyzer.analyze_feature_importance(
        hyperedge_ids,
        ground_truth,
        method='shap'  # 或 'permutation', 'model_based'
    )
    
    if result['success']:
        print("特征重要性:")
        for feature, importance in result['feature_importance'].items():
            print(f"  {feature}: {importance:.4f}")
    
    return result

# 运行分析
result = asyncio.run(analyze_features())
```

### 特征相关性分析

```python
async def analyze_correlation():
    analyzer = FeatureAnalyzer(scorer)
    
    # 分析特征相关性
    corr_result = await analyzer.analyze_feature_correlation(hyperedge_ids)
    
    if corr_result['success']:
        # 查看高度相关的特征对
        for pair in corr_result['high_correlation_pairs']:
            print(f"{pair['feature1']} <-> {pair['feature2']}: {pair['correlation']:.4f}")
        
        # 生成热力图
        analyzer.plot_correlation_heatmap(
            corr_result['correlation_array'],
            save_path='correlation_heatmap.png'
        )

asyncio.run(analyze_correlation())
```

### 生成完整报告

```python
async def generate_full_report():
    analyzer = FeatureAnalyzer(scorer)
    
    # 特征重要性分析
    importance_result = await analyzer.analyze_feature_importance(
        hyperedge_ids, ground_truth, method='shap'
    )
    
    # 特征相关性分析
    correlation_result = await analyzer.analyze_feature_correlation(hyperedge_ids)
    
    # 生成可视化
    analyzer.plot_feature_importance(
        importance_result['feature_importance'],
        save_path='feature_importance.png'
    )
    
    if 'shap_values' in importance_result:
        analyzer.plot_shap_summary(
            importance_result['shap_values'],
            X,  # 特征矩阵
            save_path='shap_summary.png'
        )
    
    analyzer.plot_correlation_heatmap(
        correlation_result['correlation_array'],
        save_path='correlation_heatmap.png'
    )
    
    # 生成综合报告
    report_path = analyzer.generate_analysis_report(
        importance_result,
        correlation_result,
        save_path='feature_analysis_report.md'
    )
    
    print(f"报告已保存到: {report_path}")

asyncio.run(generate_full_report())
```

### 比较不同方法

```python
from hypergraphrag.quality import compare_feature_importance_methods

# 比较三种方法的结果
comparison = compare_feature_importance_methods(
    analyzer,
    hyperedge_ids,
    ground_truth
)

for method, importance in comparison.items():
    print(f"\n{method} 方法:")
    for feature, value in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feature}: {value:.4f}")
```

## API 参考

### FeatureAnalyzer

#### `__init__(scorer)`

初始化特征分析器。

**参数:**
- `scorer`: QualityScorer 实例

#### `analyze_feature_importance(hyperedge_ids, ground_truth, method='shap')`

分析特征重要性。

**参数:**
- `hyperedge_ids`: 超边ID列表
- `ground_truth`: 超边ID到真实质量标签的映射 (0-1)
- `method`: 分析方法 ('shap', 'permutation', 'model_based')

**返回:**
```python
{
    'success': True,
    'method': 'shap',
    'num_samples': 100,
    'feature_importance': {
        'degree_centrality': 0.25,
        'betweenness': 0.15,
        'clustering': 0.10,
        'coherence': 0.35,
        'text_quality': 0.15
    },
    'shap_values': np.ndarray,  # 仅 SHAP 方法
    'model_performance': {
        'train_r2': 0.85,
        'test_r2': 0.78,
        'train_mse': 0.02,
        'test_mse': 0.03
    },
    'model': RandomForestRegressor
}
```

#### `analyze_feature_correlation(hyperedge_ids)`

分析特征之间的相关性。

**参数:**
- `hyperedge_ids`: 超边ID列表

**返回:**
```python
{
    'success': True,
    'num_samples': 100,
    'correlation_matrix': {
        'degree_centrality': {
            'degree_centrality': 1.0,
            'betweenness': 0.45,
            ...
        },
        ...
    },
    'high_correlation_pairs': [
        {
            'feature1': 'degree_centrality',
            'feature2': 'betweenness',
            'correlation': 0.75
        }
    ],
    'correlation_array': np.ndarray
}
```

#### `plot_feature_importance(feature_importance, save_path=None, title='Feature Importance')`

绘制特征重要性条形图。

**参数:**
- `feature_importance`: 特征重要性字典
- `save_path`: 保存路径（默认: `expr/analysis/feature_importance.png`）
- `title`: 图表标题

**返回:** 保存的文件路径

#### `plot_shap_summary(shap_values, X, save_path=None)`

绘制 SHAP 摘要图。

**参数:**
- `shap_values`: SHAP 值矩阵
- `X`: 特征矩阵
- `save_path`: 保存路径（默认: `expr/analysis/shap_summary.png`）

**返回:** 保存的文件路径

#### `plot_correlation_heatmap(correlation_matrix, save_path=None)`

绘制特征相关性热力图。

**参数:**
- `correlation_matrix`: 相关性矩阵（numpy 数组）
- `save_path`: 保存路径（默认: `expr/analysis/correlation_heatmap.png`）

**返回:** 保存的文件路径

#### `generate_analysis_report(importance_result, correlation_result=None, save_path=None)`

生成综合分析报告。

**参数:**
- `importance_result`: 特征重要性分析结果
- `correlation_result`: 特征相关性分析结果（可选）
- `save_path`: 保存路径（默认: `expr/analysis/feature_analysis_report.md`）

**返回:** 报告文件路径

## 特征说明

### 1. degree_centrality (度中心性)
- **定义**: 超边连接的实体数量（归一化）
- **意义**: 反映超边的连接广度，连接更多实体的超边可能更重要

### 2. betweenness (边介数中心性)
- **定义**: 经过该超边的最短路径数量
- **意义**: 反映超边的桥接作用，桥接不同子图的超边更重要

### 3. clustering (局部聚类系数)
- **定义**: 超边邻居之间的连接密度
- **意义**: 反映超边所在子图的紧密程度，处于密集子图的超边更可靠

### 4. coherence (超边一致性)
- **定义**: 超边内实体的语义相似度
- **意义**: 反映超边的语义连贯性，语义一致的实体更可能真正相关

### 5. text_quality (文本质量)
- **定义**: 源文本的语言质量和完整性
- **意义**: 反映超边的可靠性，来自高质量文本的超边更可靠

## 依赖项

### 必需
- numpy
- scikit-learn
- matplotlib
- seaborn

### 可选
- shap (用于 SHAP 分析)

安装可选依赖:
```bash
pip install shap
```

## 输出文件

默认情况下，所有输出文件保存在 `expr/analysis/` 目录：

- `feature_importance.png`: 特征重要性条形图
- `shap_summary.png`: SHAP 摘要图（如果使用 SHAP 方法）
- `correlation_heatmap.png`: 特征相关性热力图
- `feature_analysis_report.md`: 综合分析报告

## 最佳实践

1. **样本量**: 建议至少使用 50 个标注样本进行分析，样本越多结果越可靠

2. **方法选择**:
   - 研究用途：使用 SHAP 方法（最准确但较慢）
   - 快速分析：使用 model_based 方法
   - 平衡选择：使用 permutation 方法

3. **标注质量**: 确保 ground_truth 标签准确，可以使用多个标注者并计算一致性

4. **特征冗余**: 如果发现高度相关的特征对，考虑在轻量级版本中移除其中一个

5. **定期更新**: 随着数据集的变化，定期重新分析特征重要性

## 故障排除

### SHAP 安装失败
如果 SHAP 安装失败，可以使用其他方法：
```python
result = await analyzer.analyze_feature_importance(
    hyperedge_ids, ground_truth, method='model_based'
)
```

### 内存不足
对于大数据集，SHAP 可能消耗大量内存。解决方案：
- 使用采样（代码中已实现，默认最多 100 个样本）
- 使用 permutation 或 model_based 方法

### 可视化不显示
确保使用非交互式后端：
```python
import matplotlib
matplotlib.use('Agg')
```

## 相关文档

- [Quality Scorer](./scorer.py): 质量评分器
- [Graph Features](./features.py): 图结构特征提取
- [Coherence Metric](./coherence.py): 超边一致性度量
- [Design Document](../../.kiro/specs/dynhyperrag-quality-aware/design.md): 系统设计文档

## 引用

如果使用 SHAP 方法，请引用：
```
Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. 
Advances in neural information processing systems, 30.
```
