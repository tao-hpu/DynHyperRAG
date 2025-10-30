"""
Efficient Retrieval Module for DynHyperRAG

This module provides functionality for efficient hyperedge retrieval using
entity type filtering and quality-aware ranking.
"""

from .entity_filter import EntityTypeFilter
from .quality_ranker import QualityAwareRanker, rank_by_quality
from .lite_retriever import LiteRetriever
from .performance_monitor import (
    PerformanceMonitor,
    RetrievalTracker,
    RetrievalMetrics,
    get_global_monitor,
    set_global_monitor
)

__all__ = [
    'EntityTypeFilter',
    'QualityAwareRanker',
    'rank_by_quality',
    'LiteRetriever',
    'PerformanceMonitor',
    'RetrievalTracker',
    'RetrievalMetrics',
    'get_global_monitor',
    'set_global_monitor',
]

# Implemented:
# - Task 10: EntityTypeFilter ✓
# - Task 11: QualityAwareRanker ✓
# - Task 12: LiteRetriever ✓
# - Task 13.2: PerformanceMonitor ✓
