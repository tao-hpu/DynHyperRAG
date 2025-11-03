"""
图结构特征提取模块

实现超边质量评估所需的图结构特征：
1. 度中心性（Degree Centrality）
2. 边介数中心性（Edge Betweenness）
3. 局部聚类系数（Local Clustering Coefficient）
4. 文本质量（Text Quality）
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional
import networkx as nx
from collections import defaultdict


class GraphFeatureExtractor:
    """图结构特征提取器"""
    
    def __init__(self, knowledge_graph_inst):
        """
        初始化特征提取器
        
        Args:
            knowledge_graph_inst: 知识图谱实例（BaseGraphStorage）
        """
        self.graph = knowledge_graph_inst
        self._max_degree_cache = None
        self._betweenness_cache = {}
        
    async def compute_degree_centrality(self, hyperedge_id: str) -> float:
        """
        计算度中心性
        
        度中心性 = 超边连接的实体数量 / 图中最大连接数
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            归一化的度中心性分数 (0-1)
        """
        try:
            # 获取超边的度数（连接的实体数量）
            degree = await self.graph.node_degree(hyperedge_id)
            
            if degree == 0:
                return 0.0
            
            # 获取或计算最大度数
            if self._max_degree_cache is None:
                self._max_degree_cache = await self._compute_max_degree()
            
            # 归一化
            if self._max_degree_cache > 0:
                centrality = degree / self._max_degree_cache
            else:
                centrality = 0.0
            
            return min(1.0, centrality)
            
        except Exception as e:
            print(f"计算度中心性失败 {hyperedge_id}: {e}")
            return 0.5  # 默认值
    
    async def _compute_max_degree(self) -> int:
        """计算图中的最大度数"""
        # 简化实现：使用固定值或从配置读取
        # 在实际应用中，可以遍历所有节点找到最大度数
        return 20  # 假设最大连接20个实体
    
    async def compute_betweenness(self, hyperedge_id: str, 
                                 use_sampling: bool = True,
                                 sample_size: int = 100) -> float:
        """
        计算边介数中心性
        
        边介数 = 经过该超边的最短路径数量 / 所有最短路径数量
        
        Args:
            hyperedge_id: 超边节点ID
            use_sampling: 是否使用采样（大图优化）
            sample_size: 采样节点数量
            
        Returns:
            归一化的边介数中心性分数 (0-1)
        """
        try:
            # 检查缓存
            if hyperedge_id in self._betweenness_cache:
                return self._betweenness_cache[hyperedge_id]
            
            # 构建NetworkX图用于计算介数
            nx_graph = await self._build_networkx_graph(use_sampling, sample_size)
            
            if nx_graph.number_of_edges() == 0:
                return 0.0
            
            # 计算边介数中心性
            edge_betweenness = nx.edge_betweenness_centrality(nx_graph)
            
            # 查找超边对应的边
            betweenness_score = 0.0
            edges = await self.graph.get_node_edges(hyperedge_id)
            
            for src, dst, _ in edges:
                # 在NetworkX图中查找对应的边
                if nx_graph.has_edge(src, dst):
                    betweenness_score = max(betweenness_score, 
                                          edge_betweenness.get((src, dst), 0.0))
                elif nx_graph.has_edge(dst, src):
                    betweenness_score = max(betweenness_score,
                                          edge_betweenness.get((dst, src), 0.0))
            
            # 缓存结果
            self._betweenness_cache[hyperedge_id] = betweenness_score
            
            return betweenness_score
            
        except Exception as e:
            print(f"计算边介数失败 {hyperedge_id}: {e}")
            return 0.5  # 默认值
    
    async def _build_networkx_graph(self, use_sampling: bool = True,
                                   sample_size: int = 100) -> nx.Graph:
        """
        构建NetworkX图用于计算图算法
        
        Args:
            use_sampling: 是否采样（大图优化）
            sample_size: 采样大小
            
        Returns:
            NetworkX无向图
        """
        G = nx.Graph()
        
        # 简化实现：只构建实体-实体的投影图
        # 在实际应用中，需要遍历所有超边并添加边
        
        # TODO: 实现完整的图构建逻辑
        # 这里返回空图作为占位符
        
        return G
    
    async def compute_clustering(self, hyperedge_id: str) -> float:
        """
        计算局部聚类系数
        
        聚类系数 = 超边邻居之间的连接密度
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            局部聚类系数 (0-1)
        """
        try:
            # 1. 获取超边的邻居（通过共享实体连接的其他超边）
            neighbors = await self._get_hyperedge_neighbors(hyperedge_id)
            
            if len(neighbors) < 2:
                return 0.0  # 邻居太少，无法计算聚类
            
            # 2. 计算邻居之间的连接数
            connections = 0
            for i, neighbor1 in enumerate(neighbors):
                for neighbor2 in neighbors[i+1:]:
                    if await self._are_neighbors(neighbor1, neighbor2):
                        connections += 1
            
            # 3. 计算聚类系数
            k = len(neighbors)
            max_connections = k * (k - 1) / 2
            
            if max_connections > 0:
                clustering = connections / max_connections
            else:
                clustering = 0.0
            
            return clustering
            
        except Exception as e:
            print(f"计算聚类系数失败 {hyperedge_id}: {e}")
            return 0.5  # 默认值
    
    async def _get_hyperedge_neighbors(self, hyperedge_id: str) -> List[str]:
        """
        获取超边的邻居超边（通过共享实体连接）
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            邻居超边ID列表
        """
        neighbors = set()
        
        # 1. 获取超边连接的所有实体
        edges = await self.graph.get_node_edges(hyperedge_id)
        entity_ids = [dst for src, dst, _ in edges if src == hyperedge_id]
        
        # 2. 对每个实体，找到连接它的其他超边
        for entity_id in entity_ids:
            entity_edges = await self.graph.get_node_edges(entity_id)
            for src, dst, _ in entity_edges:
                other_hyperedge = src if src != entity_id else dst
                if other_hyperedge != hyperedge_id:
                    # 检查是否是超边节点
                    node = await self.graph.get_node(other_hyperedge)
                    if node and node.get('role') == 'hyperedge':
                        neighbors.add(other_hyperedge)
        
        return list(neighbors)
    
    async def _are_neighbors(self, hyperedge1: str, hyperedge2: str) -> bool:
        """
        检查两个超边是否是邻居（共享至少一个实体）
        
        Args:
            hyperedge1: 第一个超边ID
            hyperedge2: 第二个超边ID
            
        Returns:
            是否是邻居
        """
        # 获取两个超边的实体
        edges1 = await self.graph.get_node_edges(hyperedge1)
        entities1 = set(dst for src, dst, _ in edges1 if src == hyperedge1)
        
        edges2 = await self.graph.get_node_edges(hyperedge2)
        entities2 = set(dst for src, dst, _ in edges2 if src == hyperedge2)
        
        # 检查是否有共享实体
        return len(entities1 & entities2) > 0
    
    async def compute_text_quality(self, hyperedge_id: str) -> float:
        """
        计算文本质量分数
        
        评估指标：
        1. 文本长度（适中为好）
        2. 完整性（是否有完整的句子）
        3. 信息密度
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            文本质量分数 (0-1)
        """
        try:
            # 获取超边节点数据
            node = await self.graph.get_node(hyperedge_id)
            if not node:
                return 0.0
            
            text = node.get('hyperedge', '')
            if not text:
                return 0.0
            
            # 1. 长度分数（理想长度：50-200字符）
            length = len(text)
            if length < 20:
                length_score = length / 20.0
            elif length <= 200:
                length_score = 1.0
            else:
                length_score = max(0.5, 1.0 - (length - 200) / 500.0)
            
            # 2. 完整性分数（是否有句号、问号等）
            completeness_score = 1.0 if any(p in text for p in '.!?。！？') else 0.5
            
            # 3. 信息密度（实体数量 / 文本长度）
            edges = await self.graph.get_node_edges(hyperedge_id)
            num_entities = len([e for e in edges if e[0] == hyperedge_id])
            density_score = min(1.0, num_entities / max(1, length / 50))
            
            # 综合评分
            quality = (length_score * 0.4 + 
                      completeness_score * 0.3 + 
                      density_score * 0.3)
            
            return quality
            
        except Exception as e:
            print(f"计算文本质量失败 {hyperedge_id}: {e}")
            return 0.5  # 默认值
    
    async def extract_all_features(self, hyperedge_id: str) -> Dict[str, float]:
        """
        提取所有图结构特征
        
        Args:
            hyperedge_id: 超边节点ID
            
        Returns:
            特征字典
        """
        # 并行计算所有特征
        results = await asyncio.gather(
            self.compute_degree_centrality(hyperedge_id),
            self.compute_betweenness(hyperedge_id),
            self.compute_clustering(hyperedge_id),
            self.compute_text_quality(hyperedge_id),
            return_exceptions=True
        )
        
        # 处理异常
        features = {
            'degree_centrality': results[0] if not isinstance(results[0], Exception) else 0.5,
            'betweenness': results[1] if not isinstance(results[1], Exception) else 0.5,
            'clustering': results[2] if not isinstance(results[2], Exception) else 0.5,
            'text_quality': results[3] if not isinstance(results[3], Exception) else 0.5,
        }
        
        return features
    
    def clear_cache(self):
        """清除缓存"""
        self._betweenness_cache.clear()
        self._max_degree_cache = None


# 辅助函数
def normalize_features(features: Dict[str, float]) -> Dict[str, float]:
    """
    归一化特征到 [0, 1] 范围
    
    Args:
        features: 原始特征字典
        
    Returns:
        归一化后的特征字典
    """
    normalized = {}
    for key, value in features.items():
        normalized[key] = max(0.0, min(1.0, value))
    return normalized
