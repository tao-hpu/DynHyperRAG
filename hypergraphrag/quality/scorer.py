"""
质量评分器模块

集成所有质量特征，计算超边的综合质量分数。
支持无监督（固定权重）和有监督（学习权重）两种模式。
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from .features import GraphFeatureExtractor, normalize_features
from .coherence import CoherenceMetric


class QualityScorer:
    """超边质量评分器"""
    
    def __init__(self, 
                 knowledge_graph_inst,
                 embedding_func: Callable,
                 config: Optional[Dict] = None):
        """
        初始化质量评分器
        
        Args:
            knowledge_graph_inst: 知识图谱实例（BaseGraphStorage）
            embedding_func: 嵌入函数
            config: 配置字典，包含特征权重等参数
        """
        self.graph = knowledge_graph_inst
        self.embedding_func = embedding_func
        
        # 初始化特征提取器
        self.feature_extractor = GraphFeatureExtractor(knowledge_graph_inst)
        self.coherence_metric = CoherenceMetric(embedding_func, knowledge_graph_inst)
        
        # 配置参数
        self.config = config or {}
        self.mode = self.config.get('quality_mode', 'unsupervised')
        
        # 特征权重（无监督模式）
        self.feature_weights = self.config.get('quality_feature_weights', {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        })
        
        # 验证权重和为1
        weight_sum = sum(self.feature_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            print(f"警告：特征权重和为 {weight_sum}，已归一化")
            self.feature_weights = {
                k: v / weight_sum for k, v in self.feature_weights.items()
            }
        
        # 有监督模式的模型
        self.supervised_model = None
        
    async def compute_quality_score(self, hyperedge_id: str) -> Dict:
        """
        计算超边的质量分数
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            包含质量分数和特征的字典
        """
        try:
            # 1. 提取所有特征
            features = await self._extract_all_features(hyperedge_id)
            
            # 2. 归一化特征
            normalized_features = normalize_features(features)
            
            # 3. 计算质量分数
            if self.mode == 'supervised' and self.supervised_model is not None:
                quality_score = self._compute_supervised_score(normalized_features)
            else:
                quality_score = self._compute_unsupervised_score(normalized_features)
            
            return {
                'quality_score': quality_score,
                'features': normalized_features,
                'mode': self.mode
            }
            
        except Exception as e:
            print(f"计算质量分数失败 {hyperedge_id}: {e}")
            return {
                'quality_score': 0.5,
                'features': {},
                'error': str(e)
            }
    
    async def _extract_all_features(self, hyperedge_id: str) -> Dict[str, float]:
        """
        提取所有质量特征
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            特征字典
        """
        # 并行提取图结构特征和一致性
        graph_features_task = self.feature_extractor.extract_all_features(hyperedge_id)
        coherence_task = self.coherence_metric.compute_coherence(hyperedge_id)
        
        graph_features, coherence = await asyncio.gather(
            graph_features_task,
            coherence_task,
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(graph_features, Exception):
            print(f"提取图特征失败: {graph_features}")
            graph_features = {
                'degree_centrality': 0.5,
                'betweenness': 0.5,
                'clustering': 0.5,
                'text_quality': 0.5
            }
        
        if isinstance(coherence, Exception):
            print(f"计算一致性失败: {coherence}")
            coherence = 0.5
        
        # 合并所有特征
        all_features = {
            **graph_features,
            'coherence': coherence
        }
        
        return all_features
    
    def _compute_unsupervised_score(self, features: Dict[str, float]) -> float:
        """
        无监督模式：使用固定权重计算质量分数
        
        Args:
            features: 归一化后的特征字典
            
        Returns:
            质量分数 (0-1)
        """
        quality_score = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            feature_value = features.get(feature_name, 0.5)
            quality_score += weight * feature_value
        
        return max(0.0, min(1.0, quality_score))
    
    def _compute_supervised_score(self, features: Dict[str, float]) -> float:
        """
        有监督模式：使用学习的模型计算质量分数
        
        Args:
            features: 归一化后的特征字典
            
        Returns:
            质量分数 (0-1)
        """
        if self.supervised_model is None:
            # 回退到无监督模式
            return self._compute_unsupervised_score(features)
        
        # 构建特征向量
        feature_vector = self._features_to_vector(features)
        
        # 使用模型预测
        try:
            score = self.supervised_model.predict([feature_vector])[0]
            return max(0.0, min(1.0, float(score)))
        except Exception as e:
            print(f"有监督预测失败: {e}")
            return self._compute_unsupervised_score(features)
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """
        将特征字典转换为向量
        
        Args:
            features: 特征字典
            
        Returns:
            特征向量
        """
        feature_order = [
            'degree_centrality',
            'betweenness',
            'clustering',
            'coherence',
            'text_quality'
        ]
        
        vector = [features.get(f, 0.5) for f in feature_order]
        return np.array(vector)
    
    async def batch_compute_quality(self, 
                                   hyperedge_ids: List[str],
                                   show_progress: bool = False) -> Dict[str, Dict]:
        """
        批量计算多个超边的质量分数
        
        Args:
            hyperedge_ids: 超边ID列表
            show_progress: 是否显示进度条
            
        Returns:
            超边ID到质量结果的映射
        """
        if show_progress:
            try:
                from tqdm.asyncio import tqdm_asyncio
                results = await tqdm_asyncio.gather(*[
                    self.compute_quality_score(he_id)
                    for he_id in hyperedge_ids
                ], desc="计算质量分数")
            except ImportError:
                print("警告：tqdm未安装，无法显示进度条")
                results = await asyncio.gather(*[
                    self.compute_quality_score(he_id)
                    for he_id in hyperedge_ids
                ])
        else:
            results = await asyncio.gather(*[
                self.compute_quality_score(he_id)
                for he_id in hyperedge_ids
            ], return_exceptions=True)
        
        # 构建结果字典
        quality_results = {}
        for he_id, result in zip(hyperedge_ids, results):
            if isinstance(result, Exception):
                quality_results[he_id] = {
                    'quality_score': 0.5,
                    'error': str(result)
                }
            else:
                quality_results[he_id] = result
        
        return quality_results
    
    async def train_supervised_model(self,
                                    hyperedge_ids: List[str],
                                    ground_truth_labels: Dict[str, float],
                                    model_type: str = 'random_forest') -> Dict:
        """
        训练有监督质量评估模型
        
        Args:
            hyperedge_ids: 训练数据的超边ID列表
            ground_truth_labels: 超边ID到真实质量标签的映射 (0-1)
            model_type: 模型类型 ('linear', 'random_forest', 'gradient_boosting')
            
        Returns:
            训练结果字典
        """
        try:
            # 1. 提取特征
            print(f"提取 {len(hyperedge_ids)} 个超边的特征...")
            quality_results = await self.batch_compute_quality(hyperedge_ids)
            
            # 2. 构建训练数据
            X = []
            y = []
            valid_ids = []
            
            for he_id in hyperedge_ids:
                if he_id in ground_truth_labels and he_id in quality_results:
                    features = quality_results[he_id].get('features', {})
                    if features:
                        X.append(self._features_to_vector(features))
                        y.append(ground_truth_labels[he_id])
                        valid_ids.append(he_id)
            
            if len(X) < 10:
                return {
                    'success': False,
                    'error': f'训练数据不足：只有 {len(X)} 个样本'
                }
            
            X = np.array(X)
            y = np.array(y)
            
            print(f"训练数据：{len(X)} 个样本")
            
            # 3. 训练模型
            if model_type == 'linear':
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
            elif model_type == 'random_forest':
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
            elif model_type == 'gradient_boosting':
                from sklearn.ensemble import GradientBoostingRegressor
                model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
            else:
                return {
                    'success': False,
                    'error': f'未知的模型类型: {model_type}'
                }
            
            model.fit(X, y)
            
            # 4. 评估模型
            from sklearn.metrics import mean_squared_error, r2_score
            y_pred = model.predict(X)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            
            # 5. 保存模型
            self.supervised_model = model
            self.mode = 'supervised'
            
            # 6. 特征重要性（如果支持）
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                feature_names = [
                    'degree_centrality',
                    'betweenness',
                    'clustering',
                    'coherence',
                    'text_quality'
                ]
                feature_importance = dict(zip(feature_names, model.feature_importances_))
            
            return {
                'success': True,
                'model_type': model_type,
                'num_samples': len(X),
                'mse': float(mse),
                'r2': float(r2),
                'feature_importance': feature_importance
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_graph_with_quality_scores(self,
                                              hyperedge_ids: List[str],
                                              show_progress: bool = True):
        """
        计算质量分数并更新到图中
        
        Args:
            hyperedge_ids: 超边ID列表
            show_progress: 是否显示进度条
        """
        # 批量计算质量分数
        quality_results = await self.batch_compute_quality(hyperedge_ids, show_progress)
        
        # 更新图中的节点数据
        update_tasks = []
        for he_id, result in quality_results.items():
            if 'error' not in result:
                # 获取当前节点数据
                node = await self.graph.get_node(he_id)
                if node:
                    # 更新质量相关字段
                    node['quality_score'] = result['quality_score']
                    node['quality_features'] = result['features']
                    
                    # 如果没有动态权重，初始化为质量分数
                    if 'dynamic_weight' not in node:
                        node['dynamic_weight'] = result['quality_score']
                    
                    # 更新节点
                    update_tasks.append(self.graph.upsert_node(he_id, node))
        
        # 批量更新
        if update_tasks:
            await asyncio.gather(*update_tasks)
            print(f"已更新 {len(update_tasks)} 个超边的质量分数")
    
    def get_feature_weights(self) -> Dict[str, float]:
        """获取当前特征权重"""
        if self.mode == 'supervised' and self.supervised_model is not None:
            if hasattr(self.supervised_model, 'feature_importances_'):
                feature_names = [
                    'degree_centrality',
                    'betweenness',
                    'clustering',
                    'coherence',
                    'text_quality'
                ]
                return dict(zip(feature_names, self.supervised_model.feature_importances_))
        
        return self.feature_weights.copy()
    
    def set_feature_weights(self, weights: Dict[str, float]):
        """
        设置特征权重（无监督模式）
        
        Args:
            weights: 新的特征权重字典
        """
        # 验证权重和为1
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            print(f"警告：特征权重和为 {weight_sum}，已归一化")
            weights = {k: v / weight_sum for k, v in weights.items()}
        
        self.feature_weights = weights
        self.mode = 'unsupervised'
    
    def clear_cache(self):
        """清除所有缓存"""
        self.feature_extractor.clear_cache()
        self.coherence_metric.clear_cache()


# 辅助函数
def compute_quality_statistics(quality_results: Dict[str, Dict]) -> Dict:
    """
    计算质量分数的统计信息
    
    Args:
        quality_results: 超边ID到质量结果的映射
        
    Returns:
        统计信息字典
    """
    scores = [r['quality_score'] for r in quality_results.values() 
              if 'quality_score' in r]
    
    if not scores:
        return {}
    
    return {
        'mean': float(np.mean(scores)),
        'std': float(np.std(scores)),
        'min': float(np.min(scores)),
        'max': float(np.max(scores)),
        'median': float(np.median(scores)),
        'q25': float(np.percentile(scores, 25)),
        'q75': float(np.percentile(scores, 75)),
        'count': len(scores)
    }


def analyze_feature_distribution(quality_results: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    分析各特征的分布
    
    Args:
        quality_results: 超边ID到质量结果的映射
        
    Returns:
        特征名到统计信息的映射
    """
    feature_values = {}
    
    # 收集所有特征值
    for result in quality_results.values():
        features = result.get('features', {})
        for feature_name, value in features.items():
            if feature_name not in feature_values:
                feature_values[feature_name] = []
            feature_values[feature_name].append(value)
    
    # 计算每个特征的统计信息
    feature_stats = {}
    for feature_name, values in feature_values.items():
        if values:
            feature_stats[feature_name] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'median': float(np.median(values))
            }
    
    return feature_stats
