"""
Automated Experiment Pipeline for DynHyperRAG Evaluation

This module provides a comprehensive experiment pipeline that integrates:
- Data loading and preprocessing
- Hyperedge extraction and quality scoring
- Retrieval and answer generation
- Comprehensive evaluation metrics
- Baseline comparisons
- Statistical significance testing

The pipeline supports YAML configuration files for reproducible experiments.
"""

import asyncio
import json
import logging
import os
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from ..base import BaseGraphStorage, BaseVectorStorage, BaseKVStorage, QueryParam
from ..operate import extract_entities, kg_query
from .metrics import IntrinsicMetrics, ExtrinsicMetrics, EfficiencyMetrics
from .baselines import BaselineMethods, StaticHyperGraphRAG, BaselineComparator

logger = logging.getLogger(__name__)

# Optional import for QualityScorer (requires additional dependencies)
try:
    from ..quality import QualityScorer
    QUALITY_SCORER_AVAILABLE = True
except ImportError:
    QUALITY_SCORER_AVAILABLE = False
    logger.debug("QualityScorer not available - quality scoring will be skipped")


class ExperimentPipeline:
    """
    Automated experiment pipeline for DynHyperRAG evaluation.
    
    This class orchestrates the complete experimental workflow:
    1. Data loading and preprocessing
    2. Knowledge graph construction
    3. Quality assessment
    4. Retrieval and generation
    5. Evaluation against baselines
    6. Statistical analysis
    7. Results reporting
    
    Features:
    - YAML configuration support
    - Experiment metadata tracking
    - Reproducible random seeds
    - Comprehensive logging
    - Parallel experiment execution
    - Automatic result saving
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize experiment pipeline.
        
        Args:
            config: Configuration dictionary containing:
                - experiment_name: Name of the experiment
                - dataset: Dataset configuration
                - model: Model configuration
                - evaluation: Evaluation configuration
                - output_dir: Output directory for results
                - random_seed: Random seed for reproducibility
        """
        self.config = config
        self.experiment_name = config.get("experiment_name", "dynhyperrag_experiment")
        self.output_dir = Path(config.get("output_dir", "expr/experiments"))
        self.random_seed = config.get("random_seed", 42)
        
        # Set random seeds for reproducibility
        np.random.seed(self.random_seed)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Experiment metadata
        self.metadata = {
            "experiment_name": self.experiment_name,
            "start_time": None,
            "end_time": None,
            "duration_seconds": None,
            "config": config,
            "random_seed": self.random_seed,
            "git_commit": self._get_git_commit(),
        }
        
        # Results storage
        self.results = {
            "intrinsic_metrics": {},
            "extrinsic_metrics": {},
            "efficiency_metrics": {},
            "baseline_comparisons": {},
            "statistical_tests": {},
        }
        
        logger.info(f"Initialized ExperimentPipeline: {self.experiment_name}")
    
    def _get_git_commit(self) -> Optional[str]:
        """Get current git commit hash for reproducibility."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not get git commit: {e}")
        return None
    
    async def run_full_pipeline(self, dataset_name: str) -> Dict[str, Any]:
        """
        Run the complete experiment pipeline.
        
        This is the main entry point that orchestrates all experimental steps.
        
        Args:
            dataset_name: Name of the dataset to use (e.g., 'cail2019', 'pubmed')
            
        Returns:
            Dictionary containing all experimental results
        """
        self.metadata["start_time"] = datetime.now().isoformat()
        start_time = time.time()
        
        logger.info(f"=" * 80)
        logger.info(f"Starting Experiment: {self.experiment_name}")
        logger.info(f"Dataset: {dataset_name}")
        logger.info(f"=" * 80)
        
        try:
            # Step 1: Load data
            logger.info("\n[Step 1/9] Loading data...")
            data = await self.load_data(dataset_name)
            logger.info(f"✓ Loaded {len(data.get('documents', []))} documents, "
                       f"{len(data.get('queries', []))} queries")
            
            # Step 2: Extract hyperedges
            logger.info("\n[Step 2/9] Extracting hyperedges...")
            hyperedges = await self.extract_hyperedges(data)
            logger.info(f"✓ Extracted {len(hyperedges)} hyperedges")
            
            # Step 3: Compute quality scores
            logger.info("\n[Step 3/9] Computing quality scores...")
            quality_scores = await self.compute_quality_scores(hyperedges)
            logger.info(f"✓ Computed quality scores for {len(quality_scores)} hyperedges")
            
            # Step 4: Evaluate intrinsic quality
            if data.get("ground_truth_hyperedges"):
                logger.info("\n[Step 4/9] Evaluating intrinsic quality...")
                intrinsic_results = await self.evaluate_intrinsic_quality(
                    quality_scores,
                    data["ground_truth_hyperedges"]
                )
                self.results["intrinsic_metrics"] = intrinsic_results
                logger.info(f"✓ Intrinsic evaluation completed")
                self._log_intrinsic_results(intrinsic_results)
            else:
                logger.info("\n[Step 4/9] Skipping intrinsic evaluation (no ground truth)")
            
            # Step 5: Evaluate retrieval performance
            logger.info("\n[Step 5/9] Evaluating retrieval performance...")
            retrieval_results = await self.evaluate_retrieval(
                data["queries"],
                data.get("expected_answers", [])
            )
            self.results["extrinsic_metrics"] = retrieval_results
            logger.info(f"✓ Retrieval evaluation completed")
            self._log_retrieval_results(retrieval_results)
            
            # Step 6: Evaluate efficiency
            logger.info("\n[Step 6/9] Evaluating efficiency...")
            efficiency_results = await self.evaluate_efficiency(data["queries"])
            self.results["efficiency_metrics"] = efficiency_results
            logger.info(f"✓ Efficiency evaluation completed")
            self._log_efficiency_results(efficiency_results)
            
            # Step 7: Compare with baselines
            logger.info("\n[Step 7/9] Comparing with baselines...")
            baseline_results = await self.compare_baselines(
                hyperedges,
                data.get("ground_truth_hyperedges", {}),
                data["queries"],
                data.get("expected_answers", [])
            )
            self.results["baseline_comparisons"] = baseline_results
            logger.info(f"✓ Baseline comparison completed")
            self._log_baseline_results(baseline_results)
            
            # Step 8: Statistical significance testing
            logger.info("\n[Step 8/9] Performing statistical tests...")
            significance_results = await self.statistical_tests(
                retrieval_results,
                baseline_results
            )
            self.results["statistical_tests"] = significance_results
            logger.info(f"✓ Statistical tests completed")
            self._log_statistical_results(significance_results)
            
            # Step 9: Generate and save report
            logger.info("\n[Step 9/9] Generating experiment report...")
            report = self.generate_report(self.results)
            self.save_results(dataset_name, report)
            logger.info(f"✓ Report saved to {self.output_dir}")
            
            # Update metadata
            end_time = time.time()
            self.metadata["end_time"] = datetime.now().isoformat()
            self.metadata["duration_seconds"] = end_time - start_time
            
            logger.info(f"\n" + "=" * 80)
            logger.info(f"Experiment completed successfully!")
            logger.info(f"Total duration: {self.metadata['duration_seconds']:.2f} seconds")
            logger.info(f"Results saved to: {self.output_dir / f'{dataset_name}_results.json'}")
            logger.info(f"=" * 80)
            
            return report
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)
            self.metadata["error"] = str(e)
            self.metadata["end_time"] = datetime.now().isoformat()
            raise
    
    async def load_data(self, dataset_name: str) -> Dict[str, Any]:
        """
        Load and preprocess dataset.
        
        Args:
            dataset_name: Name of the dataset ('cail2019', 'pubmed', 'aminer')
            
        Returns:
            Dictionary containing:
                - documents: List of documents
                - queries: List of test queries
                - expected_answers: List of expected answers (optional)
                - ground_truth_hyperedges: Ground truth hyperedges (optional)
        """
        dataset_config = self.config.get("dataset", {})
        data_path = dataset_config.get("path", f"expr/{dataset_name}")
        
        logger.info(f"Loading dataset from: {data_path}")
        
        # Load based on dataset type
        if dataset_name.lower() == "cail2019":
            from ..data import CAIL2019Loader
            loader = CAIL2019Loader(data_path)
            data = loader.load_and_clean()
            
        elif dataset_name.lower() in ["pubmed", "aminer"]:
            from ..data import AcademicLoader
            loader = AcademicLoader(data_path, dataset_type=dataset_name.lower())
            data = loader.load_and_clean()
            
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        # Extract test split
        test_data = data.get("test", [])
        
        # Prepare documents and queries
        documents = []
        queries = []
        expected_answers = []
        
        for item in test_data:
            if "content" in item:
                documents.append(item["content"])
            if "query" in item:
                queries.append(item["query"])
            if "answer" in item:
                expected_answers.append(item["answer"])
        
        # Load ground truth if available
        ground_truth_file = Path(data_path) / "ground_truth_hyperedges.json"
        ground_truth_hyperedges = {}
        if ground_truth_file.exists():
            with open(ground_truth_file, 'r', encoding='utf-8') as f:
                ground_truth_hyperedges = json.load(f)
        
        return {
            "documents": documents,
            "queries": queries,
            "expected_answers": expected_answers,
            "ground_truth_hyperedges": ground_truth_hyperedges,
            "metadata": data.get("metadata", {}),
        }
    
    async def extract_hyperedges(self, data: Dict[str, Any]) -> List[str]:
        """
        Extract hyperedges from documents using existing extract_entities function.
        
        Args:
            data: Data dictionary containing documents
            
        Returns:
            List of hyperedge IDs
        """
        # This is a placeholder - in practice, you would:
        # 1. Initialize storage instances
        # 2. Process documents into chunks
        # 3. Call extract_entities from operate.py
        # 4. Return list of extracted hyperedge IDs
        
        # For now, return empty list as this requires full system setup
        logger.warning("extract_hyperedges is a placeholder - requires full system initialization")
        return []
    
    async def compute_quality_scores(self, hyperedges: List[str]) -> Dict[str, float]:
        """
        Compute quality scores for hyperedges.
        
        Args:
            hyperedges: List of hyperedge IDs
            
        Returns:
            Dictionary mapping hyperedge IDs to quality scores
        """
        # This is a placeholder - in practice, you would:
        # 1. Initialize QualityScorer
        # 2. Compute scores for all hyperedges
        # 3. Return score dictionary
        
        logger.warning("compute_quality_scores is a placeholder - requires QualityScorer initialization")
        return {}
    
    async def evaluate_intrinsic_quality(
        self,
        predicted_scores: Dict[str, float],
        ground_truth: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluate intrinsic quality metrics.
        
        Args:
            predicted_scores: Predicted quality scores
            ground_truth: Ground truth quality labels
            
        Returns:
            Dictionary of intrinsic metrics
        """
        # Precision, Recall, F1
        predicted_set = set(predicted_scores.keys())
        ground_truth_set = set(ground_truth.keys())
        
        prf_metrics = IntrinsicMetrics.precision_recall_f1(
            predicted_set,
            ground_truth_set
        )
        
        # Quality score correlation
        correlation_metrics = IntrinsicMetrics.quality_score_correlation(
            predicted_scores,
            ground_truth
        )
        
        # ROC AUC
        binary_labels = {k: 1 if v > 0.5 else 0 for k, v in ground_truth.items()}
        roc_metrics = IntrinsicMetrics.roc_auc(
            predicted_scores,
            binary_labels
        )
        
        return {
            "precision_recall_f1": prf_metrics,
            "quality_correlation": correlation_metrics,
            "roc_auc": roc_metrics,
        }
    
    async def evaluate_retrieval(
        self,
        queries: List[str],
        expected_answers: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval performance using existing kg_query function.
        
        Args:
            queries: List of test queries
            expected_answers: List of expected answers
            
        Returns:
            Dictionary of extrinsic metrics
        """
        # This is a placeholder - in practice, you would:
        # 1. Initialize storage instances
        # 2. Call kg_query for each query
        # 3. Collect retrieval results and generated answers
        # 4. Compute extrinsic metrics
        
        logger.warning("evaluate_retrieval is a placeholder - requires full system initialization")
        return {}
    
    async def evaluate_efficiency(self, queries: List[str]) -> Dict[str, Any]:
        """
        Evaluate efficiency metrics.
        
        Args:
            queries: List of test queries
            
        Returns:
            Dictionary of efficiency metrics
        """
        # This is a placeholder - in practice, you would:
        # 1. Measure retrieval time
        # 2. Measure resource usage
        # 3. Measure API costs
        # 4. Measure storage requirements
        
        logger.warning("evaluate_efficiency is a placeholder - requires full system initialization")
        return {}
    
    async def compare_baselines(
        self,
        hyperedges: List[str],
        ground_truth: Dict[str, float],
        queries: List[str],
        expected_answers: List[str]
    ) -> Dict[str, Any]:
        """
        Compare with baseline methods.
        
        Args:
            hyperedges: List of hyperedge IDs
            ground_truth: Ground truth quality labels
            queries: Test queries
            expected_answers: Expected answers
            
        Returns:
            Dictionary of baseline comparison results
        """
        # This is a placeholder - in practice, you would:
        # 1. Initialize BaselineMethods
        # 2. Compute baseline scores
        # 3. Compare with DynHyperRAG
        # 4. Return comparison results
        
        logger.warning("compare_baselines is a placeholder - requires baseline initialization")
        return {}
    
    async def statistical_tests(
        self,
        dynhyperrag_results: Dict[str, Any],
        baseline_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform statistical significance tests.
        
        Args:
            dynhyperrag_results: DynHyperRAG results
            baseline_results: Baseline results
            
        Returns:
            Dictionary of statistical test results
        """
        from scipy.stats import ttest_rel, wilcoxon
        
        results = {}
        
        # Compare key metrics
        metrics_to_compare = ["mrr", "precision_at_5", "recall_at_5", "f1_at_5"]
        
        for metric in metrics_to_compare:
            if metric in dynhyperrag_results and metric in baseline_results:
                dyn_values = dynhyperrag_results[metric]
                base_values = baseline_results[metric]
                
                # Ensure we have arrays
                if not isinstance(dyn_values, (list, np.ndarray)):
                    dyn_values = [dyn_values]
                if not isinstance(base_values, (list, np.ndarray)):
                    base_values = [base_values]
                
                # Paired t-test
                try:
                    t_stat, t_pval = ttest_rel(dyn_values, base_values)
                    results[f"{metric}_ttest"] = {
                        "t_statistic": float(t_stat),
                        "p_value": float(t_pval),
                        "significant": t_pval < 0.05
                    }
                except Exception as e:
                    logger.warning(f"T-test failed for {metric}: {e}")
                
                # Wilcoxon signed-rank test
                try:
                    w_stat, w_pval = wilcoxon(dyn_values, base_values)
                    results[f"{metric}_wilcoxon"] = {
                        "w_statistic": float(w_stat),
                        "p_value": float(w_pval),
                        "significant": w_pval < 0.05
                    }
                except Exception as e:
                    logger.warning(f"Wilcoxon test failed for {metric}: {e}")
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive experiment report.
        
        Args:
            results: All experimental results
            
        Returns:
            Complete report dictionary
        """
        report = {
            "metadata": self.metadata,
            "results": results,
            "summary": self._generate_summary(results),
        }
        
        return report
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from results."""
        summary = {
            "intrinsic_quality": {},
            "retrieval_performance": {},
            "efficiency": {},
            "baseline_comparison": {},
        }
        
        # Summarize intrinsic metrics
        if "intrinsic_metrics" in results:
            intrinsic = results["intrinsic_metrics"]
            if "precision_recall_f1" in intrinsic:
                summary["intrinsic_quality"]["f1_score"] = intrinsic["precision_recall_f1"].get("f1", 0.0)
            if "quality_correlation" in intrinsic:
                summary["intrinsic_quality"]["correlation"] = intrinsic["quality_correlation"].get("correlation", 0.0)
        
        # Summarize retrieval metrics
        if "extrinsic_metrics" in results:
            extrinsic = results["extrinsic_metrics"]
            summary["retrieval_performance"] = {
                "mrr": extrinsic.get("mrr", 0.0),
                "precision_at_5": extrinsic.get("precision_at_5", 0.0),
                "recall_at_5": extrinsic.get("recall_at_5", 0.0),
            }
        
        # Summarize efficiency
        if "efficiency_metrics" in results:
            efficiency = results["efficiency_metrics"]
            summary["efficiency"] = {
                "mean_retrieval_time": efficiency.get("mean_time", 0.0),
                "memory_usage_mb": efficiency.get("process_memory_mb", 0.0),
            }
        
        return summary
    
    def save_results(self, dataset_name: str, report: Dict[str, Any]):
        """
        Save experimental results to files.
        
        Args:
            dataset_name: Name of the dataset
            report: Complete experiment report
        """
        # Save JSON report
        json_path = self.output_dir / f"{dataset_name}_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved JSON report to: {json_path}")
        
        # Save markdown summary
        md_path = self.output_dir / f"{dataset_name}_summary.md"
        self._save_markdown_summary(md_path, report)
        logger.info(f"Saved markdown summary to: {md_path}")
    
    def _save_markdown_summary(self, path: Path, report: Dict[str, Any]):
        """Save a markdown summary of the results."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# Experiment Report: {self.experiment_name}\n\n")
            
            # Metadata
            f.write("## Metadata\n\n")
            metadata = report["metadata"]
            f.write(f"- **Experiment Name**: {metadata['experiment_name']}\n")
            f.write(f"- **Start Time**: {metadata['start_time']}\n")
            f.write(f"- **Duration**: {metadata.get('duration_seconds', 0):.2f} seconds\n")
            f.write(f"- **Random Seed**: {metadata['random_seed']}\n")
            if metadata.get('git_commit'):
                f.write(f"- **Git Commit**: {metadata['git_commit']}\n")
            f.write("\n")
            
            # Summary
            f.write("## Summary\n\n")
            summary = report.get("summary", {})
            
            if "intrinsic_quality" in summary:
                f.write("### Intrinsic Quality\n\n")
                for key, value in summary["intrinsic_quality"].items():
                    f.write(f"- **{key}**: {value:.4f}\n")
                f.write("\n")
            
            if "retrieval_performance" in summary:
                f.write("### Retrieval Performance\n\n")
                for key, value in summary["retrieval_performance"].items():
                    f.write(f"- **{key}**: {value:.4f}\n")
                f.write("\n")
            
            if "efficiency" in summary:
                f.write("### Efficiency\n\n")
                for key, value in summary["efficiency"].items():
                    f.write(f"- **{key}**: {value:.4f}\n")
                f.write("\n")
    
    def _log_intrinsic_results(self, results: Dict[str, Any]):
        """Log intrinsic evaluation results."""
        if "precision_recall_f1" in results:
            prf = results["precision_recall_f1"]
            logger.info(f"  Precision: {prf.get('precision', 0):.4f}")
            logger.info(f"  Recall: {prf.get('recall', 0):.4f}")
            logger.info(f"  F1: {prf.get('f1', 0):.4f}")
        
        if "quality_correlation" in results:
            corr = results["quality_correlation"]
            logger.info(f"  Correlation: {corr.get('correlation', 0):.4f} (p={corr.get('p_value', 1):.4f})")
    
    def _log_retrieval_results(self, results: Dict[str, Any]):
        """Log retrieval evaluation results."""
        logger.info(f"  MRR: {results.get('mrr', 0):.4f}")
        logger.info(f"  Precision@5: {results.get('precision_at_5', 0):.4f}")
        logger.info(f"  Recall@5: {results.get('recall_at_5', 0):.4f}")
    
    def _log_efficiency_results(self, results: Dict[str, Any]):
        """Log efficiency evaluation results."""
        logger.info(f"  Mean Time: {results.get('mean_time', 0):.4f}s")
        logger.info(f"  Memory: {results.get('process_memory_mb', 0):.2f} MB")
    
    def _log_baseline_results(self, results: Dict[str, Any]):
        """Log baseline comparison results."""
        for baseline_name, metrics in results.items():
            logger.info(f"  {baseline_name}: {metrics}")
    
    def _log_statistical_results(self, results: Dict[str, Any]):
        """Log statistical test results."""
        for test_name, test_results in results.items():
            if test_results.get("significant"):
                logger.info(f"  {test_name}: p={test_results.get('p_value', 1):.4f} ✓ Significant")
            else:
                logger.info(f"  {test_name}: p={test_results.get('p_value', 1):.4f}")


def load_experiment_config(config_path: str) -> Dict[str, Any]:
    """
    Load experiment configuration from YAML file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


async def run_experiment_from_config(config_path: str, dataset_name: str) -> Dict[str, Any]:
    """
    Run experiment from YAML configuration file.
    
    Args:
        config_path: Path to YAML configuration file
        dataset_name: Name of the dataset to use
        
    Returns:
        Experiment results
    """
    config = load_experiment_config(config_path)
    pipeline = ExperimentPipeline(config)
    results = await pipeline.run_full_pipeline(dataset_name)
    return results


# Example usage
if __name__ == "__main__":
    # Example configuration
    example_config = {
        "experiment_name": "dynhyperrag_cail2019_test",
        "dataset": {
            "name": "cail2019",
            "path": "expr/cail2019",
        },
        "model": {
            "llm_model": "gpt-4o-mini",
            "embedding_model": "text-embedding-3-small",
        },
        "evaluation": {
            "metrics": ["mrr", "precision_at_k", "recall_at_k", "f1"],
            "k_values": [1, 3, 5, 10],
        },
        "output_dir": "expr/experiments",
        "random_seed": 42,
    }
    
    # Run experiment
    pipeline = ExperimentPipeline(example_config)
    
    # Note: This would require full system initialization
    # asyncio.run(pipeline.run_full_pipeline("cail2019"))
    
    print("ExperimentPipeline initialized successfully")
    print(f"Output directory: {pipeline.output_dir}")
    print(f"Random seed: {pipeline.random_seed}")
