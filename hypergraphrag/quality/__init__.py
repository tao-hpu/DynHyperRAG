"""
Quality Assessment Module for DynHyperRAG

This module provides functionality for evaluating hyperedge quality based on
graph structure features and semantic coherence.
"""

from .features import GraphFeatureExtractor, normalize_features
from .coherence import CoherenceMetric, compute_coherence_statistics
from .scorer import (
    QualityScorer,
    compute_quality_statistics,
    analyze_feature_distribution
)
from .analyzer import FeatureAnalyzer, compare_feature_importance_methods

__all__ = [
    'GraphFeatureExtractor',
    'normalize_features',
    'CoherenceMetric',
    'compute_coherence_statistics',
    'QualityScorer',
    'compute_quality_statistics',
    'analyze_feature_distribution',
    'FeatureAnalyzer',
    'compare_feature_importance_methods',
]

# Implementation status:
# ✅ Task 2: GraphFeatureExtractor (features.py)
# ✅ Task 3: CoherenceMetric (coherence.py)
# ✅ Task 4: QualityScorer (scorer.py)
# ✅ Task 5: FeatureAnalyzer (analyzer.py)
