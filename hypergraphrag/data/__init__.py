"""
Data Processing Module for DynHyperRAG

This module provides data loaders and preprocessing utilities for various
datasets including CAIL2019 (legal) and academic datasets.
"""

from hypergraphrag.data.cail2019_loader import CAIL2019Loader

__all__ = [
    'CAIL2019Loader',
    'AcademicLoader',
    'QualityAnnotator',
]

# Implemented:
# - Task 14.1: CAIL2019Loader ✓

# To be implemented:
# - Task 15: AcademicLoader
# - Task 16: QualityAnnotator
