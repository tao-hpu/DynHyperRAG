"""
Ablation Studies for DynHyperRAG

This module implements comprehensive ablation experiments to measure the contribution
of individual features and modules to the overall system performance.

Ablation studies include:
1. Feature Ablation - Disable individual quality features to measure their contribution
2. Module Ablation - Disable entire modules (quality assessment, dynamic updates, entity filtering)
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime

from ..base import BaseGraphStorage, BaseVectorStorage, QueryParam
from .metrics import IntrinsicMetrics, ExtrinsicMetrics, EfficiencyMetrics, StatisticalTests

logger = logging.getLogger(__name__)

# Optional imports
try:
    from ..quality import QualityScorer
    QUALITY_SCORER_AVAILABLE = True
except ImportError:
    QUALITY_SCORER_AVAILABLE = False
    logger.debug("QualityScorer not available")

try:
    from ..dynamic import WeightUpdater
    WEIGHT_UPDATER_AVAILABLE = True
except ImportError:
    WEIGHT_UPDATER_AVAILABLE = False
    logger.debug("WeightUpdater not available")

try:
    from ..retrieval import EntityTypeFilter, QualityAwareRanker
    RETRIEVAL_MODULES_AVAILABLE = True
except ImportError:
    RETRIEVAL_MODULES_AVAILABLE = False
    logger.debug("Retrieval modules not available")


class FeatureAblationExperiment:
    """
    Feature Ablation Experiment
    
    This class implements experiments to measure the contribution of individual
    quality features by systematically disabling them one at a time.
    
    Quality features tested:
    - degree_centrality: Node connectivity
    - betweenness: Bridge importance
    - clustering: Local density
    - coherence: Semantic consistency
    - text_quality: Text completeness
    """
    
    def __init__(self, graph_storage: BaseGraphStorage, config: Dict[str, Any]):
        """
        Initialize feature ablation experiment.
        
        Args:
            graph_storage: Graph storage instance
            config: Configuration dictionary
        """
        self.graph_storage = graph_storage
        self.config = config
        
        # Default feature weights (from design document)
        self.default_weights = {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        }
        
        # Results storage
        self.results = {}
        
        logger.info("Initialized FeatureAblationExperiment")
    
    async def run_ablation_study(self, hyperedge_ids: List[str],
                                ground_truth: Optional[Dict[str, float]] = None,
                                test_queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run complete feature ablation study.
        
        This method:
        1. Tests full model with all features
        2. Tests model with each feature disabled individually
        3. Compares performance to measure feature contribution
        
        Args:
            hyperedge_ids: List of hyperedge IDs to evaluate
            ground_truth: Optional ground truth quality scores
            test_queries: Optional test queries for retrieval evaluation
            
        Returns:
            Dictionary containing ablation results
        """
        logger.info("=" * 80)
        logger.info("Starting Feature Ablation Study")
        logger.info(f"Testing {len(hyperedge_ids)} hyperedges")
        logger.info(f"Features to ablate: {list(self.default_weights.keys())}")
        logger.info("=" * 80)
        
        results = {
            'full_model': None,
            'ablated_models': {},
            'feature_contributions': {},
            'statistical_tests': {},
            'summary': {}
        }
        
        # Step 1: Evaluate full model (all features enabled)
        logger.info("\n[1/6] Evaluating full model (all features)...")
        full_model_scores = await self._evaluate_with_features(
            hyperedge_ids,
            enabled_features=list(self.default_weights.keys())
        )
        results['full_model'] = {
            'scores': full_model_scores,
            'mean_score': np.mean(list(full_model_scores.values())),
            'std_score': np.std(list(full_model_scores.values()))
        }
        logger.info(f"✓ Full model mean score: {results['full_model']['mean_score']:.4f}")
        
        # Step 2: Ablate each feature individually
        logger.info("\n[2/6] Running individual feature ablations...")
        for feature_name in self.default_weights.keys():
            logger.info(f"  Ablating feature: {feature_name}")
            
            # Get list of features excluding the current one
            enabled_features = [f for f in self.default_weights.keys() if f != feature_name]
            
            # Evaluate without this feature
            ablated_scores = await self._evaluate_with_features(
                hyperedge_ids,
                enabled_features=enabled_features
            )
            
            results['ablated_models'][feature_name] = {
                'scores': ablated_scores,
                'mean_score': np.mean(list(ablated_scores.values())),
                'std_score': np.std(list(ablated_scores.values())),
                'disabled_feature': feature_name
            }
            
            logger.info(f"    Mean score without {feature_name}: "
                       f"{results['ablated_models'][feature_name]['mean_score']:.4f}")
        
        # Step 3: Calculate feature contributions
        logger.info("\n[3/6] Calculating feature contributions...")
        for feature_name in self.default_weights.keys():
            full_mean = results['full_model']['mean_score']
            ablated_mean = results['ablated_models'][feature_name]['mean_score']
            
            # Contribution = performance drop when feature is removed
            contribution = full_mean - ablated_mean
            contribution_percent = (contribution / full_mean * 100) if full_mean != 0 else 0
            
            results['feature_contributions'][feature_name] = {
                'absolute_contribution': contribution,
                'relative_contribution_percent': contribution_percent,
                'feature_weight': self.default_weights[feature_name]
            }
            
            logger.info(f"  {feature_name}: {contribution:+.4f} ({contribution_percent:+.2f}%)")
        
        # Step 4: Statistical significance testing
        if ground_truth:
            logger.info("\n[4/6] Performing statistical tests...")
            results['statistical_tests'] = await self._statistical_comparison(
                full_model_scores,
                results['ablated_models'],
                ground_truth
            )
        else:
            logger.info("\n[4/6] Skipping statistical tests (no ground truth)")
        
        # Step 5: Rank features by importance
        logger.info("\n[5/6] Ranking features by importance...")
        feature_ranking = sorted(
            results['feature_contributions'].items(),
            key=lambda x: x[1]['absolute_contribution'],
            reverse=True
        )
        results['summary']['feature_ranking'] = [
            {
                'rank': i + 1,
                'feature': feature_name,
                'contribution': contrib['absolute_contribution'],
                'contribution_percent': contrib['relative_contribution_percent']
            }
            for i, (feature_name, contrib) in enumerate(feature_ranking)
        ]
        
        logger.info("  Feature importance ranking:")
        for item in results['summary']['feature_ranking']:
            logger.info(f"    {item['rank']}. {item['feature']}: "
                       f"{item['contribution']:+.4f} ({item['contribution_percent']:+.2f}%)")
        
        # Step 6: Generate report
        logger.info("\n[6/6] Generating ablation report...")
        results['summary']['total_features'] = len(self.default_weights)
        results['summary']['full_model_performance'] = results['full_model']['mean_score']
        results['summary']['best_single_feature'] = feature_ranking[0][0]
        results['summary']['worst_single_feature'] = feature_ranking[-1][0]
        
        logger.info("\n" + "=" * 80)
        logger.info("Feature Ablation Study Completed")
        logger.info(f"Most important feature: {results['summary']['best_single_feature']}")
        logger.info(f"Least important feature: {results['summary']['worst_single_feature']}")
        logger.info("=" * 80)
        
        self.results = results
        return results
    
    async def _evaluate_with_features(self, hyperedge_ids: List[str],
                                     enabled_features: List[str]) -> Dict[str, float]:
        """
        Evaluate hyperedges with specific features enabled.
        
        Args:
            hyperedge_ids: List of hyperedge IDs
            enabled_features: List of feature names to enable
            
        Returns:
            Dictionary mapping hyperedge IDs to quality scores
        """
        if not QUALITY_SCORER_AVAILABLE:
            logger.warning("QualityScorer not available, returning mock scores")
            return {he_id: 0.5 for he_id in hyperedge_ids}
        
        # Create feature weights with disabled features set to 0
        feature_weights = {}
        for feature_name in self.default_weights.keys():
            if feature_name in enabled_features:
                feature_weights[feature_name] = self.default_weights[feature_name]
            else:
                feature_weights[feature_name] = 0.0
        
        # Renormalize weights so they sum to 1
        total_weight = sum(feature_weights.values())
        if total_weight > 0:
            feature_weights = {k: v / total_weight for k, v in feature_weights.items()}
        
        # Create scorer with modified weights
        scorer_config = self.config.copy()
        scorer_config['feature_weights'] = feature_weights
        
        try:
            from ..quality import QualityScorer
            scorer = QualityScorer(self.graph_storage, scorer_config)
            
            # Compute scores for all hyperedges
            scores = {}
            for he_id in hyperedge_ids:
                try:
                    result = await scorer.compute_quality_score(he_id)
                    scores[he_id] = result['quality_score']
                except Exception as e:
                    logger.warning(f"Error scoring {he_id}: {e}")
                    scores[he_id] = 0.5  # Default score
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in feature evaluation: {e}")
            return {he_id: 0.5 for he_id in hyperedge_ids}
    
    async def _statistical_comparison(self, full_model_scores: Dict[str, float],
                                     ablated_models: Dict[str, Dict],
                                     ground_truth: Dict[str, float]) -> Dict[str, Any]:
        """
        Perform statistical comparison between full and ablated models.
        
        Args:
            full_model_scores: Scores from full model
            ablated_models: Scores from ablated models
            ground_truth: Ground truth scores
            
        Returns:
            Statistical test results
        """
        results = {}
        
        # Get common IDs
        common_ids = set(full_model_scores.keys()) & set(ground_truth.keys())
        
        if len(common_ids) < 2:
            logger.warning("Not enough common IDs for statistical tests")
            return results
        
        # Full model correlation with ground truth
        full_correlation = IntrinsicMetrics.quality_score_correlation(
            full_model_scores,
            ground_truth
        )
        results['full_model_correlation'] = full_correlation
        
        # Compare each ablated model
        for feature_name, ablated_data in ablated_models.items():
            ablated_scores = ablated_data['scores']
            
            # Correlation with ground truth
            ablated_correlation = IntrinsicMetrics.quality_score_correlation(
                ablated_scores,
                ground_truth
            )
            
            # Paired comparison
            full_values = [full_model_scores[id_] for id_ in common_ids]
            ablated_values = [ablated_scores[id_] for id_ in common_ids]
            
            t_test = StatisticalTests.paired_t_test(ablated_values, full_values)
            wilcoxon_test = StatisticalTests.wilcoxon_signed_rank_test(ablated_values, full_values)
            
            results[feature_name] = {
                'correlation': ablated_correlation,
                'correlation_drop': full_correlation['correlation'] - ablated_correlation['correlation'],
                't_test': t_test,
                'wilcoxon_test': wilcoxon_test
            }
        
        return results
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate markdown report of ablation results.
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Markdown formatted report string
        """
        if not self.results:
            return "No ablation results available. Run run_ablation_study() first."
        
        lines = []
        lines.append("# Feature Ablation Study Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        summary = self.results['summary']
        lines.append(f"- **Total Features Tested**: {summary['total_features']}")
        lines.append(f"- **Full Model Performance**: {summary['full_model_performance']:.4f}")
        lines.append(f"- **Most Important Feature**: {summary['best_single_feature']}")
        lines.append(f"- **Least Important Feature**: {summary['worst_single_feature']}")
        lines.append("")
        
        # Feature ranking table
        lines.append("## Feature Importance Ranking")
        lines.append("")
        lines.append("| Rank | Feature | Contribution | Contribution (%) |")
        lines.append("|------|---------|--------------|------------------|")
        
        for item in summary['feature_ranking']:
            lines.append(
                f"| {item['rank']} | {item['feature']} | "
                f"{item['contribution']:+.4f} | {item['contribution_percent']:+.2f}% |"
            )
        lines.append("")
        
        # Detailed results
        lines.append("## Detailed Results")
        lines.append("")
        
        full_mean = self.results['full_model']['mean_score']
        lines.append(f"### Full Model (All Features)")
        lines.append(f"- Mean Score: {full_mean:.4f}")
        lines.append(f"- Std Dev: {self.results['full_model']['std_score']:.4f}")
        lines.append("")
        
        for feature_name in self.default_weights.keys():
            ablated = self.results['ablated_models'][feature_name]
            contrib = self.results['feature_contributions'][feature_name]
            
            lines.append(f"### Without {feature_name}")
            lines.append(f"- Mean Score: {ablated['mean_score']:.4f}")
            lines.append(f"- Std Dev: {ablated['std_score']:.4f}")
            lines.append(f"- Contribution: {contrib['absolute_contribution']:+.4f} "
                        f"({contrib['relative_contribution_percent']:+.2f}%)")
            lines.append("")
        
        # Statistical tests
        if 'statistical_tests' in self.results and self.results['statistical_tests']:
            lines.append("## Statistical Significance")
            lines.append("")
            
            for feature_name, stats in self.results['statistical_tests'].items():
                if feature_name == 'full_model_correlation':
                    continue
                
                lines.append(f"### {feature_name}")
                if 't_test' in stats:
                    t_test = stats['t_test']
                    sig_marker = "✓" if t_test['significant'] else "✗"
                    lines.append(f"- t-test: p={t_test['p_value']:.4f} {sig_marker}")
                
                if 'wilcoxon_test' in stats:
                    w_test = stats['wilcoxon_test']
                    sig_marker = "✓" if w_test['significant'] else "✗"
                    lines.append(f"- Wilcoxon: p={w_test['p_value']:.4f} {sig_marker}")
                
                lines.append("")
        
        report = "\n".join(lines)
        
        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Saved feature ablation report to: {output_path}")
        
        return report


class ModuleAblationExperiment:
    """
    Module Ablation Experiment
    
    This class implements experiments to measure the contribution of entire modules
    by disabling them and comparing performance.
    
    Modules tested:
    - Quality Assessment: Hyperedge quality scoring
    - Dynamic Updates: Weight adjustment based on feedback
    - Entity Type Filtering: Pre-filtering by entity types
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize module ablation experiment.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results = {}
        
        logger.info("Initialized ModuleAblationExperiment")
    
    async def run_ablation_study(self, test_queries: List[str],
                                expected_answers: Optional[List[str]] = None,
                                dynhyperrag_instance=None) -> Dict[str, Any]:
        """
        Run complete module ablation study.
        
        This method tests the system with different module configurations:
        1. Full system (all modules enabled)
        2. Without quality assessment
        3. Without dynamic updates
        4. Without entity type filtering
        5. Minimal system (no modules)
        
        Args:
            test_queries: List of test queries
            expected_answers: Optional expected answers for evaluation
            dynhyperrag_instance: DynHyperRAG instance (if available)
            
        Returns:
            Dictionary containing ablation results
        """
        logger.info("=" * 80)
        logger.info("Starting Module Ablation Study")
        logger.info(f"Testing {len(test_queries)} queries")
        logger.info("=" * 80)
        
        results = {
            'configurations': {},
            'module_contributions': {},
            'statistical_tests': {},
            'summary': {}
        }
        
        # Define module configurations to test
        configurations = {
            'full_system': {
                'enable_quality_ranking': True,
                'enable_dynamic_updates': True,
                'enable_entity_filtering': True,
                'description': 'Full DynHyperRAG system'
            },
            'no_quality': {
                'enable_quality_ranking': False,
                'enable_dynamic_updates': True,
                'enable_entity_filtering': True,
                'description': 'Without quality assessment'
            },
            'no_dynamic': {
                'enable_quality_ranking': True,
                'enable_dynamic_updates': False,
                'enable_entity_filtering': True,
                'description': 'Without dynamic updates'
            },
            'no_filtering': {
                'enable_quality_ranking': True,
                'enable_dynamic_updates': True,
                'enable_entity_filtering': False,
                'description': 'Without entity type filtering'
            },
            'minimal': {
                'enable_quality_ranking': False,
                'enable_dynamic_updates': False,
                'enable_entity_filtering': False,
                'description': 'Minimal system (static HyperGraphRAG)'
            }
        }
        
        # Step 1: Test each configuration
        logger.info("\n[1/4] Testing different module configurations...")
        for config_name, config_settings in configurations.items():
            logger.info(f"  Testing: {config_settings['description']}")
            
            # Run queries with this configuration
            config_results = await self._evaluate_configuration(
                test_queries,
                config_settings,
                dynhyperrag_instance
            )
            
            results['configurations'][config_name] = {
                'settings': config_settings,
                'results': config_results,
                'mean_performance': self._compute_mean_performance(config_results)
            }
            
            logger.info(f"    Mean performance: {results['configurations'][config_name]['mean_performance']:.4f}")
        
        # Step 2: Calculate module contributions
        logger.info("\n[2/4] Calculating module contributions...")
        full_performance = results['configurations']['full_system']['mean_performance']
        
        # Quality assessment contribution
        no_quality_perf = results['configurations']['no_quality']['mean_performance']
        quality_contrib = full_performance - no_quality_perf
        results['module_contributions']['quality_assessment'] = {
            'absolute_contribution': quality_contrib,
            'relative_contribution_percent': (quality_contrib / full_performance * 100) if full_performance != 0 else 0
        }
        logger.info(f"  Quality Assessment: {quality_contrib:+.4f} "
                   f"({results['module_contributions']['quality_assessment']['relative_contribution_percent']:+.2f}%)")
        
        # Dynamic updates contribution
        no_dynamic_perf = results['configurations']['no_dynamic']['mean_performance']
        dynamic_contrib = full_performance - no_dynamic_perf
        results['module_contributions']['dynamic_updates'] = {
            'absolute_contribution': dynamic_contrib,
            'relative_contribution_percent': (dynamic_contrib / full_performance * 100) if full_performance != 0 else 0
        }
        logger.info(f"  Dynamic Updates: {dynamic_contrib:+.4f} "
                   f"({results['module_contributions']['dynamic_updates']['relative_contribution_percent']:+.2f}%)")
        
        # Entity filtering contribution
        no_filtering_perf = results['configurations']['no_filtering']['mean_performance']
        filtering_contrib = full_performance - no_filtering_perf
        results['module_contributions']['entity_filtering'] = {
            'absolute_contribution': filtering_contrib,
            'relative_contribution_percent': (filtering_contrib / full_performance * 100) if full_performance != 0 else 0
        }
        logger.info(f"  Entity Filtering: {filtering_contrib:+.4f} "
                   f"({results['module_contributions']['entity_filtering']['relative_contribution_percent']:+.2f}%)")
        
        # Step 3: Statistical significance testing
        if expected_answers:
            logger.info("\n[3/4] Performing statistical tests...")
            results['statistical_tests'] = await self._statistical_comparison(
                results['configurations'],
                expected_answers
            )
        else:
            logger.info("\n[3/4] Skipping statistical tests (no expected answers)")
        
        # Step 4: Generate summary
        logger.info("\n[4/4] Generating summary...")
        module_ranking = sorted(
            results['module_contributions'].items(),
            key=lambda x: x[1]['absolute_contribution'],
            reverse=True
        )
        
        results['summary'] = {
            'full_system_performance': full_performance,
            'minimal_system_performance': results['configurations']['minimal']['mean_performance'],
            'total_improvement': full_performance - results['configurations']['minimal']['mean_performance'],
            'module_ranking': [
                {
                    'rank': i + 1,
                    'module': module_name,
                    'contribution': contrib['absolute_contribution'],
                    'contribution_percent': contrib['relative_contribution_percent']
                }
                for i, (module_name, contrib) in enumerate(module_ranking)
            ]
        }
        
        logger.info("\n  Module importance ranking:")
        for item in results['summary']['module_ranking']:
            logger.info(f"    {item['rank']}. {item['module']}: "
                       f"{item['contribution']:+.4f} ({item['contribution_percent']:+.2f}%)")
        
        logger.info("\n" + "=" * 80)
        logger.info("Module Ablation Study Completed")
        logger.info(f"Full system vs Minimal: {results['summary']['total_improvement']:+.4f}")
        logger.info("=" * 80)
        
        self.results = results
        return results
    
    async def _evaluate_configuration(self, test_queries: List[str],
                                     config_settings: Dict[str, Any],
                                     dynhyperrag_instance=None) -> Dict[str, Any]:
        """
        Evaluate system with specific module configuration.
        
        Args:
            test_queries: List of test queries
            config_settings: Module configuration settings
            dynhyperrag_instance: DynHyperRAG instance
            
        Returns:
            Evaluation results
        """
        # This is a placeholder - in practice, you would:
        # 1. Configure the system with specified module settings
        # 2. Run queries
        # 3. Collect performance metrics
        
        logger.warning("_evaluate_configuration is a placeholder - requires full system integration")
        
        # Mock results for demonstration
        # In real implementation, this would call the actual system
        mock_scores = np.random.uniform(0.5, 0.9, len(test_queries))
        
        return {
            'query_scores': mock_scores.tolist(),
            'mean_score': float(np.mean(mock_scores)),
            'std_score': float(np.std(mock_scores)),
            'n_queries': len(test_queries)
        }
    
    def _compute_mean_performance(self, config_results: Dict[str, Any]) -> float:
        """Compute mean performance from configuration results."""
        return config_results.get('mean_score', 0.0)
    
    async def _statistical_comparison(self, configurations: Dict[str, Dict],
                                     expected_answers: List[str]) -> Dict[str, Any]:
        """
        Perform statistical comparison between configurations.
        
        Args:
            configurations: Results from different configurations
            expected_answers: Expected answers
            
        Returns:
            Statistical test results
        """
        results = {}
        
        full_scores = configurations['full_system']['results']['query_scores']
        
        for config_name, config_data in configurations.items():
            if config_name == 'full_system':
                continue
            
            ablated_scores = config_data['results']['query_scores']
            
            # Paired t-test
            t_test = StatisticalTests.paired_t_test(ablated_scores, full_scores)
            
            # Wilcoxon test
            wilcoxon_test = StatisticalTests.wilcoxon_signed_rank_test(ablated_scores, full_scores)
            
            # Effect size
            effect_size = StatisticalTests.effect_size_cohens_d(ablated_scores, full_scores)
            
            results[config_name] = {
                't_test': t_test,
                'wilcoxon_test': wilcoxon_test,
                'effect_size': effect_size
            }
        
        return results
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        Generate markdown report of module ablation results.
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Markdown formatted report string
        """
        if not self.results:
            return "No ablation results available. Run run_ablation_study() first."
        
        lines = []
        lines.append("# Module Ablation Study Report")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().isoformat()}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        summary = self.results['summary']
        lines.append(f"- **Full System Performance**: {summary['full_system_performance']:.4f}")
        lines.append(f"- **Minimal System Performance**: {summary['minimal_system_performance']:.4f}")
        lines.append(f"- **Total Improvement**: {summary['total_improvement']:+.4f}")
        lines.append("")
        
        # Module ranking
        lines.append("## Module Importance Ranking")
        lines.append("")
        lines.append("| Rank | Module | Contribution | Contribution (%) |")
        lines.append("|------|--------|--------------|------------------|")
        
        for item in summary['module_ranking']:
            lines.append(
                f"| {item['rank']} | {item['module']} | "
                f"{item['contribution']:+.4f} | {item['contribution_percent']:+.2f}% |"
            )
        lines.append("")
        
        # Configuration results
        lines.append("## Configuration Results")
        lines.append("")
        
        for config_name, config_data in self.results['configurations'].items():
            settings = config_data['settings']
            results_data = config_data['results']
            
            lines.append(f"### {settings['description']}")
            lines.append("")
            lines.append("**Settings:**")
            lines.append(f"- Quality Ranking: {'✓' if settings['enable_quality_ranking'] else '✗'}")
            lines.append(f"- Dynamic Updates: {'✓' if settings['enable_dynamic_updates'] else '✗'}")
            lines.append(f"- Entity Filtering: {'✓' if settings['enable_entity_filtering'] else '✗'}")
            lines.append("")
            lines.append("**Performance:**")
            lines.append(f"- Mean Score: {results_data['mean_score']:.4f}")
            lines.append(f"- Std Dev: {results_data['std_score']:.4f}")
            lines.append("")
        
        # Statistical tests
        if 'statistical_tests' in self.results and self.results['statistical_tests']:
            lines.append("## Statistical Significance")
            lines.append("")
            
            for config_name, stats in self.results['statistical_tests'].items():
                config_desc = self.results['configurations'][config_name]['settings']['description']
                lines.append(f"### {config_desc}")
                
                if 't_test' in stats:
                    t_test = stats['t_test']
                    sig_marker = "✓" if t_test['significant'] else "✗"
                    lines.append(f"- t-test: p={t_test['p_value']:.4f} {sig_marker}")
                
                if 'wilcoxon_test' in stats:
                    w_test = stats['wilcoxon_test']
                    sig_marker = "✓" if w_test['significant'] else "✗"
                    lines.append(f"- Wilcoxon: p={w_test['p_value']:.4f} {sig_marker}")
                
                if 'effect_size' in stats:
                    lines.append(f"- Effect Size (Cohen's d): {stats['effect_size']:.3f}")
                
                lines.append("")
        
        report = "\n".join(lines)
        
        # Save if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Saved module ablation report to: {output_path}")
        
        return report


class AblationStudyRunner:
    """
    Unified runner for all ablation studies.
    
    This class provides a convenient interface to run both feature and module
    ablation studies and generate comprehensive reports.
    """
    
    def __init__(self, graph_storage: Optional[BaseGraphStorage] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize ablation study runner.
        
        Args:
            graph_storage: Graph storage instance
            config: Configuration dictionary
        """
        self.graph_storage = graph_storage
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', 'outputs/ablation_studies'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized AblationStudyRunner with output dir: {self.output_dir}")
    
    async def run_all_ablation_studies(self, hyperedge_ids: List[str],
                                      test_queries: List[str],
                                      ground_truth: Optional[Dict[str, float]] = None,
                                      expected_answers: Optional[List[str]] = None,
                                      dynhyperrag_instance=None) -> Dict[str, Any]:
        """
        Run all ablation studies (feature and module).
        
        Args:
            hyperedge_ids: List of hyperedge IDs for feature ablation
            test_queries: List of test queries for module ablation
            ground_truth: Optional ground truth quality scores
            expected_answers: Optional expected answers
            dynhyperrag_instance: Optional DynHyperRAG instance
            
        Returns:
            Combined results from all ablation studies
        """
        logger.info("=" * 80)
        logger.info("Running Complete Ablation Study Suite")
        logger.info("=" * 80)
        
        results = {
            'feature_ablation': None,
            'module_ablation': None,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'n_hyperedges': len(hyperedge_ids),
                'n_queries': len(test_queries)
            }
        }
        
        # Run feature ablation
        if self.graph_storage and hyperedge_ids:
            logger.info("\n### Running Feature Ablation Study ###\n")
            feature_experiment = FeatureAblationExperiment(self.graph_storage, self.config)
            results['feature_ablation'] = await feature_experiment.run_ablation_study(
                hyperedge_ids,
                ground_truth,
                test_queries
            )
            
            # Generate and save feature ablation report
            feature_report_path = self.output_dir / "feature_ablation_report.md"
            feature_experiment.generate_report(feature_report_path)
        else:
            logger.warning("Skipping feature ablation (missing graph_storage or hyperedge_ids)")
        
        # Run module ablation
        if test_queries:
            logger.info("\n### Running Module Ablation Study ###\n")
            module_experiment = ModuleAblationExperiment(self.config)
            results['module_ablation'] = await module_experiment.run_ablation_study(
                test_queries,
                expected_answers,
                dynhyperrag_instance
            )
            
            # Generate and save module ablation report
            module_report_path = self.output_dir / "module_ablation_report.md"
            module_experiment.generate_report(module_report_path)
        else:
            logger.warning("Skipping module ablation (missing test_queries)")
        
        # Save combined results
        results_path = self.output_dir / "ablation_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"\nSaved combined results to: {results_path}")
        
        # Generate combined summary report
        summary_path = self.output_dir / "ablation_summary.md"
        self._generate_combined_summary(results, summary_path)
        
        logger.info("\n" + "=" * 80)
        logger.info("Complete Ablation Study Suite Finished")
        logger.info(f"Reports saved to: {self.output_dir}")
        logger.info("=" * 80)
        
        return results
    
    def _generate_combined_summary(self, results: Dict[str, Any], output_path: Path):
        """Generate combined summary of all ablation studies."""
        lines = []
        lines.append("# Complete Ablation Study Summary")
        lines.append("")
        lines.append(f"**Generated**: {results['metadata']['timestamp']}")
        lines.append(f"**Hyperedges Tested**: {results['metadata']['n_hyperedges']}")
        lines.append(f"**Queries Tested**: {results['metadata']['n_queries']}")
        lines.append("")
        
        # Feature ablation summary
        if results['feature_ablation']:
            lines.append("## Feature Ablation Results")
            lines.append("")
            feature_summary = results['feature_ablation']['summary']
            lines.append(f"- **Most Important Feature**: {feature_summary['best_single_feature']}")
            lines.append(f"- **Least Important Feature**: {feature_summary['worst_single_feature']}")
            lines.append("")
            
            lines.append("### Top 3 Features")
            for item in feature_summary['feature_ranking'][:3]:
                lines.append(f"{item['rank']}. **{item['feature']}**: "
                           f"{item['contribution']:+.4f} ({item['contribution_percent']:+.2f}%)")
            lines.append("")
        
        # Module ablation summary
        if results['module_ablation']:
            lines.append("## Module Ablation Results")
            lines.append("")
            module_summary = results['module_ablation']['summary']
            lines.append(f"- **Full System Performance**: {module_summary['full_system_performance']:.4f}")
            lines.append(f"- **Minimal System Performance**: {module_summary['minimal_system_performance']:.4f}")
            lines.append(f"- **Total Improvement**: {module_summary['total_improvement']:+.4f}")
            lines.append("")
            
            lines.append("### Module Contributions")
            for item in module_summary['module_ranking']:
                lines.append(f"{item['rank']}. **{item['module']}**: "
                           f"{item['contribution']:+.4f} ({item['contribution_percent']:+.2f}%)")
            lines.append("")
        
        # Key findings
        lines.append("## Key Findings")
        lines.append("")
        lines.append("### Feature-Level Insights")
        if results['feature_ablation']:
            feature_ranking = results['feature_ablation']['summary']['feature_ranking']
            top_feature = feature_ranking[0]
            lines.append(f"- The **{top_feature['feature']}** feature contributes most to quality assessment "
                        f"({top_feature['contribution_percent']:+.2f}%)")
        
        lines.append("")
        lines.append("### Module-Level Insights")
        if results['module_ablation']:
            module_ranking = results['module_ablation']['summary']['module_ranking']
            top_module = module_ranking[0]
            lines.append(f"- The **{top_module['module']}** module provides the largest performance gain "
                        f"({top_module['contribution_percent']:+.2f}%)")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("For detailed results, see:")
        lines.append("- [Feature Ablation Report](feature_ablation_report.md)")
        lines.append("- [Module Ablation Report](module_ablation_report.md)")
        
        summary = "\n".join(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Saved combined summary to: {output_path}")


# Convenience function for running ablation studies
async def run_ablation_studies(graph_storage: Optional[BaseGraphStorage] = None,
                              hyperedge_ids: Optional[List[str]] = None,
                              test_queries: Optional[List[str]] = None,
                              ground_truth: Optional[Dict[str, float]] = None,
                              expected_answers: Optional[List[str]] = None,
                              config: Optional[Dict[str, Any]] = None,
                              dynhyperrag_instance=None) -> Dict[str, Any]:
    """
    Convenience function to run all ablation studies.
    
    Args:
        graph_storage: Graph storage instance
        hyperedge_ids: List of hyperedge IDs
        test_queries: List of test queries
        ground_truth: Optional ground truth quality scores
        expected_answers: Optional expected answers
        config: Configuration dictionary
        dynhyperrag_instance: Optional DynHyperRAG instance
        
    Returns:
        Combined ablation study results
    """
    runner = AblationStudyRunner(graph_storage, config)
    
    results = await runner.run_all_ablation_studies(
        hyperedge_ids or [],
        test_queries or [],
        ground_truth,
        expected_answers,
        dynhyperrag_instance
    )
    
    return results


# Example usage
if __name__ == "__main__":
    # Example: Run feature ablation only
    async def example_feature_ablation():
        from ..kg import NetworkXStorage
        
        # Mock setup
        graph = NetworkXStorage()
        config = {
            'feature_weights': {
                'degree_centrality': 0.2,
                'betweenness': 0.15,
                'clustering': 0.15,
                'coherence': 0.3,
                'text_quality': 0.2
            }
        }
        
        # Mock hyperedge IDs
        hyperedge_ids = [f"hyperedge_{i}" for i in range(10)]
        
        # Run feature ablation
        experiment = FeatureAblationExperiment(graph, config)
        results = await experiment.run_ablation_study(hyperedge_ids)
        
        # Generate report
        report = experiment.generate_report()
        print(report)
    
    # Run example
    # asyncio.run(example_feature_ablation())
    
    print("Ablation study module loaded successfully")
