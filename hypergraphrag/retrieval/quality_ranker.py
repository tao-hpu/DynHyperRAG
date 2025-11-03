"""
Quality-Aware Ranker for Efficient Retrieval

This module implements quality-aware ranking that combines semantic similarity,
quality scores, and dynamic weights to prioritize high-quality hyperedges
during retrieval.

Key Features:
- Composite scoring function: α × similarity + β × quality + γ × dynamic_weight
- Configurable weight parameters (α, β, γ)
- Re-ranking after initial vector retrieval
- Ranking explanation for interpretability

Usage:
    from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker
    
    ranker = QualityAwareRanker(config)
    ranked_results = await ranker.rank_hyperedges(query, hyperedges)
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class QualityAwareRanker:
    """
    Quality-aware ranker for hyperedge retrieval.
    
    This class implements a composite ranking function that combines:
    1. Semantic similarity (from vector retrieval)
    2. Quality score (from quality assessment)
    3. Dynamic weight (from feedback-based updates)
    
    The final score is computed as:
        score = α × similarity + β × quality + γ × dynamic_weight
    
    Attributes:
        alpha: Weight for semantic similarity (default: 0.5)
        beta: Weight for quality score (default: 0.3)
        gamma: Weight for dynamic weight (default: 0.2)
        normalize_scores: Whether to normalize scores to [0, 1]
        provide_explanation: Whether to include ranking explanations
    """
    
    def __init__(self, config: dict):
        """
        Initialize QualityAwareRanker.
        
        Args:
            config: Configuration dict with keys:
                - similarity_weight (α): Weight for semantic similarity (default: 0.5)
                - quality_weight (β): Weight for quality score (default: 0.3)
                - dynamic_weight (γ): Weight for dynamic weight (default: 0.2)
                - normalize_scores: Whether to normalize scores (default: True)
                - provide_explanation: Whether to include explanations (default: False)
        """
        self.alpha = config.get("similarity_weight", 0.5)
        self.beta = config.get("quality_weight", 0.3)
        self.gamma = config.get("dynamic_weight", 0.2)
        self.normalize_scores = config.get("normalize_scores", True)
        self.provide_explanation = config.get("provide_explanation", False)
        
        # Validate weights sum to 1.0 (or close to it)
        total_weight = self.alpha + self.beta + self.gamma
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Ranking weights sum to {total_weight:.3f}, not 1.0. "
                f"Consider normalizing: α={self.alpha}, β={self.beta}, γ={self.gamma}"
            )
        
        logger.info(
            f"QualityAwareRanker initialized with weights: "
            f"α={self.alpha} (similarity), β={self.beta} (quality), "
            f"γ={self.gamma} (dynamic)"
        )
    
    async def rank_hyperedges(
        self,
        query: str,
        hyperedges: List[Dict],
        graph: Optional[object] = None
    ) -> List[Dict]:
        """
        Rank hyperedges using quality-aware scoring.
        
        This method re-ranks hyperedges retrieved from vector search by
        incorporating quality scores and dynamic weights. The input hyperedges
        should already have similarity scores from vector retrieval.
        
        Args:
            query: Query string (for logging/explanation purposes)
            hyperedges: List of hyperedge dicts from vector retrieval, each containing:
                - hyperedge_name or id: Hyperedge identifier
                - distance: Semantic similarity score (0-1, higher is better)
                - Other fields from graph node (quality_score, dynamic_weight, etc.)
            graph: Optional BaseGraphStorage instance to fetch missing data
            
        Returns:
            List of hyperedge dicts sorted by final_score (descending), with added fields:
                - final_score: Composite ranking score
                - ranking_components: Dict with individual score components (if explain=True)
                
        Example:
            >>> ranker = QualityAwareRanker({"similarity_weight": 0.5, "quality_weight": 0.3})
            >>> results = await vdb.query(query, top_k=20)
            >>> ranked = await ranker.rank_hyperedges(query, results)
            >>> print(f"Top result score: {ranked[0]['final_score']:.3f}")
        """
        if not hyperedges:
            logger.warning("No hyperedges to rank")
            return []
        
        logger.info(f"Ranking {len(hyperedges)} hyperedges for query: {query[:50]}...")
        
        scored_hyperedges = []
        
        for he in hyperedges:
            try:
                # Extract components
                similarity = self._extract_similarity(he)
                quality = self._extract_quality(he)
                dynamic_weight = self._extract_dynamic_weight(he)
                
                # Compute final score
                final_score = (
                    self.alpha * similarity +
                    self.beta * quality +
                    self.gamma * dynamic_weight
                )
                
                # Normalize if requested
                if self.normalize_scores:
                    final_score = max(0.0, min(1.0, final_score))
                
                # Add score to hyperedge dict
                he_scored = he.copy()
                he_scored["final_score"] = final_score
                
                # Add explanation if requested
                if self.provide_explanation:
                    he_scored["ranking_components"] = {
                        "similarity": similarity,
                        "quality": quality,
                        "dynamic_weight": dynamic_weight,
                        "weights": {
                            "alpha": self.alpha,
                            "beta": self.beta,
                            "gamma": self.gamma
                        },
                        "computation": (
                            f"{self.alpha}×{similarity:.3f} + "
                            f"{self.beta}×{quality:.3f} + "
                            f"{self.gamma}×{dynamic_weight:.3f} = {final_score:.3f}"
                        )
                    }
                
                scored_hyperedges.append(he_scored)
                
            except Exception as e:
                logger.warning(
                    f"Error scoring hyperedge {he.get('hyperedge_name', 'unknown')}: {e}"
                )
                # Include with default score to avoid losing data
                he_scored = he.copy()
                he_scored["final_score"] = 0.5
                scored_hyperedges.append(he_scored)
        
        # Sort by final score (descending - higher is better)
        scored_hyperedges.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Log ranking statistics
        if scored_hyperedges:
            scores = [h["final_score"] for h in scored_hyperedges]
            logger.info(
                f"Ranking complete. Score range: [{min(scores):.3f}, {max(scores):.3f}], "
                f"mean: {sum(scores)/len(scores):.3f}"
            )
        
        return scored_hyperedges
    
    def _extract_similarity(self, hyperedge: Dict) -> float:
        """
        Extract semantic similarity score from hyperedge dict.
        
        Args:
            hyperedge: Hyperedge dict from vector retrieval
            
        Returns:
            Similarity score (0-1, higher is better)
        """
        # Vector retrieval typically returns 'distance' field
        # Distance can be cosine distance (0=identical, 2=opposite)
        # or similarity score (1=identical, 0=unrelated)
        
        if "distance" in hyperedge:
            distance = hyperedge["distance"]
            # Assume distance is already a similarity score (0-1)
            # If it's cosine distance, convert: similarity = 1 - distance/2
            # For now, assume it's already similarity
            return max(0.0, min(1.0, distance))
        
        if "similarity" in hyperedge:
            return max(0.0, min(1.0, hyperedge["similarity"]))
        
        # Default: medium similarity
        logger.debug(
            f"No similarity score found for {hyperedge.get('hyperedge_name', 'unknown')}, "
            "using default 0.5"
        )
        return 0.5
    
    def _extract_quality(self, hyperedge: Dict) -> float:
        """
        Extract quality score from hyperedge dict.
        
        Args:
            hyperedge: Hyperedge dict
            
        Returns:
            Quality score (0-1)
        """
        if "quality_score" in hyperedge:
            return max(0.0, min(1.0, hyperedge["quality_score"]))
        
        # Default: medium quality
        logger.debug(
            f"No quality_score found for {hyperedge.get('hyperedge_name', 'unknown')}, "
            "using default 0.5"
        )
        return 0.5
    
    def _extract_dynamic_weight(self, hyperedge: Dict) -> float:
        """
        Extract dynamic weight from hyperedge dict.
        
        Args:
            hyperedge: Hyperedge dict
            
        Returns:
            Dynamic weight (0-1)
        """
        if "dynamic_weight" in hyperedge:
            return max(0.0, min(1.0, hyperedge["dynamic_weight"]))
        
        # Fallback to quality score if available
        if "quality_score" in hyperedge:
            return max(0.0, min(1.0, hyperedge["quality_score"]))
        
        # Fallback to original weight if available
        if "weight" in hyperedge:
            # Original weight is typically 0-100, normalize to 0-1
            return max(0.0, min(1.0, hyperedge["weight"] / 100.0))
        
        # Default: medium weight
        logger.debug(
            f"No dynamic_weight found for {hyperedge.get('hyperedge_name', 'unknown')}, "
            "using default 0.5"
        )
        return 0.5
    
    def set_weights(self, alpha: float, beta: float, gamma: float):
        """
        Update ranking weights.
        
        Args:
            alpha: New weight for semantic similarity
            beta: New weight for quality score
            gamma: New weight for dynamic weight
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        total = alpha + beta + gamma
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"New weights sum to {total:.3f}, not 1.0. "
                f"α={alpha}, β={beta}, γ={gamma}"
            )
        
        logger.info(f"Ranking weights updated: α={alpha}, β={beta}, γ={gamma}")
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get current ranking weights.
        
        Returns:
            Dict with keys: alpha, beta, gamma
        """
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma
        }
    
    def explain_ranking(self, hyperedge: Dict) -> str:
        """
        Generate human-readable explanation of ranking score.
        
        Args:
            hyperedge: Hyperedge dict with ranking_components
            
        Returns:
            Explanation string
        """
        if "ranking_components" not in hyperedge:
            return "No ranking explanation available"
        
        components = hyperedge["ranking_components"]
        explanation = (
            f"Final Score: {hyperedge['final_score']:.3f}\n"
            f"  - Similarity: {components['similarity']:.3f} (weight: {self.alpha})\n"
            f"  - Quality: {components['quality']:.3f} (weight: {self.beta})\n"
            f"  - Dynamic Weight: {components['dynamic_weight']:.3f} (weight: {self.gamma})\n"
            f"Computation: {components['computation']}"
        )
        return explanation


# Convenience function for quick ranking
async def rank_by_quality(
    hyperedges: List[Dict],
    query: str = "",
    similarity_weight: float = 0.5,
    quality_weight: float = 0.3,
    dynamic_weight: float = 0.2
) -> List[Dict]:
    """
    Convenience function for quality-aware ranking.
    
    Args:
        hyperedges: List of hyperedge dicts from vector retrieval
        query: Query string (optional, for logging)
        similarity_weight: Weight for similarity (α)
        quality_weight: Weight for quality (β)
        dynamic_weight: Weight for dynamic weight (γ)
        
    Returns:
        Ranked list of hyperedges
        
    Example:
        >>> results = await vdb.query(query, top_k=20)
        >>> ranked = await rank_by_quality(results, query)
    """
    config = {
        "similarity_weight": similarity_weight,
        "quality_weight": quality_weight,
        "dynamic_weight": dynamic_weight
    }
    ranker = QualityAwareRanker(config)
    return await ranker.rank_hyperedges(query, hyperedges)
