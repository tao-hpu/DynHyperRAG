"""
Hyperedge Refiner for DynHyperRAG

This module implements hyperedge refinement functionality to filter and improve
the quality of the knowledge graph. It supports both hard filtering (deletion)
and soft filtering (weight reduction) strategies, along with multiple threshold
selection methods.

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Literal
from datetime import datetime

from ..base import BaseGraphStorage
from ..utils import logger


class HyperedgeRefiner:
    """
    Hyperedge refiner for filtering low-quality hyperedges.
    
    This class implements filtering strategies to maintain knowledge graph quality
    by removing or downweighting low-quality hyperedges. It supports:
    
    - Hard filtering: Permanently delete low-quality hyperedges
    - Soft filtering: Reduce dynamic weight but keep hyperedges
    - Multiple threshold selection strategies
    
    Args:
        graph: BaseGraphStorage instance for accessing and modifying nodes
        config: Configuration dictionary with the following keys:
            - quality_threshold: Quality score threshold for filtering (default: 0.5)
            - filter_mode: 'hard' or 'soft' filtering (default: 'soft')
            - threshold_strategy: Strategy for threshold selection (default: 'fixed')
                - 'fixed': Use fixed quality_threshold
                - 'percentile': Use percentile-based threshold
                - 'f1_optimal': Find F1-optimal threshold (requires ground truth)
            - percentile: Percentile for threshold (default: 25, i.e., bottom 25%)
            - soft_filter_weight_multiplier: Weight multiplier for soft filtering (default: 0.1)
            - track_decisions: Whether to track filtering decisions (default: True)
    
    Example:
        >>> config = {
        ...     'quality_threshold': 0.5,
        ...     'filter_mode': 'soft',
        ...     'threshold_strategy': 'fixed'
        ... }
        >>> refiner = HyperedgeRefiner(graph, config)
        >>> result = await refiner.filter_low_quality(hyperedge_ids)
    """
    
    def __init__(self, graph: BaseGraphStorage, config: dict):
        """Initialize the hyperedge refiner."""
        self.graph = graph
        
        # Filtering configuration
        self.quality_threshold = config.get('quality_threshold', 0.5)
        if not (0.0 <= self.quality_threshold <= 1.0):
            raise ValueError(
                f"quality_threshold must be in [0, 1], got {self.quality_threshold}"
            )
        
        # Filter mode
        self.filter_mode = config.get('filter_mode', 'soft')
        if self.filter_mode not in ['hard', 'soft']:
            raise ValueError(
                f"Invalid filter_mode: {self.filter_mode}. Must be 'hard' or 'soft'"
            )
        
        # Threshold strategy
        self.threshold_strategy = config.get('threshold_strategy', 'fixed')
        if self.threshold_strategy not in ['fixed', 'percentile', 'f1_optimal']:
            raise ValueError(
                f"Invalid threshold_strategy: {self.threshold_strategy}. "
                f"Must be 'fixed', 'percentile', or 'f1_optimal'"
            )
        
        # Percentile configuration
        self.percentile = config.get('percentile', 25)
        if not (0 < self.percentile < 100):
            raise ValueError(f"percentile must be in (0, 100), got {self.percentile}")
        
        # Soft filtering configuration
        self.soft_filter_weight_multiplier = config.get('soft_filter_weight_multiplier', 0.1)
        
        # Decision tracking
        self.track_decisions = config.get('track_decisions', True)
        self.filtering_history = []
        
        logger.info(
            f"HyperedgeRefiner initialized with mode={self.filter_mode}, "
            f"threshold_strategy={self.threshold_strategy}, "
            f"quality_threshold={self.quality_threshold}"
        )
    
    async def filter_low_quality(
        self,
        hyperedge_ids: List[str],
        ground_truth: Optional[Dict[str, bool]] = None
    ) -> Dict:
        """
        Filter low-quality hyperedges from the graph.
        
        Args:
            hyperedge_ids: List of hyperedge IDs to evaluate
            ground_truth: Optional ground truth labels for F1-optimal threshold
                         (dict mapping hyperedge_id to True/False)
        
        Returns:
            Dictionary with filtering results:
                - filtered: List of filtered hyperedge IDs
                - kept: List of kept hyperedge IDs
                - filter_rate: Proportion of hyperedges filtered
                - threshold_used: Actual threshold used for filtering
                - statistics: Filtering statistics
        
        Example:
            >>> result = await refiner.filter_low_quality(['he1', 'he2', 'he3'])
            >>> print(f"Filtered {result['filter_rate']:.1%} of hyperedges")
        """
        if not hyperedge_ids:
            logger.warning("No hyperedge IDs provided for filtering")
            return {
                'filtered': [],
                'kept': [],
                'filter_rate': 0.0,
                'threshold_used': self.quality_threshold,
                'statistics': {}
            }
        
        # 1. Collect quality scores
        quality_scores = await self._collect_quality_scores(hyperedge_ids)
        
        # 2. Determine threshold based on strategy
        threshold = await self._determine_threshold(
            quality_scores,
            ground_truth
        )
        
        logger.info(
            f"Filtering {len(hyperedge_ids)} hyperedges with threshold={threshold:.3f} "
            f"(strategy={self.threshold_strategy})"
        )
        
        # 3. Filter hyperedges
        filtered = []
        kept = []
        
        for he_id in hyperedge_ids:
            quality = quality_scores.get(he_id, 0.5)
            
            if quality < threshold:
                # Low quality - filter
                if self.filter_mode == 'hard':
                    await self._hard_filter(he_id)
                else:  # soft
                    await self._soft_filter(he_id)
                
                filtered.append(he_id)
                
                # Track decision
                if self.track_decisions:
                    self._record_decision(he_id, quality, threshold, 'filtered')
            else:
                # High quality - keep
                kept.append(he_id)
                
                # Track decision
                if self.track_decisions:
                    self._record_decision(he_id, quality, threshold, 'kept')
        
        # 4. Compute statistics
        filter_rate = len(filtered) / len(hyperedge_ids) if hyperedge_ids else 0.0
        
        statistics = {
            'total_evaluated': len(hyperedge_ids),
            'filtered_count': len(filtered),
            'kept_count': len(kept),
            'filter_rate': filter_rate,
            'avg_quality_filtered': np.mean([quality_scores[he_id] for he_id in filtered]) if filtered else 0.0,
            'avg_quality_kept': np.mean([quality_scores[he_id] for he_id in kept]) if kept else 0.0,
            'filter_mode': self.filter_mode,
            'threshold_strategy': self.threshold_strategy,
        }
        
        logger.info(
            f"Filtering complete: {len(filtered)} filtered ({filter_rate:.1%}), "
            f"{len(kept)} kept"
        )
        
        return {
            'filtered': filtered,
            'kept': kept,
            'filter_rate': filter_rate,
            'threshold_used': threshold,
            'statistics': statistics
        }
    
    async def _collect_quality_scores(
        self,
        hyperedge_ids: List[str]
    ) -> Dict[str, float]:
        """
        Collect quality scores for hyperedges.
        
        Args:
            hyperedge_ids: List of hyperedge IDs
        
        Returns:
            Dictionary mapping hyperedge_id to quality score
        """
        quality_scores = {}
        
        # Fetch nodes in parallel
        nodes = await asyncio.gather(
            *[self.graph.get_node(he_id) for he_id in hyperedge_ids],
            return_exceptions=True
        )
        
        for he_id, node in zip(hyperedge_ids, nodes):
            if isinstance(node, Exception):
                logger.warning(f"Failed to get node {he_id}: {node}")
                quality_scores[he_id] = 0.5  # Default quality
            elif node is None:
                logger.warning(f"Node {he_id} not found")
                quality_scores[he_id] = 0.5  # Default quality
            else:
                # Get quality score from node data
                quality = node.get('quality_score', 0.5)
                quality_scores[he_id] = quality
        
        return quality_scores
    
    async def _determine_threshold(
        self,
        quality_scores: Dict[str, float],
        ground_truth: Optional[Dict[str, bool]] = None
    ) -> float:
        """
        Determine filtering threshold based on strategy.
        
        Args:
            quality_scores: Dictionary mapping hyperedge_id to quality score
            ground_truth: Optional ground truth labels
        
        Returns:
            Threshold value
        """
        if self.threshold_strategy == 'fixed':
            return self.quality_threshold
        
        elif self.threshold_strategy == 'percentile':
            return self._percentile_threshold(quality_scores)
        
        elif self.threshold_strategy == 'f1_optimal':
            if ground_truth is None:
                logger.warning(
                    "F1-optimal strategy requires ground truth, "
                    "falling back to fixed threshold"
                )
                return self.quality_threshold
            return self._f1_optimal_threshold(quality_scores, ground_truth)
        
        else:
            raise ValueError(f"Unknown threshold strategy: {self.threshold_strategy}")
    
    def _percentile_threshold(self, quality_scores: Dict[str, float]) -> float:
        """
        Compute percentile-based threshold.
        
        Filters the bottom X% of hyperedges by quality score.
        
        Args:
            quality_scores: Dictionary mapping hyperedge_id to quality score
        
        Returns:
            Threshold at the specified percentile
        """
        if not quality_scores:
            return self.quality_threshold
        
        scores = list(quality_scores.values())
        threshold = np.percentile(scores, self.percentile)
        
        logger.info(
            f"Percentile threshold: {threshold:.3f} "
            f"(bottom {self.percentile}% of {len(scores)} hyperedges)"
        )
        
        return float(threshold)
    
    def _f1_optimal_threshold(
        self,
        quality_scores: Dict[str, float],
        ground_truth: Dict[str, bool]
    ) -> float:
        """
        Find F1-optimal threshold using ground truth labels.
        
        Searches for the threshold that maximizes F1 score for
        identifying low-quality hyperedges.
        
        Args:
            quality_scores: Dictionary mapping hyperedge_id to quality score
            ground_truth: Dictionary mapping hyperedge_id to True (good) / False (bad)
        
        Returns:
            Threshold that maximizes F1 score
        """
        # Get common hyperedge IDs
        common_ids = set(quality_scores.keys()) & set(ground_truth.keys())
        
        if not common_ids:
            logger.warning("No overlap between quality scores and ground truth")
            return self.quality_threshold
        
        # Prepare data
        scores = [quality_scores[he_id] for he_id in common_ids]
        labels = [ground_truth[he_id] for he_id in common_ids]
        
        # Try different thresholds
        candidate_thresholds = np.linspace(
            min(scores), max(scores), num=50
        )
        
        best_threshold = self.quality_threshold
        best_f1 = 0.0
        
        for threshold in candidate_thresholds:
            # Predict: quality < threshold => bad (False)
            predictions = [score >= threshold for score in scores]
            
            # Compute F1
            tp = sum(1 for pred, label in zip(predictions, labels) if pred and label)
            fp = sum(1 for pred, label in zip(predictions, labels) if pred and not label)
            fn = sum(1 for pred, label in zip(predictions, labels) if not pred and label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        logger.info(
            f"F1-optimal threshold: {best_threshold:.3f} (F1={best_f1:.3f})"
        )
        
        return float(best_threshold)
    
    async def _hard_filter(self, hyperedge_id: str):
        """
        Hard filter: Delete hyperedge from graph.
        
        Args:
            hyperedge_id: ID of hyperedge to delete
        """
        try:
            await self.graph.delete_node(hyperedge_id)
            logger.debug(f"Hard filtered (deleted) hyperedge: {hyperedge_id}")
        except Exception as e:
            logger.error(f"Failed to delete hyperedge {hyperedge_id}: {e}")
    
    async def _soft_filter(self, hyperedge_id: str):
        """
        Soft filter: Reduce dynamic weight but keep hyperedge.
        
        Args:
            hyperedge_id: ID of hyperedge to soft filter
        """
        try:
            node = await self.graph.get_node(hyperedge_id)
            if node is None:
                logger.warning(f"Node {hyperedge_id} not found for soft filtering")
                return
            
            # Reduce dynamic weight
            current_weight = node.get('dynamic_weight', node.get('weight', 1.0))
            new_weight = current_weight * self.soft_filter_weight_multiplier
            
            node['dynamic_weight'] = new_weight
            node['filtered'] = True
            node['filtered_at'] = datetime.now().isoformat()
            
            await self.graph.upsert_node(hyperedge_id, node)
            
            logger.debug(
                f"Soft filtered hyperedge {hyperedge_id}: "
                f"weight {current_weight:.3f} -> {new_weight:.3f}"
            )
        except Exception as e:
            logger.error(f"Failed to soft filter hyperedge {hyperedge_id}: {e}")
    
    def _record_decision(
        self,
        hyperedge_id: str,
        quality: float,
        threshold: float,
        decision: Literal['filtered', 'kept']
    ):
        """
        Record filtering decision for analysis.
        
        Args:
            hyperedge_id: ID of hyperedge
            quality: Quality score
            threshold: Threshold used
            decision: 'filtered' or 'kept'
        """
        self.filtering_history.append({
            'timestamp': datetime.now().isoformat(),
            'hyperedge_id': hyperedge_id,
            'quality': quality,
            'threshold': threshold,
            'decision': decision,
            'filter_mode': self.filter_mode,
            'threshold_strategy': self.threshold_strategy,
        })
        
        # Limit history size
        if len(self.filtering_history) > 10000:
            self.filtering_history = self.filtering_history[-10000:]
    
    async def batch_filter_low_quality(
        self,
        hyperedge_id_batches: List[List[str]],
        ground_truth: Optional[Dict[str, bool]] = None
    ) -> List[Dict]:
        """
        Batch filter multiple sets of hyperedges.
        
        Args:
            hyperedge_id_batches: List of hyperedge ID lists
            ground_truth: Optional ground truth labels
        
        Returns:
            List of filtering result dictionaries
        """
        tasks = [
            self.filter_low_quality(batch, ground_truth)
            for batch in hyperedge_id_batches
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        result_list = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch filtering failed for batch {i}: {result}")
                result_list.append({
                    'filtered': [],
                    'kept': [],
                    'filter_rate': 0.0,
                    'error': str(result)
                })
            else:
                result_list.append(result)
        
        return result_list
    
    def get_filtering_statistics(self) -> Dict:
        """
        Get overall filtering statistics.
        
        Returns:
            Dictionary with filtering statistics
        """
        if not self.filtering_history:
            return {
                'total_decisions': 0,
                'filtered_count': 0,
                'kept_count': 0,
                'filter_rate': 0.0,
            }
        
        filtered_count = sum(
            1 for d in self.filtering_history if d['decision'] == 'filtered'
        )
        kept_count = sum(
            1 for d in self.filtering_history if d['decision'] == 'kept'
        )
        total = len(self.filtering_history)
        
        filtered_qualities = [
            d['quality'] for d in self.filtering_history
            if d['decision'] == 'filtered'
        ]
        kept_qualities = [
            d['quality'] for d in self.filtering_history
            if d['decision'] == 'kept'
        ]
        
        return {
            'total_decisions': total,
            'filtered_count': filtered_count,
            'kept_count': kept_count,
            'filter_rate': filtered_count / total if total > 0 else 0.0,
            'avg_quality_filtered': float(np.mean(filtered_qualities)) if filtered_qualities else 0.0,
            'avg_quality_kept': float(np.mean(kept_qualities)) if kept_qualities else 0.0,
            'filter_mode': self.filter_mode,
            'threshold_strategy': self.threshold_strategy,
        }
    
    def clear_history(self):
        """Clear filtering history."""
        self.filtering_history.clear()
        logger.info("Cleared filtering history")
    
    def get_history_size(self) -> int:
        """Get filtering history size."""
        return len(self.filtering_history)
    
    async def restore_filtered_hyperedges(
        self,
        hyperedge_ids: Optional[List[str]] = None
    ) -> int:
        """
        Restore soft-filtered hyperedges to original weights.
        
        Note: This only works for soft-filtered hyperedges. Hard-filtered
        (deleted) hyperedges cannot be restored.
        
        Args:
            hyperedge_ids: List of hyperedge IDs to restore, or None to restore all
        
        Returns:
            Number of hyperedges restored
        """
        if self.filter_mode == 'hard':
            logger.warning("Cannot restore hard-filtered (deleted) hyperedges")
            return 0
        
        if hyperedge_ids is None:
            # Get all filtered hyperedges from history
            hyperedge_ids = [
                d['hyperedge_id'] for d in self.filtering_history
                if d['decision'] == 'filtered'
            ]
        
        restored_count = 0
        
        for he_id in hyperedge_ids:
            try:
                node = await self.graph.get_node(he_id)
                if node is None:
                    continue
                
                if not node.get('filtered', False):
                    continue
                
                # Restore weight
                quality_score = node.get('quality_score', 0.5)
                node['dynamic_weight'] = quality_score
                node['filtered'] = False
                node['restored_at'] = datetime.now().isoformat()
                
                await self.graph.upsert_node(he_id, node)
                restored_count += 1
                
                logger.debug(f"Restored hyperedge {he_id}")
            
            except Exception as e:
                logger.error(f"Failed to restore hyperedge {he_id}: {e}")
        
        logger.info(f"Restored {restored_count} hyperedges")
        return restored_count
    
    async def iterative_refine_hyperedges(
        self,
        hyperedge_ids: List[str],
        text_chunks_db,
        llm_model_func: callable,
        embedding_func: callable,
        quality_scorer,
        global_config: dict,
        max_iterations: int = 1
    ) -> Dict:
        """
        Iteratively refine low-quality hyperedges by triggering re-extraction.
        
        This method implements iterative refinement for low-quality hyperedges:
        1. Identify low-quality hyperedges
        2. Retrieve source text chunks
        3. Re-extract hyperedges using improved prompts
        4. Compare quality scores
        5. Replace if new hyperedge is better
        
        Args:
            hyperedge_ids: List of hyperedge IDs to potentially refine
            text_chunks_db: Text chunks database for retrieving source text
            llm_model_func: LLM function for re-extraction
            embedding_func: Embedding function for quality computation
            quality_scorer: QualityScorer instance for computing quality
            global_config: Global configuration dictionary
            max_iterations: Maximum refinement iterations per hyperedge (default: 1)
        
        Returns:
            Dictionary with refinement results:
                - refined_count: Number of hyperedges refined
                - improved_count: Number of hyperedges with quality improvement
                - failed_count: Number of refinement failures
                - quality_improvements: List of quality improvements
                - refinement_details: Detailed refinement information
        
        Example:
            >>> result = await refiner.iterative_refine_hyperedges(
            ...     low_quality_ids,
            ...     text_chunks_db,
            ...     llm_func,
            ...     embedding_func,
            ...     scorer,
            ...     config
            ... )
            >>> print(f"Refined {result['improved_count']} hyperedges")
        """
        from ..prompt import PROMPTS, GRAPH_FIELD_SEP
        from ..utils import (
            clean_str,
            split_string_by_multi_markers,
            is_float_regex,
        )
        import re
        
        logger.info(
            f"Starting iterative refinement for {len(hyperedge_ids)} hyperedges "
            f"(max_iterations={max_iterations})"
        )
        
        refined_count = 0
        improved_count = 0
        failed_count = 0
        quality_improvements = []
        refinement_details = []
        
        for he_id in hyperedge_ids:
            try:
                # 1. Get current hyperedge and quality
                node = await self.graph.get_node(he_id)
                if node is None:
                    logger.warning(f"Hyperedge {he_id} not found")
                    failed_count += 1
                    continue
                
                current_quality = node.get('quality_score', 0.5)
                
                # Skip if quality is already good
                if current_quality >= self.quality_threshold:
                    logger.debug(f"Hyperedge {he_id} quality already good: {current_quality:.3f}")
                    continue
                
                # 2. Get source text chunks
                source_ids = node.get('source_id', '').split(GRAPH_FIELD_SEP)
                if not source_ids or source_ids == ['']:
                    logger.warning(f"No source_id for hyperedge {he_id}")
                    failed_count += 1
                    continue
                
                # Retrieve source text
                source_texts = []
                for src_id in source_ids:
                    chunk = await text_chunks_db.get_by_id(src_id)
                    if chunk:
                        source_texts.append(chunk.get('content', ''))
                
                if not source_texts:
                    logger.warning(f"No source text found for hyperedge {he_id}")
                    failed_count += 1
                    continue
                
                combined_text = "\n\n".join(source_texts)
                
                # 3. Iterative refinement
                best_quality = current_quality
                best_hyperedge_text = node.get('hyperedge', '')
                best_entities = []
                
                for iteration in range(max_iterations):
                    logger.debug(
                        f"Refinement iteration {iteration + 1}/{max_iterations} "
                        f"for hyperedge {he_id}"
                    )
                    
                    # 4. Re-extract with improved prompt
                    new_hyperedge_text, new_entities = await self._re_extract_hyperedge(
                        combined_text,
                        current_hyperedge=best_hyperedge_text,
                        current_quality=best_quality,
                        llm_model_func=llm_model_func,
                        global_config=global_config,
                        iteration=iteration
                    )
                    
                    if not new_hyperedge_text:
                        logger.warning(f"Re-extraction failed for hyperedge {he_id}")
                        continue
                    
                    # 5. Compute quality of new hyperedge
                    # Create temporary node for quality computation
                    temp_node_id = f"{he_id}_temp_{iteration}"
                    temp_node = {
                        'role': 'hyperedge',
                        'hyperedge': new_hyperedge_text,
                        'source_id': node.get('source_id', ''),
                        'weight': node.get('weight', 1.0),
                    }
                    
                    # Temporarily insert for quality computation
                    await self.graph.upsert_node(temp_node_id, temp_node)
                    
                    # Add temporary edges to entities
                    for entity_name in new_entities:
                        await self.graph.upsert_edge(
                            temp_node_id,
                            entity_name,
                            edge_data={'weight': 1.0, 'source_id': node.get('source_id', '')}
                        )
                    
                    # Compute quality
                    try:
                        quality_result = await quality_scorer.compute_quality_score(temp_node_id)
                        new_quality = quality_result['quality_score']
                    except Exception as e:
                        logger.error(f"Quality computation failed: {e}")
                        new_quality = 0.0
                    
                    # Clean up temporary node
                    await self.graph.delete_node(temp_node_id)
                    
                    logger.debug(
                        f"New hyperedge quality: {new_quality:.3f} "
                        f"(current best: {best_quality:.3f})"
                    )
                    
                    # 6. Compare and keep best
                    if new_quality > best_quality:
                        best_quality = new_quality
                        best_hyperedge_text = new_hyperedge_text
                        best_entities = new_entities
                        logger.info(
                            f"Quality improved for {he_id}: "
                            f"{current_quality:.3f} -> {new_quality:.3f}"
                        )
                
                # 7. Replace if improved
                if best_quality > current_quality:
                    # Update hyperedge
                    node['hyperedge'] = best_hyperedge_text
                    node['quality_score'] = best_quality
                    node['refined'] = True
                    node['refined_at'] = datetime.now().isoformat()
                    node['previous_quality'] = current_quality
                    
                    await self.graph.upsert_node(he_id, node)
                    
                    # Update edges if entities changed
                    if best_entities:
                        # Remove old edges
                        old_edges = await self.graph.get_node_edges(he_id)
                        for edge in old_edges:
                            await self.graph.delete_edge(he_id, edge[1])
                        
                        # Add new edges
                        for entity_name in best_entities:
                            await self.graph.upsert_edge(
                                he_id,
                                entity_name,
                                edge_data={
                                    'weight': node.get('weight', 1.0),
                                    'source_id': node.get('source_id', '')
                                }
                            )
                    
                    improved_count += 1
                    quality_improvement = best_quality - current_quality
                    quality_improvements.append(quality_improvement)
                    
                    refinement_details.append({
                        'hyperedge_id': he_id,
                        'old_quality': current_quality,
                        'new_quality': best_quality,
                        'improvement': quality_improvement,
                        'old_text': node.get('hyperedge', ''),
                        'new_text': best_hyperedge_text,
                    })
                    
                    logger.info(
                        f"Replaced hyperedge {he_id}: "
                        f"quality {current_quality:.3f} -> {best_quality:.3f}"
                    )
                else:
                    logger.debug(
                        f"No improvement for hyperedge {he_id}, keeping original"
                    )
                
                refined_count += 1
                
            except Exception as e:
                logger.error(f"Refinement failed for hyperedge {he_id}: {e}")
                failed_count += 1
        
        # Summary statistics
        avg_improvement = (
            float(np.mean(quality_improvements))
            if quality_improvements else 0.0
        )
        
        result = {
            'refined_count': refined_count,
            'improved_count': improved_count,
            'failed_count': failed_count,
            'improvement_rate': improved_count / refined_count if refined_count > 0 else 0.0,
            'avg_quality_improvement': avg_improvement,
            'quality_improvements': quality_improvements,
            'refinement_details': refinement_details,
        }
        
        logger.info(
            f"Iterative refinement complete: "
            f"{improved_count}/{refined_count} improved "
            f"(avg improvement: {avg_improvement:.3f}), "
            f"{failed_count} failed"
        )
        
        return result
    
    async def _re_extract_hyperedge(
        self,
        source_text: str,
        current_hyperedge: str,
        current_quality: float,
        llm_model_func: callable,
        global_config: dict,
        iteration: int = 0
    ) -> tuple[str, List[str]]:
        """
        Re-extract hyperedge from source text using improved prompt.
        
        Args:
            source_text: Source text to extract from
            current_hyperedge: Current hyperedge text
            current_quality: Current quality score
            llm_model_func: LLM function for extraction
            global_config: Global configuration
            iteration: Current iteration number
        
        Returns:
            Tuple of (new_hyperedge_text, entity_names)
        """
        from ..prompt import PROMPTS, GRAPH_FIELD_SEP
        from ..utils import clean_str, split_string_by_multi_markers, is_float_regex
        import re
        
        # Build improved prompt with feedback
        language = global_config["addon_params"].get(
            "language", PROMPTS["DEFAULT_LANGUAGE"]
        )
        entity_types = global_config["addon_params"].get(
            "entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"]
        )
        
        context_base = dict(
            tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
            record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
            completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
            language=language,
        )
        
        # Create refinement prompt
        refinement_prompt = f"""---Role---
You are an expert knowledge extraction assistant tasked with improving the quality of extracted knowledge fragments.

---Context---
The following knowledge fragment was previously extracted but has low quality (score: {current_quality:.2f}/1.0).
Current fragment: "{current_hyperedge}"

---Goal---
Re-extract a higher quality knowledge fragment from the source text that:
1. Is more complete and coherent
2. Captures the most important relationships
3. Connects relevant entities clearly
4. Is factually accurate and well-formed

---Instructions---
Extract knowledge fragments and entities using the same format as before:
- Knowledge fragments: ("hyper-relation"{context_base['tuple_delimiter']}<knowledge_segment>{context_base['tuple_delimiter']}<completeness_score>)
- Entities: ("entity"{context_base['tuple_delimiter']}<entity_name>{context_base['tuple_delimiter']}<entity_type>{context_base['tuple_delimiter']}<description>{context_base['tuple_delimiter']}<key_score>)

Focus on extracting ONE high-quality knowledge fragment that improves upon the current one.
Use {language} as output language.

---Source Text---
{source_text}

---Output---
"""
        
        try:
            # Call LLM
            result = await llm_model_func(refinement_prompt)
            
            # Parse result
            records = split_string_by_multi_markers(
                result,
                [context_base["record_delimiter"], context_base["completion_delimiter"]],
            )
            
            new_hyperedge_text = None
            entity_names = []
            
            for record in records:
                record_match = re.search(r"\((.*)\)", record)
                if record_match is None:
                    continue
                
                record_content = record_match.group(1)
                attributes = split_string_by_multi_markers(
                    record_content, [context_base["tuple_delimiter"]]
                )
                
                # Extract hyperedge
                if len(attributes) >= 3 and attributes[0] == '"hyper-relation"':
                    new_hyperedge_text = "<hyperedge>" + clean_str(attributes[1])
                
                # Extract entities
                elif len(attributes) >= 5 and attributes[0] == '"entity"':
                    entity_name = clean_str(attributes[1].upper())
                    if entity_name.strip():
                        entity_names.append(entity_name)
            
            if new_hyperedge_text:
                logger.debug(
                    f"Re-extracted hyperedge (iteration {iteration}): "
                    f"{new_hyperedge_text[:100]}..."
                )
                return new_hyperedge_text, entity_names
            else:
                logger.warning(f"No hyperedge extracted in iteration {iteration}")
                return None, []
        
        except Exception as e:
            logger.error(f"Re-extraction failed: {e}")
            return None, []


# Helper functions

def analyze_quality_distribution(quality_scores: Dict[str, float]) -> Dict:
    """
    Analyze quality score distribution.
    
    Args:
        quality_scores: Dictionary mapping hyperedge_id to quality score
    
    Returns:
        Distribution statistics
    """
    if not quality_scores:
        return {}
    
    scores = list(quality_scores.values())
    
    return {
        'count': len(scores),
        'mean': float(np.mean(scores)),
        'std': float(np.std(scores)),
        'min': float(np.min(scores)),
        'max': float(np.max(scores)),
        'median': float(np.median(scores)),
        'q25': float(np.percentile(scores, 25)),
        'q75': float(np.percentile(scores, 75)),
        'below_0.3': sum(1 for s in scores if s < 0.3),
        'below_0.5': sum(1 for s in scores if s < 0.5),
        'above_0.7': sum(1 for s in scores if s > 0.7),
    }


def compute_filtering_metrics(
    filtered_ids: List[str],
    kept_ids: List[str],
    ground_truth: Dict[str, bool]
) -> Dict:
    """
    Compute filtering performance metrics against ground truth.
    
    Args:
        filtered_ids: List of filtered hyperedge IDs
        kept_ids: List of kept hyperedge IDs
        ground_truth: Dictionary mapping hyperedge_id to True (good) / False (bad)
    
    Returns:
        Performance metrics (precision, recall, F1, accuracy)
    """
    # True positives: kept good hyperedges
    tp = sum(1 for he_id in kept_ids if ground_truth.get(he_id, False))
    
    # False positives: kept bad hyperedges
    fp = sum(1 for he_id in kept_ids if not ground_truth.get(he_id, True))
    
    # False negatives: filtered good hyperedges
    fn = sum(1 for he_id in filtered_ids if ground_truth.get(he_id, False))
    
    # True negatives: filtered bad hyperedges
    tn = sum(1 for he_id in filtered_ids if not ground_truth.get(he_id, True))
    
    # Compute metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
    }
