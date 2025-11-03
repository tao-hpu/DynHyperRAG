"""
Approximate Nearest Neighbor (ANN) Search Module

This module provides ANN search capabilities for efficient hyperedge retrieval
in resource-constrained environments. It supports multiple ANN backends:
- FAISS: Facebook AI Similarity Search (CPU and GPU)
- HNSW: Hierarchical Navigable Small World graphs (via hnswlib)

ANN search trades a small amount of accuracy for significant speed improvements,
making it ideal for large-scale hypergraph retrieval.

Usage:
    from hypergraphrag.retrieval.ann_search import ANNSearchEngine
    
    # Create ANN engine
    engine = ANNSearchEngine(
        backend="hnsw",  # or "faiss"
        dimension=1536,
        config={"M": 16, "ef_construction": 200}
    )
    
    # Build index
    await engine.build_index(embeddings, ids)
    
    # Search
    results = await engine.search(query_embedding, top_k=10)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Literal
import numpy as np

logger = logging.getLogger(__name__)


class ANNSearchEngine:
    """
    Approximate Nearest Neighbor search engine with multiple backend support.
    
    This class provides a unified interface for ANN search using different
    backends (FAISS, HNSW). It handles index building, searching, and
    accuracy measurement.
    
    Attributes:
        backend: ANN backend to use ("faiss" or "hnsw")
        dimension: Embedding dimension
        config: Backend-specific configuration
        index: The underlying ANN index
        id_mapping: Mapping from index position to original IDs
    """
    
    def __init__(
        self,
        backend: Literal["faiss", "hnsw"] = "hnsw",
        dimension: int = 1536,
        config: Optional[Dict] = None
    ):
        """
        Initialize ANN search engine.
        
        Args:
            backend: ANN backend ("faiss" or "hnsw")
            dimension: Embedding vector dimension
            config: Backend-specific configuration:
                For HNSW:
                    - M: Number of connections per layer (default: 16)
                    - ef_construction: Size of dynamic candidate list (default: 200)
                    - ef_search: Size of search candidate list (default: 50)
                For FAISS:
                    - index_type: FAISS index type (default: "IVFFlat")
                    - nlist: Number of clusters for IVF (default: 100)
                    - nprobe: Number of clusters to search (default: 10)
                    - use_gpu: Whether to use GPU (default: False)
        """
        self.backend = backend.lower()
        self.dimension = dimension
        self.config = config or {}
        
        self.index = None
        self.id_mapping = []  # Maps index position to original ID
        self.is_built = False
        
        # Statistics
        self.stats = {
            "total_vectors": 0,
            "build_time": 0.0,
            "total_searches": 0,
            "total_search_time": 0.0
        }
        
        logger.info(
            f"ANNSearchEngine initialized with backend={backend}, "
            f"dimension={dimension}, config={config}"
        )
    
    async def build_index(
        self,
        embeddings: np.ndarray,
        ids: List[str]
    ):
        """
        Build ANN index from embeddings.
        
        Args:
            embeddings: Numpy array of shape (n, dimension)
            ids: List of IDs corresponding to embeddings
            
        Raises:
            ValueError: If embeddings shape doesn't match dimension
            ImportError: If required backend library is not installed
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings.shape[1]} doesn't match "
                f"expected dimension {self.dimension}"
            )
        
        if len(ids) != embeddings.shape[0]:
            raise ValueError(
                f"Number of IDs ({len(ids)}) doesn't match number of "
                f"embeddings ({embeddings.shape[0]})"
            )
        
        logger.info(f"Building {self.backend.upper()} index with {len(ids)} vectors...")
        start_time = time.time()
        
        # Build index based on backend
        if self.backend == "hnsw":
            await self._build_hnsw_index(embeddings, ids)
        elif self.backend == "faiss":
            await self._build_faiss_index(embeddings, ids)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
        
        # Update statistics
        self.stats["total_vectors"] = len(ids)
        self.stats["build_time"] = time.time() - start_time
        self.is_built = True
        
        logger.info(
            f"Index built successfully in {self.stats['build_time']:.2f}s. "
            f"Total vectors: {self.stats['total_vectors']}"
        )
    
    async def _build_hnsw_index(self, embeddings: np.ndarray, ids: List[str]):
        """Build HNSW index using hnswlib."""
        try:
            import hnswlib
        except ImportError:
            raise ImportError(
                "hnswlib is required for HNSW backend. "
                "Install it with: pip install hnswlib"
            )
        
        # Get configuration
        M = self.config.get("M", 16)
        ef_construction = self.config.get("ef_construction", 200)
        ef_search = self.config.get("ef_search", 50)
        
        # Create index
        self.index = hnswlib.Index(space='cosine', dim=self.dimension)
        self.index.init_index(
            max_elements=embeddings.shape[0],
            M=M,
            ef_construction=ef_construction
        )
        
        # Set search parameters
        self.index.set_ef(ef_search)
        
        # Add vectors
        self.index.add_items(embeddings, np.arange(len(ids)))
        
        # Store ID mapping
        self.id_mapping = ids
        
        logger.info(
            f"HNSW index built with M={M}, ef_construction={ef_construction}, "
            f"ef_search={ef_search}"
        )
    
    async def _build_faiss_index(self, embeddings: np.ndarray, ids: List[str]):
        """Build FAISS index."""
        try:
            import faiss
        except ImportError:
            raise ImportError(
                "faiss-cpu or faiss-gpu is required for FAISS backend. "
                "Install it with: pip install faiss-cpu"
            )
        
        # Get configuration
        index_type = self.config.get("index_type", "Flat")
        nlist = self.config.get("nlist", min(100, max(10, embeddings.shape[0] // 10)))
        nprobe = self.config.get("nprobe", min(10, nlist))
        use_gpu = self.config.get("use_gpu", False)
        
        # Ensure embeddings are contiguous and float32
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create index based on type
        if index_type == "Flat":
            # Exact search (baseline)
            self.index = faiss.IndexFlatIP(self.dimension)
        elif index_type == "IVFFlat":
            # Inverted file with flat quantizer
            # Ensure we have enough vectors for training
            if embeddings.shape[0] < nlist * 10:
                logger.warning(
                    f"Not enough vectors ({embeddings.shape[0]}) for IVFFlat with nlist={nlist}. "
                    f"Using Flat index instead."
                )
                self.index = faiss.IndexFlatIP(self.dimension)
            else:
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFFlat(
                    quantizer, self.dimension, nlist, faiss.METRIC_INNER_PRODUCT
                )
                # Train index
                self.index.train(embeddings)
                self.index.nprobe = nprobe
        elif index_type == "IVFPQ":
            # Inverted file with product quantization
            m = self.config.get("m", 8)  # Number of subquantizers
            
            # Ensure dimension is divisible by m
            if self.dimension % m != 0:
                logger.warning(
                    f"Dimension {self.dimension} not divisible by m={m}. "
                    f"Using Flat index instead."
                )
                self.index = faiss.IndexFlatIP(self.dimension)
            elif embeddings.shape[0] < nlist * 10:
                logger.warning(
                    f"Not enough vectors ({embeddings.shape[0]}) for IVFPQ. "
                    f"Using Flat index instead."
                )
                self.index = faiss.IndexFlatIP(self.dimension)
            else:
                quantizer = faiss.IndexFlatIP(self.dimension)
                self.index = faiss.IndexIVFPQ(
                    quantizer, self.dimension, nlist, m, 8
                )
                self.index.train(embeddings)
                self.index.nprobe = nprobe
        else:
            raise ValueError(f"Unknown FAISS index type: {index_type}")
        
        # Move to GPU if requested
        if use_gpu:
            try:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS index moved to GPU")
            except Exception as e:
                logger.warning(f"Failed to move FAISS to GPU: {e}. Using CPU.")
        
        # Add vectors
        self.index.add(embeddings)
        
        # Store ID mapping
        self.id_mapping = ids
        
        actual_index_type = "Flat" if isinstance(self.index, faiss.IndexFlatIP) else index_type
        logger.info(
            f"FAISS index built with type={actual_index_type}, "
            f"vectors={embeddings.shape[0]}, use_gpu={use_gpu}"
        )
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for nearest neighbors.
        
        Args:
            query_embedding: Query embedding vector of shape (dimension,) or (1, dimension)
            top_k: Number of nearest neighbors to return
            
        Returns:
            List of (id, distance) tuples sorted by distance (descending for similarity)
            
        Raises:
            RuntimeError: If index is not built
        """
        if not self.is_built:
            raise RuntimeError("Index must be built before searching")
        
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        start_time = time.time()
        
        # Search based on backend
        if self.backend == "hnsw":
            results = await self._search_hnsw(query_embedding, top_k)
        elif self.backend == "faiss":
            results = await self._search_faiss(query_embedding, top_k)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
        
        # Update statistics
        self.stats["total_searches"] += 1
        self.stats["total_search_time"] += time.time() - start_time
        
        return results
    
    async def _search_hnsw(
        self,
        query_embedding: np.ndarray,
        top_k: int
    ) -> List[Tuple[str, float]]:
        """Search using HNSW index."""
        # Query index
        labels, distances = self.index.knn_query(query_embedding, k=top_k)
        
        # Convert to results
        results = []
        for label, distance in zip(labels[0], distances[0]):
            if label < len(self.id_mapping):
                # HNSW returns cosine distance (0 = identical, 2 = opposite)
                # Convert to similarity (1 = identical, 0 = orthogonal, -1 = opposite)
                similarity = 1.0 - distance / 2.0
                results.append((self.id_mapping[label], similarity))
        
        return results
    
    async def _search_faiss(
        self,
        query_embedding: np.ndarray,
        top_k: int
    ) -> List[Tuple[str, float]]:
        """Search using FAISS index."""
        import faiss
        
        # Normalize query for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Query index
        distances, labels = self.index.search(query_embedding, top_k)
        
        # Convert to results
        results = []
        for label, distance in zip(labels[0], distances[0]):
            if label >= 0 and label < len(self.id_mapping):
                # FAISS returns inner product (already similarity for normalized vectors)
                results.append((self.id_mapping[label], float(distance)))
        
        return results
    
    async def batch_search(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[List[Tuple[str, float]]]:
        """
        Batch search for multiple queries.
        
        Args:
            query_embeddings: Numpy array of shape (n_queries, dimension)
            top_k: Number of nearest neighbors per query
            
        Returns:
            List of result lists, one per query
        """
        if not self.is_built:
            raise RuntimeError("Index must be built before searching")
        
        # Ensure 2D
        if query_embeddings.ndim == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        
        # Search each query
        results = []
        for query_emb in query_embeddings:
            result = await self.search(query_emb, top_k)
            results.append(result)
        
        return results
    
    def set_search_params(self, **kwargs):
        """
        Update search parameters.
        
        For HNSW:
            - ef_search: Size of search candidate list
        For FAISS:
            - nprobe: Number of clusters to search
        """
        if self.backend == "hnsw":
            if "ef_search" in kwargs:
                self.index.set_ef(kwargs["ef_search"])
                logger.info(f"HNSW ef_search updated to {kwargs['ef_search']}")
        
        elif self.backend == "faiss":
            if "nprobe" in kwargs:
                self.index.nprobe = kwargs["nprobe"]
                logger.info(f"FAISS nprobe updated to {kwargs['nprobe']}")
    
    def get_stats(self) -> Dict:
        """
        Get search statistics.
        
        Returns:
            Dict with statistics
        """
        stats = self.stats.copy()
        
        if stats["total_searches"] > 0:
            stats["avg_search_time"] = (
                stats["total_search_time"] / stats["total_searches"]
            )
        
        return stats
    
    def save_index(self, filepath: str):
        """
        Save index to disk.
        
        Args:
            filepath: Path to save index
        """
        if not self.is_built:
            raise RuntimeError("Index must be built before saving")
        
        if self.backend == "hnsw":
            self.index.save_index(filepath)
        elif self.backend == "faiss":
            import faiss
            faiss.write_index(self.index, filepath)
        
        # Save ID mapping separately
        import pickle
        with open(f"{filepath}.ids", "wb") as f:
            pickle.dump(self.id_mapping, f)
        
        logger.info(f"Index saved to {filepath}")
    
    def load_index(self, filepath: str):
        """
        Load index from disk.
        
        Args:
            filepath: Path to load index from
        """
        if self.backend == "hnsw":
            import hnswlib
            self.index = hnswlib.Index(space='cosine', dim=self.dimension)
            self.index.load_index(filepath)
            
            # Set search parameters
            ef_search = self.config.get("ef_search", 50)
            self.index.set_ef(ef_search)
        
        elif self.backend == "faiss":
            import faiss
            self.index = faiss.read_index(filepath)
        
        # Load ID mapping
        import pickle
        with open(f"{filepath}.ids", "rb") as f:
            self.id_mapping = pickle.load(f)
        
        self.is_built = True
        self.stats["total_vectors"] = len(self.id_mapping)
        
        logger.info(f"Index loaded from {filepath}")


async def measure_ann_accuracy(
    ann_engine: ANNSearchEngine,
    exact_results: List[List[Tuple[str, float]]],
    ann_results: List[List[Tuple[str, float]]],
    k_values: List[int] = [1, 5, 10]
) -> Dict:
    """
    Measure ANN search accuracy compared to exact search.
    
    This function computes recall@k metrics to quantify the accuracy
    loss from using approximate search.
    
    Args:
        ann_engine: ANN search engine
        exact_results: Exact search results (ground truth)
        ann_results: ANN search results
        k_values: List of k values for recall@k
        
    Returns:
        Dict with accuracy metrics:
            - recall@k for each k
            - average_recall
            - speedup (if timing info available)
    """
    if len(exact_results) != len(ann_results):
        raise ValueError("Number of exact and ANN results must match")
    
    metrics = {}
    
    # Compute recall@k for each k
    for k in k_values:
        recalls = []
        
        for exact, ann in zip(exact_results, ann_results):
            # Get top-k IDs
            exact_ids = set([id for id, _ in exact[:k]])
            ann_ids = set([id for id, _ in ann[:k]])
            
            # Compute recall
            if len(exact_ids) > 0:
                recall = len(exact_ids & ann_ids) / len(exact_ids)
                recalls.append(recall)
        
        metrics[f"recall@{k}"] = np.mean(recalls) if recalls else 0.0
    
    # Average recall
    metrics["average_recall"] = np.mean([
        metrics[f"recall@{k}"] for k in k_values
    ])
    
    logger.info(
        f"ANN Accuracy: " +
        ", ".join([f"recall@{k}={metrics[f'recall@{k}']:.3f}" for k in k_values])
    )
    
    return metrics
