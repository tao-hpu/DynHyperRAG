"""
Dynamic Weight Updater for DynHyperRAG

This module implements dynamic weight adjustment for hyperedges based on
retrieval feedback and quality scores. It supports multiple update strategies
and includes constraints to prevent unbounded weight growth.

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
from typing import Dict, Optional, List
from datetime import datetime

from ..base import BaseGraphStorage
from ..utils import logger


class WeightUpdater:
    """
    Dynamic weight updater for hyperedges.
    
    This class implements three update strategies:
    - EMA (Exponential Moving Average): Smooth updates with momentum
    - Additive: Direct addition of feedback signals
    - Multiplicative: Proportional updates based on current weight
    
    Features:
    - Configurable update strategies
    - Decay factor to prevent unbounded growth
    - Quality-based constraints
    - Update history tracking
    
    Args:
        graph: BaseGraphStorage instance for accessing and updating nodes
        config: Configuration dictionary with the following keys:
            - strategy: Update strategy ('ema', 'additive', 'multiplicative')
            - update_alpha: Learning rate for updates (0 < alpha <= 1)
            - decay_factor: Decay factor to prevent unbounded growth (0 < decay <= 1)
            - min_weight_ratio: Minimum weight as ratio of quality score (default: 0.5)
            - max_weight_ratio: Maximum weight as ratio of quality score (default: 2.0)
            - track_history: Whether to track update history (default: True)
    
    Example:
        >>> config = {
        ...     'strategy': 'ema',
        ...     'update_alpha': 0.1,
        ...     'decay_factor': 0.99
        ... }
        >>> updater = WeightUpdater(graph, config)
        >>> new_weight = await updater.update_weights('hyperedge_1', 0.8)
    """
    
    def __init__(self, graph: BaseGraphStorage, config: dict):
        """Initialize the weight updater."""
        self.graph = graph
        
        # Update strategy configuration
        self.strategy = config.get('strategy', 'ema')
        if self.strategy not in ['ema', 'additive', 'multiplicative']:
            raise ValueError(
                f"Invalid strategy: {self.strategy}. "
                f"Must be 'ema', 'additive', or 'multiplicative'"
            )
        
        # Learning rate (alpha)
        self.alpha = config.get('update_alpha', 0.1)
        if not (0.0 < self.alpha <= 1.0):
            raise ValueError(f"update_alpha must be in (0, 1], got {self.alpha}")
        
        # Decay factor
        self.decay = config.get('decay_factor', 0.99)
        if not (0.0 < self.decay <= 1.0):
            raise ValueError(f"decay_factor must be in (0, 1], got {self.decay}")
        
        # Weight constraints
        self.min_weight_ratio = config.get('min_weight_ratio', 0.5)
        self.max_weight_ratio = config.get('max_weight_ratio', 2.0)
        
        # History tracking
        self.track_history = config.get('track_history', True)
        self.max_history_length = config.get('max_history_length', 100)
        
        logger.info(
            f"WeightUpdater initialized with strategy={self.strategy}, "
            f"alpha={self.alpha}, decay={self.decay}"
        )
    
    async def update_weights(
        self,
        hyperedge_id: str,
        feedback_signal: float,
        metadata: Optional[Dict] = None
    ) -> float:
        """
        Update the weight of a hyperedge based on feedback signal.
        
        Args:
            hyperedge_id: ID of the hyperedge to update
            feedback_signal: Feedback signal (0-1), where:
                - 1.0 = highly useful
                - 0.5 = neutral
                - 0.0 = not useful
            metadata: Optional metadata about the update (e.g., query, timestamp)
        
        Returns:
            The new dynamic weight after update
        
        Raises:
            ValueError: If hyperedge_id doesn't exist or feedback_signal is invalid
        """
        # Validate feedback signal
        if not (0.0 <= feedback_signal <= 1.0):
            raise ValueError(
                f"feedback_signal must be in [0, 1], got {feedback_signal}"
            )
        
        # Get current node data
        node = await self.graph.get_node(hyperedge_id)
        if node is None:
            raise ValueError(f"Hyperedge {hyperedge_id} not found in graph")
        
        # Get current weight and quality score
        current_weight = node.get('dynamic_weight', node.get('weight', 1.0))
        quality_score = node.get('quality_score', 0.5)
        
        # Apply update strategy
        if self.strategy == 'ema':
            new_weight = self._ema_update(current_weight, feedback_signal)
        elif self.strategy == 'additive':
            new_weight = self._additive_update(current_weight, feedback_signal)
        elif self.strategy == 'multiplicative':
            new_weight = self._multiplicative_update(current_weight, feedback_signal)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Apply decay
        new_weight = self._apply_decay(new_weight)
        
        # Apply quality constraints
        new_weight = self._apply_quality_constraints(new_weight, quality_score)
        
        # Update node data
        node['dynamic_weight'] = new_weight
        
        # Track update history
        if self.track_history:
            self._add_to_history(node, current_weight, new_weight, feedback_signal, metadata)
        
        # Update feedback count
        node['feedback_count'] = node.get('feedback_count', 0) + 1
        node['last_updated'] = datetime.now().isoformat()
        
        # Save to graph
        await self.graph.upsert_node(hyperedge_id, node)
        
        logger.debug(
            f"Updated {hyperedge_id}: {current_weight:.4f} -> {new_weight:.4f} "
            f"(feedback={feedback_signal:.4f}, strategy={self.strategy})"
        )
        
        return new_weight
    
    async def batch_update_weights(
        self,
        updates: List[Dict[str, any]]
    ) -> Dict[str, float]:
        """
        Batch update multiple hyperedges.
        
        Args:
            updates: List of update dictionaries, each containing:
                - hyperedge_id: ID of the hyperedge
                - feedback_signal: Feedback signal (0-1)
                - metadata: Optional metadata
        
        Returns:
            Dictionary mapping hyperedge_id to new weight
        
        Example:
            >>> updates = [
            ...     {'hyperedge_id': 'he1', 'feedback_signal': 0.8},
            ...     {'hyperedge_id': 'he2', 'feedback_signal': 0.3}
            ... ]
            >>> results = await updater.batch_update_weights(updates)
        """
        tasks = []
        for update in updates:
            task = self.update_weights(
                update['hyperedge_id'],
                update['feedback_signal'],
                update.get('metadata')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dictionary
        result_dict = {}
        for update, result in zip(updates, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to update {update['hyperedge_id']}: {result}"
                )
                result_dict[update['hyperedge_id']] = None
            else:
                result_dict[update['hyperedge_id']] = result
        
        logger.info(
            f"Batch updated {len(updates)} hyperedges, "
            f"{sum(1 for v in result_dict.values() if v is not None)} succeeded"
        )
        
        return result_dict
    
    def _ema_update(self, current: float, feedback: float) -> float:
        """
        Exponential Moving Average (EMA) update.
        
        Formula: w_t = (1 - α) * w_{t-1} + α * f_t
        
        This provides smooth updates with momentum, where recent feedback
        has more influence but historical performance is retained.
        
        Args:
            current: Current weight
            feedback: Feedback signal (0-1)
        
        Returns:
            Updated weight
        """
        return (1 - self.alpha) * current + self.alpha * feedback
    
    def _additive_update(self, current: float, feedback: float) -> float:
        """
        Additive update strategy.
        
        Formula: w_t = w_{t-1} + α * (f_t - 0.5)
        
        This adds or subtracts from the current weight based on whether
        feedback is positive (> 0.5) or negative (< 0.5).
        
        Args:
            current: Current weight
            feedback: Feedback signal (0-1)
        
        Returns:
            Updated weight
        """
        return current + self.alpha * (feedback - 0.5)
    
    def _multiplicative_update(self, current: float, feedback: float) -> float:
        """
        Multiplicative update strategy.
        
        Formula: w_t = w_{t-1} * (1 + α * (f_t - 0.5))
        
        This scales the weight proportionally, making larger weights
        change more dramatically than smaller weights.
        
        Args:
            current: Current weight
            feedback: Feedback signal (0-1)
        
        Returns:
            Updated weight
        """
        return current * (1 + self.alpha * (feedback - 0.5))
    
    def _apply_decay(self, weight: float) -> float:
        """
        Apply decay factor to prevent unbounded weight growth.
        
        This ensures that weights gradually decrease over time unless
        continuously reinforced by positive feedback.
        
        Args:
            weight: Weight before decay
        
        Returns:
            Weight after decay
        """
        return weight * self.decay
    
    def _apply_quality_constraints(self, weight: float, quality_score: float) -> float:
        """
        Apply quality-based constraints to the weight.
        
        Ensures that dynamic weight stays within reasonable bounds
        relative to the hyperedge's quality score:
        - Minimum: quality_score * min_weight_ratio
        - Maximum: quality_score * max_weight_ratio
        
        This prevents low-quality hyperedges from gaining excessive weight
        and ensures high-quality hyperedges maintain minimum weight.
        
        Args:
            weight: Weight before constraints
            quality_score: Quality score of the hyperedge (0-1)
        
        Returns:
            Constrained weight
        """
        min_weight = quality_score * self.min_weight_ratio
        max_weight = quality_score * self.max_weight_ratio
        
        return max(min_weight, min(max_weight, weight))
    
    def _add_to_history(
        self,
        node: dict,
        old_weight: float,
        new_weight: float,
        feedback: float,
        metadata: Optional[Dict]
    ):
        """
        Add update to history tracking.
        
        Maintains a history of weight updates for analysis and debugging.
        History is stored in the node data under 'weight_history' key.
        
        Args:
            node: Node data dictionary
            old_weight: Weight before update
            new_weight: Weight after update
            feedback: Feedback signal that triggered update
            metadata: Optional metadata about the update
        """
        if 'weight_history' not in node:
            node['weight_history'] = []
        
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'old_weight': old_weight,
            'new_weight': new_weight,
            'feedback': feedback,
            'strategy': self.strategy,
        }
        
        if metadata:
            history_entry['metadata'] = metadata
        
        node['weight_history'].append(history_entry)
        
        # Limit history length to prevent unbounded growth
        if len(node['weight_history']) > self.max_history_length:
            node['weight_history'] = node['weight_history'][-self.max_history_length:]
    
    async def get_update_statistics(self, hyperedge_id: str) -> Optional[Dict]:
        """
        Get statistics about weight updates for a hyperedge.
        
        Args:
            hyperedge_id: ID of the hyperedge
        
        Returns:
            Dictionary with statistics or None if hyperedge not found:
                - feedback_count: Total number of updates
                - last_updated: Timestamp of last update
                - current_weight: Current dynamic weight
                - quality_score: Quality score
                - avg_feedback: Average feedback signal received
                - weight_trend: 'increasing', 'decreasing', or 'stable'
        """
        node = await self.graph.get_node(hyperedge_id)
        if node is None:
            return None
        
        stats = {
            'feedback_count': node.get('feedback_count', 0),
            'last_updated': node.get('last_updated', 'never'),
            'current_weight': node.get('dynamic_weight', node.get('weight', 1.0)),
            'quality_score': node.get('quality_score', 0.5),
        }
        
        # Calculate average feedback if history exists
        if 'weight_history' in node and node['weight_history']:
            history = node['weight_history']
            stats['avg_feedback'] = sum(h['feedback'] for h in history) / len(history)
            
            # Determine weight trend
            if len(history) >= 2:
                recent_weights = [h['new_weight'] for h in history[-10:]]
                if recent_weights[-1] > recent_weights[0] * 1.05:
                    stats['weight_trend'] = 'increasing'
                elif recent_weights[-1] < recent_weights[0] * 0.95:
                    stats['weight_trend'] = 'decreasing'
                else:
                    stats['weight_trend'] = 'stable'
        
        return stats
    
    async def reset_weights(self, hyperedge_ids: Optional[List[str]] = None):
        """
        Reset dynamic weights to initial values (quality scores).
        
        Args:
            hyperedge_ids: List of hyperedge IDs to reset, or None to reset all
        
        Note:
            This is useful for experiments or when restarting the system.
        """
        if hyperedge_ids is None:
            logger.warning("reset_weights with hyperedge_ids=None not implemented")
            return
        
        for he_id in hyperedge_ids:
            node = await self.graph.get_node(he_id)
            if node is None:
                continue
            
            # Reset to quality score or original weight
            initial_weight = node.get('quality_score', node.get('weight', 1.0))
            node['dynamic_weight'] = initial_weight
            node['feedback_count'] = 0
            node['last_updated'] = datetime.now().isoformat()
            
            if 'weight_history' in node:
                node['weight_history'] = []
            
            await self.graph.upsert_node(he_id, node)
        
        logger.info(f"Reset weights for {len(hyperedge_ids)} hyperedges")
