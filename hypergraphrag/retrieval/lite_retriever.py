"""
Lightweight Retriever for Resource-Constrained Environments

This module implements a lightweight variant of DynHyperRAG retrieval that
reduces computational overhead while maintaining acceptable accuracy. It uses
simplified quality features and caching strategies for efficient retrieval.

Key Features:
- Simplified quality scoring (degree + coherence only)
- Simple dictionary-based caching
- Batch processing for efficiency
- Suitable for production deployment

Usage:
    from hypergraphrag.retrieval.lite_retriever import LiteRetriever
    
    retriever = LiteRetriever(graph, vdb, config)
    results = await retriever.retrieve(query, top_k=10)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable
from collections import OrderedDict
import numpy as np

from hypergraphrag.base import BaseGraphStorage, BaseVectorStorage
from hypergraphrag.retrieval.ann_search import ANNSearchEngine

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
    
    This cache automatically evicts the least recently used items when
    the cache size limit is reached.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, key: str, value: any):
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item and move to end
            self.cache.move_to_end(key)
        else:
            # Add new item
            if len(self.cache) >= self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class LiteRetriever:
    """
    Lightweight retriever for efficient hyperedge retrieval.
    
    This class implements a resource-efficient variant of DynHyperRAG retrieval
    that uses simplified quality features and caching to reduce computational
    overhead while maintaining acceptable accuracy.
    
    Optimizations:
    - Simplified quality features (degree + coherence only)
    - LRU caching for query results and quality scores
    - Batch processing for efficiency
    - Configurable cache size and scoring weights
    
    Attributes:
        graph: BaseGraphStorage instance for graph operations
        vdb: BaseVectorStorage instance for vector retrieval
        cache: LRU cache for query results
        quality_cache: LRU cache for quality scores
        degree_weight: Weight for degree centrality (default: 0.5)
        coherence_weight: Weight for coherence (default: 0.5)
        similarity_weight: Weight for similarity in final ranking (default: 0.7)
        quality_weight: Weight for quality in final ranking (default: 0.3)
    """
    
    def __init__(
        self,
        graph: BaseGraphStorage,
        vdb: BaseVectorStorage,
        config: Optional[Dict] = None
    ):
        """
        Initialize LiteRetriever.
        
        Args:
            graph: BaseGraphStorage instance
            vdb: BaseVectorStorage instance
            config: Configuration dict with keys:
                - cache_size: Max number of queries to cache (default: 1000)
                - quality_cache_size: Max quality scores to cache (default: 5000)
                - degree_weight: Weight for degree in quality (default: 0.5)
                - coherence_weight: Weight for coherence in quality (default: 0.5)
                - similarity_weight: Weight for similarity in ranking (default: 0.7)
                - quality_weight: Weight for quality in ranking (default: 0.3)
                - enable_caching: Whether to enable caching (default: True)
                - embedding_func: Optional embedding function for coherence
                - use_ann: Whether to use ANN search (default: False)
                - ann_backend: ANN backend ("faiss" or "hnsw", default: "hnsw")
                - ann_config: ANN-specific configuration dict
        """
        self.graph = graph
        self.vdb = vdb
        self.config = config or {}
        
        # Cache configuration
        cache_size = self.config.get("cache_size", 1000)
        quality_cache_size = self.config.get("quality_cache_size", 5000)
        self.enable_caching = self.config.get("enable_caching", True)
        
        # Initialize caches
        self.cache = LRUCache(max_size=cache_size) if self.enable_caching else None
        self.quality_cache = LRUCache(max_size=quality_cache_size) if self.enable_caching else None
        
        # Quality scoring weights (for simplified quality)
        self.degree_weight = self.config.get("degree_weight", 0.5)
        self.coherence_weight = self.config.get("coherence_weight", 0.5)
        
        # Ranking weights
        self.similarity_weight = self.config.get("similarity_weight", 0.7)
        self.quality_weight = self.config.get("quality_weight", 0.3)
        
        # Optional embedding function for coherence computation
        self.embedding_func = self.config.get("embedding_func", None)
        
        # ANN search configuration
        self.use_ann = self.config.get("use_ann", False)
        self.ann_engine = None
        
        if self.use_ann:
            ann_backend = self.config.get("ann_backend", "hnsw")
            ann_config = self.config.get("ann_config", {})
            embedding_dim = self.config.get("embedding_dim", 1536)
            
            self.ann_engine = ANNSearchEngine(
                backend=ann_backend,
                dimension=embedding_dim,
                config=ann_config
            )
            logger.info(f"ANN search enabled with backend={ann_backend}")
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "total_retrieval_time": 0.0,
            "total_quality_computations": 0,
            "ann_searches": 0,
            "exact_searches": 0
        }
        
        logger.info(
            f"LiteRetriever initialized with cache_size={cache_size}, "
            f"quality_cache_size={quality_cache_size}, "
            f"weights: degree={self.degree_weight}, coherence={self.coherence_weight}, "
            f"similarity={self.similarity_weight}, quality={self.quality_weight}, "
            f"use_ann={self.use_ann}"
        )
    
    async def build_ann_index(self):
        """
        Build ANN index from vector database.
        
        This method extracts all embeddings from the vector database and
        builds an ANN index for fast approximate search. Should be called
        once after initial graph construction or when the graph is updated.
        
        Raises:
            RuntimeError: If ANN is not enabled
        """
        if not self.use_ann:
            raise RuntimeError("ANN search is not enabled")
        
        logger.info("Building ANN index from vector database...")
        
        # This is a placeholder - actual implementation depends on VDB interface
        # In practice, you would need to:
        # 1. Extract all embeddings and IDs from VDB
        # 2. Call ann_engine.build_index(embeddings, ids)
        
        logger.warning(
            "build_ann_index() requires VDB-specific implementation. "
            "Please implement extraction of embeddings from your VDB."
        )
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        use_cache: bool = True,
        force_exact: bool = False
    ) -> List[Dict]:
        """
        Retrieve and rank hyperedges for a query.
        
        This method performs lightweight retrieval by:
        1. Checking cache for previous results
        2. Performing vector retrieval (ANN or exact) with expanded top_k
        3. Computing simplified quality scores
        4. Ranking by combined similarity + quality
        5. Caching results for future queries
        
        Args:
            query: Query string
            top_k: Number of results to return
            use_cache: Whether to use cache (default: True)
            force_exact: Force exact search even if ANN is enabled (default: False)
            
        Returns:
            List of ranked hyperedge dicts with fields:
                - hyperedge_name or id: Hyperedge identifier
                - distance: Semantic similarity score
                - simple_quality: Simplified quality score
                - final_score: Combined ranking score
                - Other fields from graph node
                
        Example:
            >>> retriever = LiteRetriever(graph, vdb, config)
            >>> results = await retriever.retrieve("What is the penalty for theft?", top_k=10)
            >>> print(f"Top result: {results[0]['hyperedge_name']}")
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        # 1. Check cache
        if use_cache and self.enable_caching:
            cache_key = f"{query}:{top_k}:{force_exact}"
            cached_results = self.cache.get(cache_key)
            
            if cached_results is not None:
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_results
        
        logger.info(f"Retrieving for query: {query[:50]}... (top_k={top_k})")
        
        # 2. Vector retrieval (retrieve more than needed for better ranking)
        retrieval_k = min(top_k * 2, 100)  # Retrieve 2x for re-ranking
        
        # Decide whether to use ANN or exact search
        use_ann_search = self.use_ann and self.ann_engine and self.ann_engine.is_built and not force_exact
        
        try:
            if use_ann_search:
                vector_results = await self._ann_retrieve(query, retrieval_k)
                self.stats["ann_searches"] += 1
            else:
                vector_results = await self.vdb.query(query, top_k=retrieval_k)
                self.stats["exact_searches"] += 1
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return []
        
        if not vector_results:
            logger.warning("No results from vector retrieval")
            return []
        
        logger.debug(
            f"Retrieved {len(vector_results)} candidates from "
            f"{'ANN' if use_ann_search else 'exact'} search"
        )
        
        # 3. Compute simplified quality scores
        scored_results = await self._compute_quality_scores(vector_results)
        
        # 4. Rank by combined score
        ranked_results = self._rank_results(scored_results)
        
        # 5. Take top_k
        final_results = ranked_results[:top_k]
        
        # 6. Cache results
        if use_cache and self.enable_caching:
            cache_key = f"{query}:{top_k}:{force_exact}"
            self.cache.put(cache_key, final_results)
        
        # Update statistics
        elapsed_time = time.time() - start_time
        self.stats["total_retrieval_time"] += elapsed_time
        
        logger.info(
            f"Retrieved {len(final_results)} results in {elapsed_time:.3f}s "
            f"({'ANN' if use_ann_search else 'exact'}). "
            f"Score range: [{final_results[-1]['final_score']:.3f}, "
            f"{final_results[0]['final_score']:.3f}]"
        )
        
        return final_results
    
    async def _ann_retrieve(self, query: str, top_k: int) -> List[Dict]:
        """
        Retrieve using ANN search.
        
        Args:
            query: Query string
            top_k: Number of results
            
        Returns:
            List of hyperedge dicts with distance scores
        """
        # Get query embedding
        query_embedding = await self.embedding_func([query])
        query_embedding = np.array(query_embedding[0])
        
        # Search ANN index
        ann_results = await self.ann_engine.search(query_embedding, top_k)
        
        # Convert to VDB-like format
        results = []
        for hyperedge_id, similarity in ann_results:
            # Get node data from graph
            try:
                node = await self.graph.get_node(hyperedge_id)
                if node:
                    result = node.copy()
                    result["hyperedge_name"] = hyperedge_id
                    result["id"] = hyperedge_id
                    result["distance"] = similarity
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to get node {hyperedge_id}: {e}")
        
        return results
    
    async def _compute_quality_scores(self, hyperedges: List[Dict]) -> List[Dict]:
        """
        Compute simplified quality scores for hyperedges.
        
        Uses only degree centrality and coherence (if embedding_func available)
        for efficient quality assessment.
        
        Args:
            hyperedges: List of hyperedge dicts from vector retrieval
            
        Returns:
            List of hyperedge dicts with added 'simple_quality' field
        """
        scored_hyperedges = []
        
        # Process in batches for efficiency
        batch_size = 50
        for i in range(0, len(hyperedges), batch_size):
            batch = hyperedges[i:i + batch_size]
            batch_results = await self._score_batch(batch)
            scored_hyperedges.extend(batch_results)
        
        return scored_hyperedges
    
    async def _score_batch(self, batch: List[Dict]) -> List[Dict]:
        """
        Score a batch of hyperedges.
        
        Args:
            batch: Batch of hyperedge dicts
            
        Returns:
            Batch with quality scores added
        """
        scored_batch = []
        
        for he in batch:
            try:
                he_id = he.get("hyperedge_name") or he.get("id")
                
                if not he_id:
                    logger.warning("Hyperedge missing ID, skipping")
                    continue
                
                # Check quality cache
                if self.enable_caching:
                    cached_quality = self.quality_cache.get(he_id)
                    if cached_quality is not None:
                        he_scored = he.copy()
                        he_scored["simple_quality"] = cached_quality
                        scored_batch.append(he_scored)
                        continue
                
                # Compute simplified quality
                quality = await self._compute_simple_quality(he_id)
                
                # Cache quality score
                if self.enable_caching:
                    self.quality_cache.put(he_id, quality)
                
                # Add to result
                he_scored = he.copy()
                he_scored["simple_quality"] = quality
                scored_batch.append(he_scored)
                
                self.stats["total_quality_computations"] += 1
                
            except Exception as e:
                logger.warning(f"Error scoring hyperedge {he.get('hyperedge_name', 'unknown')}: {e}")
                # Use default quality on error
                he_scored = he.copy()
                he_scored["simple_quality"] = 0.5
                scored_batch.append(he_scored)
        
        return scored_batch
    
    async def _compute_simple_quality(self, hyperedge_id: str) -> float:
        """
        Compute simplified quality score using only degree and coherence.
        
        Quality = degree_weight × normalized_degree + coherence_weight × coherence
        
        Args:
            hyperedge_id: Hyperedge node ID
            
        Returns:
            Simplified quality score (0-1)
        """
        try:
            # 1. Compute degree centrality (fast)
            degree = await self.graph.node_degree(hyperedge_id)
            # Normalize degree (assume max degree ~10 for typical hypergraphs)
            normalized_degree = min(1.0, degree / 10.0)
            
            # 2. Compute coherence (optional, slower)
            coherence = 0.5  # Default if no embedding function
            
            if self.embedding_func is not None:
                try:
                    coherence = await self._compute_coherence(hyperedge_id)
                except Exception as e:
                    logger.debug(f"Coherence computation failed for {hyperedge_id}: {e}")
            
            # 3. Combine features
            quality = (
                self.degree_weight * normalized_degree +
                self.coherence_weight * coherence
            )
            
            return max(0.0, min(1.0, quality))
            
        except Exception as e:
            logger.warning(f"Error computing quality for {hyperedge_id}: {e}")
            return 0.5
    
    async def _compute_coherence(self, hyperedge_id: str) -> float:
        """
        Compute simplified coherence score.
        
        This is a lightweight version that computes average pairwise
        similarity of entity embeddings without variance penalty.
        
        Args:
            hyperedge_id: Hyperedge node ID
            
        Returns:
            Coherence score (0-1)
        """
        try:
            # Get entities connected to hyperedge
            edges = await self.graph.get_node_edges(hyperedge_id)
            
            if not edges:
                return 0.5
            
            # Extract entity IDs
            entity_ids = [e[1] for e in edges]
            
            if len(entity_ids) < 2:
                return 1.0  # Single entity is perfectly coherent
            
            # Get entity texts
            entity_nodes = await asyncio.gather(
                *[self.graph.get_node(eid) for eid in entity_ids],
                return_exceptions=True
            )
            
            entity_texts = []
            for node in entity_nodes:
                if isinstance(node, Exception) or node is None:
                    continue
                
                # Construct entity text
                entity_name = node.get("entity_name", "")
                description = node.get("description", "")
                text = f"{entity_name} {description}".strip()
                
                if text:
                    entity_texts.append(text)
            
            if len(entity_texts) < 2:
                return 0.5
            
            # Compute embeddings
            embeddings = await self.embedding_func(entity_texts)
            
            # Compute pairwise similarities
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            if not similarities:
                return 0.5
            
            # Return average similarity (no variance penalty for speed)
            coherence = np.mean(similarities)
            return max(0.0, min(1.0, coherence))
            
        except Exception as e:
            logger.debug(f"Coherence computation error: {e}")
            return 0.5
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Normalize to [0, 1]
        return (similarity + 1.0) / 2.0
    
    def _rank_results(self, hyperedges: List[Dict]) -> List[Dict]:
        """
        Rank hyperedges by combined similarity and quality.
        
        Final score = similarity_weight × similarity + quality_weight × quality
        
        Args:
            hyperedges: List of hyperedge dicts with similarity and quality
            
        Returns:
            Sorted list of hyperedges (descending by final_score)
        """
        for he in hyperedges:
            # Extract similarity
            similarity = he.get("distance", 0.5)
            
            # Extract quality
            quality = he.get("simple_quality", 0.5)
            
            # Compute final score
            final_score = (
                self.similarity_weight * similarity +
                self.quality_weight * quality
            )
            
            he["final_score"] = final_score
        
        # Sort by final score (descending)
        hyperedges.sort(key=lambda x: x["final_score"], reverse=True)
        
        return hyperedges
    
    def clear_cache(self):
        """Clear all caches."""
        if self.cache:
            self.cache.clear()
        if self.quality_cache:
            self.quality_cache.clear()
        logger.info("All caches cleared")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache statistics
        """
        stats = {
            "query_cache": self.cache.get_stats() if self.cache else None,
            "quality_cache": self.quality_cache.get_stats() if self.quality_cache else None,
            "retrieval_stats": self.stats.copy()
        }
        
        # Add average retrieval time
        if self.stats["total_queries"] > 0:
            stats["retrieval_stats"]["avg_retrieval_time"] = (
                self.stats["total_retrieval_time"] / self.stats["total_queries"]
            )
        
        return stats
    
    def set_weights(
        self,
        similarity_weight: Optional[float] = None,
        quality_weight: Optional[float] = None,
        degree_weight: Optional[float] = None,
        coherence_weight: Optional[float] = None
    ):
        """
        Update retrieval and quality weights.
        
        Args:
            similarity_weight: New weight for similarity in ranking
            quality_weight: New weight for quality in ranking
            degree_weight: New weight for degree in quality
            coherence_weight: New weight for coherence in quality
        """
        if similarity_weight is not None:
            self.similarity_weight = similarity_weight
        
        if quality_weight is not None:
            self.quality_weight = quality_weight
        
        if degree_weight is not None:
            self.degree_weight = degree_weight
        
        if coherence_weight is not None:
            self.coherence_weight = coherence_weight
        
        logger.info(
            f"Weights updated: similarity={self.similarity_weight}, "
            f"quality={self.quality_weight}, degree={self.degree_weight}, "
            f"coherence={self.coherence_weight}"
        )
    
    async def measure_ann_accuracy(
        self,
        test_queries: List[str],
        top_k: int = 10
    ) -> Dict:
        """
        Measure ANN search accuracy compared to exact search.
        
        This method runs both ANN and exact search on test queries and
        computes recall@k metrics to quantify accuracy loss.
        
        Args:
            test_queries: List of test query strings
            top_k: Number of results to compare
            
        Returns:
            Dict with accuracy metrics:
                - recall@1, recall@5, recall@10
                - average_recall
                - speedup (ANN time / exact time)
                
        Raises:
            RuntimeError: If ANN is not enabled or index not built
        """
        if not self.use_ann or not self.ann_engine or not self.ann_engine.is_built:
            raise RuntimeError("ANN search must be enabled and index built")
        
        logger.info(f"Measuring ANN accuracy on {len(test_queries)} queries...")
        
        exact_results = []
        ann_results = []
        exact_time = 0.0
        ann_time = 0.0
        
        for query in test_queries:
            # Exact search
            start = time.time()
            exact = await self.retrieve(query, top_k=top_k, use_cache=False, force_exact=True)
            exact_time += time.time() - start
            exact_results.append([(r.get("hyperedge_name") or r.get("id"), r["distance"]) for r in exact])
            
            # ANN search
            start = time.time()
            ann = await self.retrieve(query, top_k=top_k, use_cache=False, force_exact=False)
            ann_time += time.time() - start
            ann_results.append([(r.get("hyperedge_name") or r.get("id"), r["distance"]) for r in ann])
        
        # Compute recall@k
        k_values = [1, 5, 10]
        metrics = {}
        
        for k in k_values:
            if k > top_k:
                continue
            
            recalls = []
            for exact, ann in zip(exact_results, ann_results):
                exact_ids = set([id for id, _ in exact[:k]])
                ann_ids = set([id for id, _ in ann[:k]])
                
                if len(exact_ids) > 0:
                    recall = len(exact_ids & ann_ids) / len(exact_ids)
                    recalls.append(recall)
            
            metrics[f"recall@{k}"] = np.mean(recalls) if recalls else 0.0
        
        # Average recall
        metrics["average_recall"] = np.mean([
            metrics[f"recall@{k}"] for k in k_values if f"recall@{k}" in metrics
        ])
        
        # Speedup
        metrics["exact_time"] = exact_time
        metrics["ann_time"] = ann_time
        metrics["speedup"] = exact_time / ann_time if ann_time > 0 else 0.0
        
        logger.info(
            f"ANN Accuracy: " +
            ", ".join([f"recall@{k}={metrics.get(f'recall@{k}', 0):.3f}" for k in k_values if f"recall@{k}" in metrics]) +
            f", speedup={metrics['speedup']:.2f}x"
        )
        
        return metrics
