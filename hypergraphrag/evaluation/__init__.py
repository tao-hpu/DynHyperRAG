"""
Evaluation Framework for DynHyperRAG

This module provides comprehensive evaluation metrics, baseline methods,
and experiment pipeline for assessing DynHyperRAG performance.
"""

# Note: Actual implementations will be added in later tasks
# For now, we define the module structure

__all__ = [
    'IntrinsicMetrics',
    'ExtrinsicMetrics', 
    'EfficiencyMetrics',
    'StatisticalTests',
    'BaselineMethods',
    'StaticHyperGraphRAG',
    'BaselineComparator',
    'ExperimentPipeline',
    'FeatureAblationExperiment',
    'ModuleAblationExperiment',
    'AblationStudyRunner',
    'run_ablation_studies',
]

# Import implemented classes
try:
    from .metrics import IntrinsicMetrics, ExtrinsicMetrics, EfficiencyMetrics, StatisticalTests
except ImportError:
    # Metrics not yet implemented
    pass

try:
    from .baselines import BaselineMethods, StaticHyperGraphRAG, BaselineComparator
except ImportError:
    # Baselines not yet implemented
    pass

try:
    from .pipeline import ExperimentPipeline, load_experiment_config, run_experiment_from_config
except ImportError:
    # Pipeline not yet implemented
    pass

try:
    from .ablation import (
        FeatureAblationExperiment,
        ModuleAblationExperiment,
        AblationStudyRunner,
        run_ablation_studies
    )
except ImportError:
    # Ablation studies not yet implemented
    pass

# Placeholder classes will be implemented in:
# - Task 17: IntrinsicMetrics, ExtrinsicMetrics, EfficiencyMetrics ✓
# - Task 18: BaselineMethods, StaticHyperGraphRAG ✓
# - Task 19: StatisticalTests ✓
# - Task 20: ExperimentPipeline ✓
# - Task 22: FeatureAblationExperiment, ModuleAblationExperiment ✓
