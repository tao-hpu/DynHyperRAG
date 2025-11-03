"""
超边一致性度量模块

实现基于实体嵌入相似度的超边一致性评估。
一致性高的超边表示其连接的实体在语义上相关。
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Callable
from collections import defaultdict


class CoherenceMetric:
    """超边一致性度量器"""
    
    def __init__(self, embedding_func: Callable, knowledge_graph_inst, 
                 use_persistent_cache: bool = True):
        """
        初始化一致性度量器
        
        Args:
            embedding_func: 嵌入函数，接收文本列表返回嵌入向量列表
            knowledge_graph_inst: 知识图谱实例（BaseGraphStorage）
            use_persistent_cache: 是否使用持久化缓存（存储在实体节点中）
        """
        self.embedding_func = embedding_func
        self.graph = knowledge_graph_inst
        self._embedding_cache = {}  # 内存缓存：实体ID -> 嵌入向量
        self.use_persistent_cache = use_persistent_cache  # 是否使用持久化缓存
        
    async def compute_coherence(self, hyperedge_id: str, 
                               variance_penalty: float = 0.5) -> float:
        """
        计算超边一致性分数
        
        一致性 = 平均成对相似度 - λ × 方差
        
        Args:
            hyperedge_id: 超边节点ID
            variance_penalty: 方差惩罚系数（默认0.5）
            
        Returns:
            一致性分数 (0-1)
        """
        try:
            # 1. 获取超边连接的所有实体
            edges = await self.graph.get_node_edges(hyperedge_id)
            entity_ids = [dst for src, dst, _ in edges if src == hyperedge_id]
            
            if len(entity_ids) < 2:
                return 1.0  # 单实体超边默认完全一致
            
            # 2. 获取实体嵌入
            embeddings = await self._get_entity_embeddings(entity_ids)
            
            if len(embeddings) < 2:
                return 0.5  # 无法计算，返回中性值
            
            # 3. 计算成对余弦相似度
            similarities = self._compute_pairwise_similarities(embeddings)
            
            if not similarities:
                return 0.5
            
            # 4. 计算平均相似度和方差
            mean_sim = np.mean(similarities)
            var_sim = np.var(similarities)
            
            # 5. 一致性分数 = 平均相似度 - 方差惩罚
            coherence = mean_sim - variance_penalty * var_sim
            
            # 6. 归一化到 [0, 1]
            coherence = max(0.0, min(1.0, coherence))
            
            return coherence
            
        except Exception as e:
            print(f"计算一致性失败 {hyperedge_id}: {e}")
            return 0.5  # 默认值
    
    async def _get_entity_embeddings(self, entity_ids: List[str]) -> List[np.ndarray]:
        """
        获取实体嵌入（使用两级缓存：内存缓存 + 持久化缓存）
        
        优化策略：
        1. 首先检查内存缓存（最快）
        2. 然后检查持久化缓存（存储在实体节点中）
        3. 最后批量计算未缓存的嵌入
        
        Args:
            entity_ids: 实体ID列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        nodes_to_update = []  # 需要更新持久化缓存的节点
        
        # 1. 检查内存缓存和持久化缓存
        for i, entity_id in enumerate(entity_ids):
            # 1.1 检查内存缓存
            if entity_id in self._embedding_cache:
                embeddings.append(self._embedding_cache[entity_id])
                continue
            
            # 1.2 获取实体节点
            node = await self.graph.get_node(entity_id)
            if not node:
                continue
            
            # 1.3 检查持久化缓存
            if self.use_persistent_cache and 'embedding_cache' in node:
                cached_emb = node['embedding_cache']
                if cached_emb is not None and len(cached_emb) > 0:
                    # 从持久化缓存加载到内存缓存
                    emb_array = np.array(cached_emb)
                    self._embedding_cache[entity_id] = emb_array
                    embeddings.append(emb_array)
                    continue
            
            # 1.4 需要计算嵌入
            entity_text = self._get_entity_text(node)
            texts_to_embed.append(entity_text)
            indices_to_embed.append((i, entity_id, node))
        
        # 2. 批量计算未缓存的嵌入
        if texts_to_embed:
            new_embeddings = await self.embedding_func(texts_to_embed)
            
            # 转换为numpy数组并缓存
            for (idx, entity_id, node), emb in zip(indices_to_embed, new_embeddings):
                emb_array = np.array(emb) if not isinstance(emb, np.ndarray) else emb
                
                # 存储到内存缓存
                self._embedding_cache[entity_id] = emb_array
                embeddings.insert(idx, emb_array)
                
                # 准备更新持久化缓存
                if self.use_persistent_cache:
                    nodes_to_update.append((entity_id, node, emb_array))
        
        # 3. 批量更新持久化缓存（异步，不阻塞）
        if nodes_to_update:
            asyncio.create_task(self._batch_update_persistent_cache(nodes_to_update))
        
        return embeddings
    
    async def _batch_update_persistent_cache(self, nodes_to_update: List[tuple]):
        """
        批量更新实体节点的持久化嵌入缓存
        
        Args:
            nodes_to_update: 列表，每个元素为 (entity_id, node_data, embedding)
        """
        try:
            for entity_id, node, embedding in nodes_to_update:
                # 将numpy数组转换为列表以便JSON序列化
                emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                
                # 更新节点数据
                node['embedding_cache'] = emb_list
                
                # 异步更新到图存储
                await self.graph.upsert_node(entity_id, node)
        except Exception as e:
            print(f"批量更新持久化缓存失败: {e}")
    
    def _get_entity_text(self, entity_node: dict) -> str:
        """
        从实体节点提取文本表示
        
        Args:
            entity_node: 实体节点数据
            
        Returns:
            实体文本
        """
        entity_name = entity_node.get('entity_name', '')
        description = entity_node.get('description', '')
        entity_type = entity_node.get('entity_type', '')
        
        # 组合实体信息
        if description:
            text = f"{entity_name}: {description}"
        else:
            text = entity_name
        
        if entity_type:
            text = f"[{entity_type}] {text}"
        
        return text
    
    def _compute_pairwise_similarities(self, embeddings: List[np.ndarray]) -> List[float]:
        """
        计算所有嵌入对之间的余弦相似度
        
        Args:
            embeddings: 嵌入向量列表
            
        Returns:
            相似度列表
        """
        similarities = []
        
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        return similarities
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            
        Returns:
            余弦相似度 (-1 到 1)
        """
        # 确保是numpy数组
        v1 = np.array(vec1) if not isinstance(vec1, np.ndarray) else vec1
        v2 = np.array(vec2) if not isinstance(vec2, np.ndarray) else vec2
        
        # 计算余弦相似度
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # 归一化到 [0, 1]
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    async def compute_coherence_with_details(self, hyperedge_id: str,
                                            variance_penalty: float = 0.5) -> Dict:
        """
        计算一致性并返回详细信息
        
        Args:
            hyperedge_id: 超边节点ID
            variance_penalty: 方差惩罚系数
            
        Returns:
            包含一致性分数和详细信息的字典
        """
        try:
            # 获取实体
            edges = await self.graph.get_node_edges(hyperedge_id)
            entity_ids = [dst for src, dst, _ in edges if src == hyperedge_id]
            
            if len(entity_ids) < 2:
                return {
                    'coherence': 1.0,
                    'num_entities': len(entity_ids),
                    'mean_similarity': 1.0,
                    'variance': 0.0,
                    'pairwise_similarities': []
                }
            
            # 获取嵌入
            embeddings = await self._get_entity_embeddings(entity_ids)
            
            # 计算相似度
            similarities = self._compute_pairwise_similarities(embeddings)
            
            if not similarities:
                return {
                    'coherence': 0.5,
                    'num_entities': len(entity_ids),
                    'mean_similarity': 0.5,
                    'variance': 0.0,
                    'pairwise_similarities': []
                }
            
            # 统计信息
            mean_sim = np.mean(similarities)
            var_sim = np.var(similarities)
            coherence = mean_sim - variance_penalty * var_sim
            coherence = max(0.0, min(1.0, coherence))
            
            return {
                'coherence': coherence,
                'num_entities': len(entity_ids),
                'mean_similarity': float(mean_sim),
                'variance': float(var_sim),
                'std_dev': float(np.std(similarities)),
                'min_similarity': float(np.min(similarities)),
                'max_similarity': float(np.max(similarities)),
                'pairwise_similarities': [float(s) for s in similarities]
            }
            
        except Exception as e:
            print(f"计算详细一致性失败 {hyperedge_id}: {e}")
            return {
                'coherence': 0.5,
                'error': str(e)
            }
    
    async def batch_compute_coherence(self, hyperedge_ids: List[str],
                                     variance_penalty: float = 0.5) -> Dict[str, float]:
        """
        批量计算多个超边的一致性
        
        Args:
            hyperedge_ids: 超边ID列表
            variance_penalty: 方差惩罚系数
            
        Returns:
            超边ID到一致性分数的映射
        """
        # 并行计算
        results = await asyncio.gather(*[
            self.compute_coherence(he_id, variance_penalty)
            for he_id in hyperedge_ids
        ], return_exceptions=True)
        
        # 构建结果字典
        coherence_scores = {}
        for he_id, result in zip(hyperedge_ids, results):
            if isinstance(result, Exception):
                coherence_scores[he_id] = 0.5  # 默认值
            else:
                coherence_scores[he_id] = result
        
        return coherence_scores
    
    def clear_cache(self):
        """清除内存缓存（不影响持久化缓存）"""
        self._embedding_cache.clear()
    
    def get_cache_size(self) -> int:
        """获取内存缓存大小"""
        return len(self._embedding_cache)
    
    async def get_cache_statistics(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计的字典
        """
        stats = {
            'memory_cache_size': len(self._embedding_cache),
            'use_persistent_cache': self.use_persistent_cache,
        }
        
        # 如果使用持久化缓存，统计有多少实体节点有缓存
        if self.use_persistent_cache:
            # 这个操作可能比较慢，仅用于调试
            try:
                # 获取所有实体节点（这里假设可以通过某种方式获取）
                # 实际实现可能需要根据具体的图存储实现调整
                stats['persistent_cache_note'] = "Persistent cache enabled in entity nodes"
            except Exception as e:
                stats['persistent_cache_error'] = str(e)
        
        return stats
    
    async def load_persistent_cache_to_memory(self, entity_ids: List[str]) -> int:
        """
        从持久化缓存批量加载嵌入到内存缓存
        
        用于系统启动时预热缓存，提升首次查询性能
        
        Args:
            entity_ids: 要加载的实体ID列表
            
        Returns:
            成功加载的嵌入数量
        """
        loaded_count = 0
        
        # 过滤已在内存中的
        to_load = [eid for eid in entity_ids if eid not in self._embedding_cache]
        
        if not to_load:
            return 0
        
        # 批量获取节点
        nodes = await asyncio.gather(*[
            self.graph.get_node(eid) for eid in to_load
        ])
        
        # 加载持久化缓存
        for entity_id, node in zip(to_load, nodes):
            if not node:
                continue
            
            if 'embedding_cache' in node:
                cached_emb = node['embedding_cache']
                if cached_emb is not None and len(cached_emb) > 0:
                    emb_array = np.array(cached_emb)
                    self._embedding_cache[entity_id] = emb_array
                    loaded_count += 1
        
        return loaded_count
    
    async def cache_entity_embeddings(self, entity_ids: List[str]):
        """
        预先缓存实体嵌入（优化性能）
        
        支持两级缓存：
        1. 从持久化缓存加载到内存
        2. 批量计算未缓存的嵌入并存储到两级缓存
        
        Args:
            entity_ids: 要缓存的实体ID列表
        """
        # 过滤已在内存缓存中的实体
        uncached_ids = [eid for eid in entity_ids if eid not in self._embedding_cache]
        
        if not uncached_ids:
            return
        
        # 批量获取实体节点
        nodes = await asyncio.gather(*[
            self.graph.get_node(eid) for eid in uncached_ids
        ])
        
        # 分类：有持久化缓存的 vs 需要计算的
        to_compute = []
        nodes_to_update = []
        
        for entity_id, node in zip(uncached_ids, nodes):
            if not node:
                continue
            
            # 检查持久化缓存
            if self.use_persistent_cache and 'embedding_cache' in node:
                cached_emb = node['embedding_cache']
                if cached_emb is not None and len(cached_emb) > 0:
                    # 加载到内存缓存
                    emb_array = np.array(cached_emb)
                    self._embedding_cache[entity_id] = emb_array
                    continue
            
            # 需要计算
            to_compute.append((entity_id, node))
        
        # 批量计算嵌入
        if to_compute:
            texts = [self._get_entity_text(node) for _, node in to_compute]
            embeddings = await self.embedding_func(texts)
            
            # 缓存到内存和持久化存储
            for (entity_id, node), emb in zip(to_compute, embeddings):
                emb_array = np.array(emb) if not isinstance(emb, np.ndarray) else emb
                
                # 内存缓存
                self._embedding_cache[entity_id] = emb_array
                
                # 准备持久化缓存更新
                if self.use_persistent_cache:
                    nodes_to_update.append((entity_id, node, emb_array))
            
            # 批量更新持久化缓存
            if nodes_to_update:
                await self._batch_update_persistent_cache(nodes_to_update)


# 辅助函数
def compute_coherence_statistics(coherence_scores: Dict[str, float]) -> Dict:
    """
    计算一致性分数的统计信息
    
    Args:
        coherence_scores: 超边ID到一致性分数的映射
        
    Returns:
        统计信息字典
    """
    scores = list(coherence_scores.values())
    
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
