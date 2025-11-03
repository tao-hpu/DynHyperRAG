"""
特征重要性分析模块

使用 SHAP（SHapley Additive exPlanations）分析质量特征的重要性。
支持特征重要性排序、可视化和相关性分析。
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns


class FeatureAnalyzer:
    """特征重要性分析器"""
    
    def __init__(self, scorer):
        """
        初始化特征分析器
        
        Args:
            scorer: QualityScorer 实例
        """
        self.scorer = scorer
        self.feature_names = [
            'degree_centrality',
            'betweenness',
            'clustering',
            'coherence',
            'text_quality'
        ]
    
    async def analyze_feature_importance(self,
                                        hyperedge_ids: List[str],
                                        ground_truth: Dict[str, float],
                                        method: str = 'shap') -> Dict:
        """
        分析特征重要性
        
        Args:
            hyperedge_ids: 超边ID列表
            ground_truth: 超边ID到真实质量标签的映射
            method: 分析方法 ('shap', 'permutation', 'model_based')
            
        Returns:
            特征重要性分析结果
        """
        try:
            # 1. 收集所有超边的特征
            print(f"收集 {len(hyperedge_ids)} 个超边的特征...")
            features_list = []
            labels = []
            valid_ids = []
            
            for he_id in hyperedge_ids:
                if he_id in ground_truth:
                    result = await self.scorer.compute_quality_score(he_id)
                    features = result.get('features', {})
                    
                    if features and len(features) == len(self.feature_names):
                        features_list.append(self._features_to_vector(features))
                        labels.append(ground_truth[he_id])
                        valid_ids.append(he_id)
            
            if len(features_list) < 10:
                return {
                    'success': False,
                    'error': f'数据不足：只有 {len(features_list)} 个有效样本'
                }
            
            X = np.array(features_list)
            y = np.array(labels)
            
            print(f"有效样本数：{len(X)}")
            
            # 2. 训练模型
            from sklearn.ensemble import RandomForestRegressor
            from sklearn.model_selection import train_test_split
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # 3. 计算特征重要性
            if method == 'shap':
                importance_result = self._compute_shap_importance(model, X, y)
            elif method == 'permutation':
                importance_result = self._compute_permutation_importance(model, X_test, y_test)
            elif method == 'model_based':
                importance_result = self._compute_model_importance(model)
            else:
                return {
                    'success': False,
                    'error': f'未知的分析方法: {method}'
                }
            
            # 4. 评估模型性能
            from sklearn.metrics import mean_squared_error, r2_score
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            train_mse = mean_squared_error(y_train, y_pred_train)
            test_mse = mean_squared_error(y_test, y_pred_test)
            train_r2 = r2_score(y_train, y_pred_train)
            test_r2 = r2_score(y_test, y_pred_test)
            
            return {
                'success': True,
                'method': method,
                'num_samples': len(X),
                'feature_importance': importance_result['feature_importance'],
                'shap_values': importance_result.get('shap_values'),
                'model_performance': {
                    'train_mse': float(train_mse),
                    'test_mse': float(test_mse),
                    'train_r2': float(train_r2),
                    'test_r2': float(test_r2)
                },
                'model': model
            }
            
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        将特征字典转换为向量
        
        Args:
            features: 特征字典
            
        Returns:
            特征向量
        """
        vector = [features.get(f, 0.5) for f in self.feature_names]
        return np.array(vector)
    
    def _compute_shap_importance(self, model, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        使用 SHAP 计算特征重要性
        
        Args:
            model: 训练好的模型
            X: 特征矩阵
            y: 标签向量
            
        Returns:
            包含特征重要性和 SHAP 值的字典
        """
        try:
            import shap
            
            # 创建 SHAP 解释器
            explainer = shap.TreeExplainer(model)
            
            # 计算 SHAP 值（使用子集以提高速度）
            sample_size = min(100, len(X))
            sample_indices = np.random.choice(len(X), sample_size, replace=False)
            X_sample = X[sample_indices]
            
            shap_values = explainer.shap_values(X_sample)
            
            # 计算平均绝对 SHAP 值作为特征重要性
            importance = np.abs(shap_values).mean(axis=0)
            
            # 归一化
            importance = importance / importance.sum()
            
            feature_importance = dict(zip(self.feature_names, importance))
            
            return {
                'feature_importance': feature_importance,
                'shap_values': shap_values,
                'explainer': explainer
            }
            
        except ImportError:
            print("警告：shap 库未安装，回退到模型内置重要性")
            return self._compute_model_importance(model)
        except Exception as e:
            print(f"SHAP 计算失败: {e}，回退到模型内置重要性")
            return self._compute_model_importance(model)
    
    def _compute_permutation_importance(self, model, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        使用排列重要性计算特征重要性
        
        Args:
            model: 训练好的模型
            X: 特征矩阵
            y: 标签向量
            
        Returns:
            包含特征重要性的字典
        """
        from sklearn.inspection import permutation_importance
        
        result = permutation_importance(
            model, X, y,
            n_repeats=10,
            random_state=42,
            n_jobs=-1
        )
        
        importance = result.importances_mean
        importance = importance / importance.sum()
        
        feature_importance = dict(zip(self.feature_names, importance))
        
        return {
            'feature_importance': feature_importance,
            'importances_std': dict(zip(self.feature_names, result.importances_std))
        }
    
    def _compute_model_importance(self, model) -> Dict:
        """
        使用模型内置的特征重要性
        
        Args:
            model: 训练好的模型
            
        Returns:
            包含特征重要性的字典
        """
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            importance = importance / importance.sum()
            
            feature_importance = dict(zip(self.feature_names, importance))
            
            return {
                'feature_importance': feature_importance
            }
        else:
            # 如果模型不支持，返回均匀分布
            uniform_importance = 1.0 / len(self.feature_names)
            feature_importance = {name: uniform_importance for name in self.feature_names}
            
            return {
                'feature_importance': feature_importance
            }
    
    def plot_feature_importance(self,
                               feature_importance: Dict[str, float],
                               save_path: Optional[str] = None,
                               title: str = "Feature Importance") -> str:
        """
        绘制特征重要性图
        
        Args:
            feature_importance: 特征重要性字典
            save_path: 保存路径（如果为 None，自动生成）
            title: 图表标题
            
        Returns:
            保存的文件路径
        """
        # 排序特征
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        features = [f[0] for f in sorted_features]
        importance = [f[1] for f in sorted_features]
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        plt.barh(features, importance, color='steelblue')
        plt.xlabel('Importance', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # 保存图表
        if save_path is None:
            import os
            os.makedirs('expr/analysis', exist_ok=True)
            save_path = 'expr/analysis/feature_importance.png'
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"特征重要性图已保存到: {save_path}")
        return save_path
    
    def plot_shap_summary(self,
                         shap_values: np.ndarray,
                         X: np.ndarray,
                         save_path: Optional[str] = None) -> str:
        """
        绘制 SHAP 摘要图
        
        Args:
            shap_values: SHAP 值矩阵
            X: 特征矩阵
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        try:
            import shap
            
            plt.figure(figsize=(10, 6))
            shap.summary_plot(
                shap_values, X,
                feature_names=self.feature_names,
                show=False
            )
            
            if save_path is None:
                import os
                os.makedirs('expr/analysis', exist_ok=True)
                save_path = 'expr/analysis/shap_summary.png'
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"SHAP 摘要图已保存到: {save_path}")
            return save_path
            
        except ImportError:
            print("警告：shap 库未安装，无法生成 SHAP 摘要图")
            return ""
        except Exception as e:
            print(f"生成 SHAP 摘要图失败: {e}")
            return ""
    
    async def analyze_feature_correlation(self,
                                         hyperedge_ids: List[str]) -> Dict:
        """
        分析特征之间的相关性
        
        Args:
            hyperedge_ids: 超边ID列表
            
        Returns:
            相关性分析结果
        """
        try:
            # 1. 收集特征
            print(f"收集 {len(hyperedge_ids)} 个超边的特征...")
            features_list = []
            
            for he_id in hyperedge_ids:
                result = await self.scorer.compute_quality_score(he_id)
                features = result.get('features', {})
                
                if features and len(features) == len(self.feature_names):
                    features_list.append(self._features_to_vector(features))
            
            if len(features_list) < 10:
                return {
                    'success': False,
                    'error': f'数据不足：只有 {len(features_list)} 个有效样本'
                }
            
            X = np.array(features_list)
            
            # 2. 计算相关性矩阵
            correlation_matrix = np.corrcoef(X.T)
            
            # 3. 转换为字典格式
            correlation_dict = {}
            for i, name1 in enumerate(self.feature_names):
                correlation_dict[name1] = {}
                for j, name2 in enumerate(self.feature_names):
                    correlation_dict[name1][name2] = float(correlation_matrix[i, j])
            
            # 4. 识别高度相关的特征对
            high_correlation_pairs = []
            threshold = 0.7
            
            for i in range(len(self.feature_names)):
                for j in range(i + 1, len(self.feature_names)):
                    corr = abs(correlation_matrix[i, j])
                    if corr > threshold:
                        high_correlation_pairs.append({
                            'feature1': self.feature_names[i],
                            'feature2': self.feature_names[j],
                            'correlation': float(correlation_matrix[i, j])
                        })
            
            return {
                'success': True,
                'num_samples': len(X),
                'correlation_matrix': correlation_dict,
                'high_correlation_pairs': high_correlation_pairs,
                'correlation_array': correlation_matrix
            }
            
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def plot_correlation_heatmap(self,
                                correlation_matrix: np.ndarray,
                                save_path: Optional[str] = None) -> str:
        """
        绘制特征相关性热力图
        
        Args:
            correlation_matrix: 相关性矩阵
            save_path: 保存路径
            
        Returns:
            保存的文件路径
        """
        plt.figure(figsize=(10, 8))
        
        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            xticklabels=self.feature_names,
            yticklabels=self.feature_names,
            cbar_kws={'label': 'Correlation'}
        )
        
        plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path is None:
            import os
            os.makedirs('expr/analysis', exist_ok=True)
            save_path = 'expr/analysis/correlation_heatmap.png'
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"相关性热力图已保存到: {save_path}")
        return save_path
    
    def generate_analysis_report(self,
                                importance_result: Dict,
                                correlation_result: Optional[Dict] = None,
                                save_path: Optional[str] = None) -> str:
        """
        生成特征分析报告
        
        Args:
            importance_result: 特征重要性分析结果
            correlation_result: 特征相关性分析结果（可选）
            save_path: 保存路径
            
        Returns:
            报告文件路径
        """
        if save_path is None:
            import os
            os.makedirs('expr/analysis', exist_ok=True)
            save_path = 'expr/analysis/feature_analysis_report.md'
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("# 特征重要性分析报告\n\n")
            
            # 1. 基本信息
            f.write("## 1. 分析概览\n\n")
            f.write(f"- **分析方法**: {importance_result.get('method', 'N/A')}\n")
            f.write(f"- **样本数量**: {importance_result.get('num_samples', 'N/A')}\n")
            
            if 'model_performance' in importance_result:
                perf = importance_result['model_performance']
                f.write(f"- **训练集 R²**: {perf.get('train_r2', 0):.4f}\n")
                f.write(f"- **测试集 R²**: {perf.get('test_r2', 0):.4f}\n")
                f.write(f"- **训练集 MSE**: {perf.get('train_mse', 0):.4f}\n")
                f.write(f"- **测试集 MSE**: {perf.get('test_mse', 0):.4f}\n")
            
            f.write("\n")
            
            # 2. 特征重要性
            f.write("## 2. 特征重要性排序\n\n")
            
            feature_importance = importance_result.get('feature_importance', {})
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            f.write("| 排名 | 特征 | 重要性 | 百分比 |\n")
            f.write("|------|------|--------|--------|\n")
            
            for rank, (feature, importance) in enumerate(sorted_features, 1):
                f.write(f"| {rank} | {feature} | {importance:.4f} | {importance*100:.2f}% |\n")
            
            f.write("\n")
            
            # 3. 特征解释
            f.write("## 3. 特征解释\n\n")
            
            feature_descriptions = {
                'degree_centrality': '度中心性：超边连接的实体数量，反映超边的连接广度',
                'betweenness': '边介数中心性：经过该超边的最短路径数量，反映超边的桥接作用',
                'clustering': '局部聚类系数：超边邻居之间的连接密度，反映超边所在子图的紧密程度',
                'coherence': '超边一致性：超边内实体的语义相似度，反映超边的语义连贯性',
                'text_quality': '文本质量：源文本的语言质量和完整性，反映超边的可靠性'
            }
            
            for feature, importance in sorted_features:
                desc = feature_descriptions.get(feature, '无描述')
                f.write(f"### {feature}\n\n")
                f.write(f"- **重要性**: {importance:.4f} ({importance*100:.2f}%)\n")
                f.write(f"- **描述**: {desc}\n\n")
            
            # 4. 相关性分析
            if correlation_result and correlation_result.get('success'):
                f.write("## 4. 特征相关性分析\n\n")
                
                high_corr = correlation_result.get('high_correlation_pairs', [])
                if high_corr:
                    f.write("### 高度相关的特征对（|相关系数| > 0.7）\n\n")
                    f.write("| 特征1 | 特征2 | 相关系数 |\n")
                    f.write("|-------|-------|----------|\n")
                    
                    for pair in high_corr:
                        f.write(f"| {pair['feature1']} | {pair['feature2']} | {pair['correlation']:.4f} |\n")
                    
                    f.write("\n**注意**: 高度相关的特征可能存在冗余，可以考虑移除其中一个。\n\n")
                else:
                    f.write("未发现高度相关的特征对（|相关系数| > 0.7）。\n\n")
            
            # 5. 建议
            f.write("## 5. 优化建议\n\n")
            
            # 根据重要性给出建议
            top_feature = sorted_features[0][0]
            top_importance = sorted_features[0][1]
            
            if top_importance > 0.4:
                f.write(f"- **主导特征**: {top_feature} 的重要性显著高于其他特征（{top_importance*100:.2f}%），")
                f.write("建议重点优化该特征的计算准确性。\n")
            
            low_importance_features = [f for f, i in sorted_features if i < 0.1]
            if low_importance_features:
                f.write(f"- **低重要性特征**: {', '.join(low_importance_features)} 的重要性较低，")
                f.write("可以考虑在轻量级版本中移除以提高效率。\n")
            
            if correlation_result and len(correlation_result.get('high_correlation_pairs', [])) > 0:
                f.write("- **特征冗余**: 存在高度相关的特征对，建议进行特征选择以减少冗余。\n")
            
            f.write("\n")
            
            # 6. 结论
            f.write("## 6. 结论\n\n")
            f.write(f"基于 {importance_result.get('num_samples', 'N/A')} 个样本的分析，")
            f.write(f"特征重要性排序为：{' > '.join([f[0] for f in sorted_features])}。\n")
            f.write("该分析结果可用于指导特征工程和模型优化。\n")
        
        print(f"分析报告已保存到: {save_path}")
        return save_path


# 辅助函数
def compare_feature_importance_methods(analyzer: FeatureAnalyzer,
                                      hyperedge_ids: List[str],
                                      ground_truth: Dict[str, float]) -> Dict:
    """
    比较不同特征重要性分析方法的结果
    
    Args:
        analyzer: FeatureAnalyzer 实例
        hyperedge_ids: 超边ID列表
        ground_truth: 真实标签
        
    Returns:
        比较结果
    """
    import asyncio
    
    async def run_comparison():
        methods = ['shap', 'permutation', 'model_based']
        results = {}
        
        for method in methods:
            print(f"\n使用 {method} 方法分析...")
            result = await analyzer.analyze_feature_importance(
                hyperedge_ids, ground_truth, method=method
            )
            
            if result.get('success'):
                results[method] = result['feature_importance']
        
        return results
    
    return asyncio.run(run_comparison())
