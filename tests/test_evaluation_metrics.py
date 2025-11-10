"""Tests for evaluation metrics."""

import pytest
import numpy as np
import time
from typing import Dict, List, Set
from unittest.mock import Mock, patch

from hypergraphrag.evaluation.metrics import IntrinsicMetrics, ExtrinsicMetrics, EfficiencyMetrics


class TestIntrinsicMetrics:
    """Test intrinsic quality metrics."""
    
    def test_precision_recall_f1_perfect_match(self):
        """Test precision/recall/F1 with perfect match."""
        predicted = {"h1", "h2", "h3"}
        ground_truth = {"h1", "h2", "h3"}
        
        result = IntrinsicMetrics.precision_recall_f1(predicted, ground_truth)
        
        assert result['precision'] == 1.0
        assert result['recall'] == 1.0
        assert result['f1'] == 1.0
        assert result['tp'] == 3
        assert result['fp'] == 0
        assert result['fn'] == 0
    
    def test_precision_recall_f1_partial_match(self):
        """Test precision/recall/F1 with partial match."""
        predicted = {"h1", "h2", "h4"}
        ground_truth = {"h1", "h2", "h3"}
        
        result = IntrinsicMetrics.precision_recall_f1(predicted, ground_truth)
        
        assert result['precision'] == 2/3  # 2 correct out of 3 predicted
        assert result['recall'] == 2/3     # 2 correct out of 3 ground truth
        assert result['f1'] == 2/3         # F1 = 2 * (2/3) * (2/3) / ((2/3) + (2/3))
        assert result['tp'] == 2
        assert result['fp'] == 1
        assert result['fn'] == 1
    
    def test_precision_recall_f1_empty_sets(self):
        """Test precision/recall/F1 with empty sets."""
        # Both empty
        result = IntrinsicMetrics.precision_recall_f1(set(), set())
        assert result['precision'] == 1.0
        assert result['recall'] == 1.0
        assert result['f1'] == 1.0
        
        # Empty predicted
        result = IntrinsicMetrics.precision_recall_f1(set(), {"h1"})
        assert result['precision'] == 0.0
        assert result['recall'] == 0.0
        assert result['f1'] == 0.0
        
        # Empty ground truth
        result = IntrinsicMetrics.precision_recall_f1({"h1"}, set())
        assert result['precision'] == 0.0
        assert result['recall'] == 0.0
        assert result['f1'] == 0.0
    
    def test_quality_score_correlation(self):
        """Test quality score correlation."""
        predicted_scores = {"h1": 0.9, "h2": 0.7, "h3": 0.5, "h4": 0.3}
        ground_truth_labels = {"h1": 1.0, "h2": 0.8, "h3": 0.4, "h4": 0.2}
        
        result = IntrinsicMetrics.quality_score_correlation(predicted_scores, ground_truth_labels)
        
        assert 'correlation' in result
        assert 'p_value' in result
        assert 'n_samples' in result
        assert result['n_samples'] == 4
        assert result['correlation'] > 0.8  # Should be high positive correlation
    
    def test_quality_score_correlation_insufficient_data(self):
        """Test correlation with insufficient data."""
        predicted_scores = {"h1": 0.9}
        ground_truth_labels = {"h1": 1.0}
        
        result = IntrinsicMetrics.quality_score_correlation(predicted_scores, ground_truth_labels)
        
        assert result['correlation'] == 0.0
        assert result['p_value'] == 1.0
        assert result['n_samples'] == 1
    
    def test_roc_auc(self):
        """Test ROC AUC calculation."""
        predicted_scores = {"h1": 0.9, "h2": 0.7, "h3": 0.3, "h4": 0.1}
        ground_truth_labels = {"h1": 1, "h2": 1, "h3": 0, "h4": 0}
        
        result = IntrinsicMetrics.roc_auc(predicted_scores, ground_truth_labels)
        
        assert 'auc_score' in result
        assert 'n_samples' in result
        assert result['n_samples'] == 4
        assert result['auc_score'] == 1.0  # Perfect separation
    
    def test_roc_auc_single_class(self):
        """Test ROC AUC with single class."""
        predicted_scores = {"h1": 0.9, "h2": 0.7}
        ground_truth_labels = {"h1": 1, "h2": 1}  # All positive
        
        result = IntrinsicMetrics.roc_auc(predicted_scores, ground_truth_labels)
        
        assert result['auc_score'] == 0.5  # Default for single class
        assert result['n_samples'] == 2
    
    def test_compute_all_intrinsic_metrics(self):
        """Test computing all intrinsic metrics together."""
        predicted_hyperedges = {"h1", "h2", "h3"}
        ground_truth_hyperedges = {"h1", "h2", "h4"}
        predicted_scores = {"h1": 0.9, "h2": 0.7, "h3": 0.5, "h4": 0.3}
        ground_truth_labels = {"h1": 1.0, "h2": 0.8, "h3": 0.4, "h4": 0.6}
        
        result = IntrinsicMetrics.compute_all_intrinsic_metrics(
            predicted_hyperedges, ground_truth_hyperedges,
            predicted_scores, ground_truth_labels
        )
        
        assert 'precision_recall_f1' in result
        assert 'quality_correlation' in result
        assert 'roc_auc' in result
        
        # Check precision/recall/F1
        prf = result['precision_recall_f1']
        assert prf['precision'] == 2/3  # h1, h2 correct out of h1, h2, h3
        assert prf['recall'] == 2/3     # h1, h2 correct out of h1, h2, h4


class TestExtrinsicMetrics:
    """Test extrinsic performance metrics."""
    
    def test_mean_reciprocal_rank(self):
        """Test MRR calculation."""
        results = [
            ["correct", "wrong1", "wrong2"],  # Rank 1
            ["wrong1", "correct", "wrong2"],  # Rank 2
            ["wrong1", "wrong2", "correct"]   # Rank 3
        ]
        ground_truth = ["correct", "correct", "correct"]
        
        mrr = ExtrinsicMetrics.mean_reciprocal_rank(results, ground_truth)
        
        expected_mrr = (1/1 + 1/2 + 1/3) / 3
        assert abs(mrr - expected_mrr) < 1e-6
    
    def test_mean_reciprocal_rank_no_match(self):
        """Test MRR with no matches."""
        results = [["wrong1", "wrong2"], ["wrong3", "wrong4"]]
        ground_truth = ["correct1", "correct2"]
        
        mrr = ExtrinsicMetrics.mean_reciprocal_rank(results, ground_truth)
        assert mrr == 0.0
    
    def test_precision_at_k(self):
        """Test Precision@K."""
        results = [
            ["correct1", "correct2", "wrong1"],
            ["wrong1", "correct3", "wrong2"]
        ]
        ground_truth = [
            {"correct1", "correct2"},
            {"correct3", "correct4"}
        ]
        
        precision_at_2 = ExtrinsicMetrics.precision_at_k(results, ground_truth, k=2)
        
        # Query 1: 2/2 correct in top 2
        # Query 2: 1/2 correct in top 2
        expected = (2/2 + 1/2) / 2
        assert abs(precision_at_2 - expected) < 1e-6
    
    def test_recall_at_k(self):
        """Test Recall@K."""
        results = [
            ["correct1", "correct2", "wrong1"],
            ["wrong1", "correct3", "wrong2"]
        ]
        ground_truth = [
            {"correct1", "correct2", "correct3"},  # 3 relevant
            {"correct3", "correct4"}               # 2 relevant
        ]
        
        recall_at_2 = ExtrinsicMetrics.recall_at_k(results, ground_truth, k=2)
        
        # Query 1: 2/3 relevant found in top 2
        # Query 2: 1/2 relevant found in top 2
        expected = (2/3 + 1/2) / 2
        assert abs(recall_at_2 - expected) < 1e-6
    
    def test_f1_at_k(self):
        """Test F1@K."""
        results = [["correct1", "wrong1"]]
        ground_truth = [{"correct1", "correct2"}]
        
        f1_at_2 = ExtrinsicMetrics.f1_at_k(results, ground_truth, k=2)
        
        # Precision@2 = 1/2, Recall@2 = 1/2
        # F1 = 2 * (1/2) * (1/2) / ((1/2) + (1/2)) = 1/2
        assert abs(f1_at_2 - 0.5) < 1e-6
    
    @patch('hypergraphrag.evaluation.metrics.sentence_bleu')
    @patch('hypergraphrag.evaluation.metrics.SmoothingFunction')
    def test_bleu_score(self, mock_smoothing, mock_bleu):
        """Test BLEU score calculation."""
        mock_smoothing.return_value.method1 = Mock()
        mock_bleu.return_value = 0.5
        
        predictions = ["This is a test", "Another test"]
        references = ["This is a test", "Another test"]
        
        with patch('hypergraphrag.evaluation.metrics.nltk'):
            score = ExtrinsicMetrics.bleu_score(predictions, references)
            assert score == 0.5
    
    def test_bleu_score_import_error(self):
        """Test BLEU score with import error."""
        with patch('hypergraphrag.evaluation.metrics.nltk', side_effect=ImportError):
            predictions = ["test"]
            references = ["test"]
            score = ExtrinsicMetrics.bleu_score(predictions, references)
            assert score == 0.0
    
    def test_hallucination_rate(self):
        """Test hallucination rate calculation."""
        answers = [
            "The law states that theft is illegal",  # "law", "states", "theft", "illegal"
            "Courts handle criminal cases"           # "courts", "handle", "criminal", "cases"
        ]
        contexts = [
            "Legal documents mention theft and illegal activities",  # "theft", "illegal"
            "Criminal justice system and courts"                     # "criminal", "courts"
        ]
        
        rate = ExtrinsicMetrics.hallucination_rate(answers, contexts)
        
        # Answer 1: "law", "states" not in context -> 2/4 = 0.5
        # Answer 2: "handle", "cases" not in context -> 2/4 = 0.5
        # Average: 0.5
        assert abs(rate - 0.5) < 0.1  # Allow some tolerance for word processing
    
    def test_reasoning_completeness(self):
        """Test reasoning completeness calculation."""
        answers = [
            "The defendant committed theft and was sentenced",
            "The court ruled on the case"
        ]
        expected_entities = [
            {"defendant", "theft", "sentenced"},
            {"court", "case"}
        ]
        
        completeness = ExtrinsicMetrics.reasoning_completeness(answers, expected_entities)
        
        # Answer 1: all 3 entities present -> 3/3 = 1.0
        # Answer 2: all 2 entities present -> 2/2 = 1.0
        # Average: 1.0
        assert completeness == 1.0
    
    def test_compute_all_extrinsic_metrics(self):
        """Test computing all extrinsic metrics together."""
        retrieval_results = [["h1", "h2"], ["h3", "h4"]]
        ground_truth_retrieval = [{"h1"}, {"h3"}]
        generated_answers = ["Answer 1", "Answer 2"]
        reference_answers = ["Reference 1", "Reference 2"]
        contexts = ["Context 1", "Context 2"]
        expected_entities = [{"entity1"}, {"entity2"}]
        
        with patch.object(ExtrinsicMetrics, 'bleu_score', return_value=0.5), \
             patch.object(ExtrinsicMetrics, 'rouge_score', return_value=0.6), \
             patch.object(ExtrinsicMetrics, 'bert_score', return_value={'f1': 0.7}):
            
            result = ExtrinsicMetrics.compute_all_extrinsic_metrics(
                retrieval_results, ground_truth_retrieval,
                generated_answers, reference_answers,
                contexts, expected_entities
            )
        
        assert 'mrr' in result
        assert 'precision_at_1' in result
        assert 'bleu' in result
        assert 'hallucination_rate' in result
        assert 'reasoning_completeness' in result


class TestEfficiencyMetrics:
    """Test efficiency metrics."""
    
    def test_measure_retrieval_time(self):
        """Test retrieval time measurement."""
        def mock_retrieval_func(query):
            time.sleep(0.01)  # Simulate 10ms retrieval
            return f"result for {query}"
        
        queries = ["query1", "query2", "query3"]
        
        result = EfficiencyMetrics.measure_retrieval_time(
            mock_retrieval_func, queries, warmup_runs=1
        )
        
        assert 'mean_time' in result
        assert 'std_time' in result
        assert 'median_time' in result
        assert 'p95_time' in result
        assert 'n_queries' in result
        
        assert result['n_queries'] == 3
        assert result['mean_time'] > 0.005  # Should be around 10ms
        assert result['mean_time'] < 0.1    # But not too high
    
    def test_measure_retrieval_time_with_failures(self):
        """Test retrieval time measurement with some failures."""
        def failing_retrieval_func(query):
            if "fail" in query:
                raise Exception("Retrieval failed")
            time.sleep(0.01)
            return f"result for {query}"
        
        queries = ["query1", "fail_query", "query3"]
        
        result = EfficiencyMetrics.measure_retrieval_time(
            failing_retrieval_func, queries, warmup_runs=0
        )
        
        assert result['n_queries'] == 2  # Only successful queries counted
        assert result['mean_time'] > 0
    
    def test_measure_retrieval_time_empty_queries(self):
        """Test retrieval time measurement with empty queries."""
        def mock_retrieval_func(query):
            return f"result for {query}"
        
        result = EfficiencyMetrics.measure_retrieval_time(mock_retrieval_func, [])
        
        assert result['mean_time'] == 0.0
        assert result['std_time'] == 0.0
        assert result['median_time'] == 0.0
        assert result['p95_time'] == 0.0
    
    @pytest.mark.asyncio
    async def test_measure_async_retrieval_time(self):
        """Test async retrieval time measurement."""
        async def mock_async_retrieval_func(query):
            await asyncio.sleep(0.01)  # Simulate 10ms async retrieval
            return f"result for {query}"
        
        import asyncio
        queries = ["query1", "query2"]
        
        result = await EfficiencyMetrics.measure_async_retrieval_time(
            mock_async_retrieval_func, queries, warmup_runs=1
        )
        
        assert 'mean_time' in result
        assert result['n_queries'] == 2
        assert result['mean_time'] > 0.005
    
    @patch('hypergraphrag.evaluation.metrics.psutil.Process')
    def test_measure_resource_usage(self, mock_process_class):
        """Test resource usage measurement."""
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 25.5
        mock_process.memory_info.return_value = Mock(rss=1024*1024*100)  # 100MB
        mock_process.memory_percent.return_value = 5.0
        mock_process.num_threads.return_value = 4
        mock_process.num_fds.return_value = 20
        mock_process_class.return_value = mock_process
        
        with patch('hypergraphrag.evaluation.metrics.psutil.cpu_percent', return_value=50.0), \
             patch('hypergraphrag.evaluation.metrics.psutil.virtual_memory') as mock_vm:
            
            mock_vm.return_value = Mock(
                total=8*1024*1024*1024,      # 8GB
                available=4*1024*1024*1024,  # 4GB
                percent=50.0
            )
            
            result = EfficiencyMetrics.measure_resource_usage()
        
        assert result['process_cpu_percent'] == 25.5
        assert result['process_memory_mb'] == 100.0
        assert result['process_memory_percent'] == 5.0
        assert result['process_num_threads'] == 4
        assert result['system_cpu_percent'] == 50.0
        assert result['system_memory_total_gb'] == 8.0
    
    @patch('hypergraphrag.evaluation.metrics.tiktoken.encoding_for_model')
    def test_measure_api_cost(self, mock_encoding_for_model):
        """Test API cost measurement."""
        mock_encoding = Mock()
        mock_encoding.encode.side_effect = [
            [1, 2, 3, 4, 5],      # 5 tokens
            [1, 2, 3],            # 3 tokens
            [1, 2, 3, 4, 5, 6, 7] # 7 tokens
        ]
        mock_encoding_for_model.return_value = mock_encoding
        
        texts = ["Short text", "Hi", "This is a longer text"]
        
        result = EfficiencyMetrics.measure_api_cost(texts, "gpt-3.5-turbo")
        
        assert result['total_tokens'] == 15  # 5 + 3 + 7
        assert result['mean_tokens_per_text'] == 5.0  # 15 / 3
        assert result['max_tokens_per_text'] == 7
        assert result['min_tokens_per_text'] == 3
        assert result['n_texts'] == 3
    
    def test_measure_api_cost_import_error(self):
        """Test API cost measurement with import error."""
        with patch('hypergraphrag.evaluation.metrics.tiktoken', side_effect=ImportError):
            texts = ["test"]
            result = EfficiencyMetrics.measure_api_cost(texts)
            
            assert result['total_tokens'] == 0
            assert result['n_texts'] == 1
    
    def test_measure_storage_requirements(self):
        """Test storage requirements measurement."""
        mock_graph_storage = Mock()
        mock_graph_storage.get_node_count.return_value = 1000
        mock_graph_storage.get_edge_count.return_value = 2000
        
        mock_vector_storage = Mock()
        mock_vector_storage.get_vector_count.return_value = 500
        
        result = EfficiencyMetrics.measure_storage_requirements(
            mock_graph_storage, mock_vector_storage
        )
        
        assert result['graph_nodes'] == 1000
        assert result['graph_edges'] == 2000
        assert result['graph_size_estimate_mb'] > 0
        assert result['vector_size_estimate_mb'] > 0
        assert result['total_size_estimate_mb'] > 0
    
    def test_compute_efficiency_improvement(self):
        """Test efficiency improvement calculation."""
        baseline_metrics = {
            'mean_time': 1.0,
            'memory_mb': 100.0,
            'accuracy': 0.8
        }
        improved_metrics = {
            'mean_time': 0.5,    # 50% improvement (time reduced)
            'memory_mb': 80.0,   # 20% improvement (memory reduced)
            'accuracy': 0.9      # 12.5% improvement (accuracy increased)
        }
        
        improvements = EfficiencyMetrics.compute_efficiency_improvement(
            baseline_metrics, improved_metrics
        )
        
        assert improvements['mean_time_improvement_percent'] == 50.0
        assert improvements['memory_mb_improvement_percent'] == 20.0
        assert improvements['accuracy_improvement_percent'] == 12.5
    
    def test_compute_all_efficiency_metrics(self):
        """Test computing all efficiency metrics together."""
        def mock_retrieval_func(query):
            time.sleep(0.001)
            return f"result for {query}"
        
        queries = ["query1", "query2"]
        texts_for_cost = ["text1", "text2"]
        mock_graph_storage = Mock()
        mock_graph_storage.get_node_count.return_value = 100
        mock_graph_storage.get_edge_count.return_value = 200
        
        with patch.object(EfficiencyMetrics, 'measure_resource_usage') as mock_resource, \
             patch.object(EfficiencyMetrics, 'measure_api_cost') as mock_cost:
            
            mock_resource.return_value = {'cpu_percent': 25.0}
            mock_cost.return_value = {'total_tokens': 100}
            
            result = EfficiencyMetrics.compute_all_efficiency_metrics(
                mock_retrieval_func, queries, texts_for_cost, mock_graph_storage
            )
        
        assert 'retrieval_time' in result
        assert 'resource_usage' in result
        assert 'api_cost' in result
        assert 'storage_requirements' in result


class TestStatisticalTests:
    """Test statistical significance testing."""
    
    def test_paired_t_test_significant_difference(self):
        """Test paired t-test with significant difference."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        # Group 2 is consistently higher than group 1
        group1 = [0.5, 0.6, 0.7, 0.8, 0.9]
        group2 = [0.7, 0.8, 0.9, 1.0, 1.1]
        
        result = StatisticalTests.paired_t_test(group1, group2)
        
        assert result['error'] is None
        assert result['n_samples'] == 5
        assert result['mean_diff'] == 0.2  # Consistent 0.2 difference
        assert result['p_value'] < 0.05    # Should be significant
        assert result['significant'] is True
        assert len(result['confidence_interval']) == 2
        assert result['statistic'] != 0.0
    
    def test_paired_t_test_no_difference(self):
        """Test paired t-test with no difference."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        # Identical groups
        group1 = [0.5, 0.6, 0.7, 0.8, 0.9]
        group2 = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        result = StatisticalTests.paired_t_test(group1, group2)
        
        assert result['error'] is None
        assert result['mean_diff'] == 0.0
        assert result['p_value'] > 0.05    # Should not be significant
        assert result['significant'] is False
    
    def test_paired_t_test_length_mismatch(self):
        """Test paired t-test with mismatched lengths."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        group1 = [0.5, 0.6, 0.7]
        group2 = [0.7, 0.8]  # Different length
        
        result = StatisticalTests.paired_t_test(group1, group2)
        
        assert result['error'] == 'Length mismatch'
        assert result['p_value'] == 1.0
        assert result['significant'] is False
    
    def test_paired_t_test_insufficient_samples(self):
        """Test paired t-test with insufficient samples."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        group1 = [0.5]
        group2 = [0.7]
        
        result = StatisticalTests.paired_t_test(group1, group2)
        
        assert result['error'] == 'Insufficient samples'
        assert result['n_samples'] == 1
        assert result['significant'] is False
    
    def test_wilcoxon_signed_rank_test_significant(self):
        """Test Wilcoxon signed-rank test with significant difference."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        # Non-normal distribution with clear difference
        group1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        group2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Consistently +2
        
        result = StatisticalTests.wilcoxon_signed_rank_test(group1, group2)
        
        assert result['error'] is None
        assert result['n_samples'] == 10
        assert result['median_diff'] == 2.0
        assert result['p_value'] < 0.05
        assert result['significant'] is True
    
    def test_wilcoxon_signed_rank_test_no_difference(self):
        """Test Wilcoxon signed-rank test with no difference."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        group1 = [1, 2, 3, 4, 5]
        group2 = [1, 2, 3, 4, 5]  # Identical
        
        result = StatisticalTests.wilcoxon_signed_rank_test(group1, group2)
        
        assert result['error'] == 'Too many zero differences'
        assert result['median_diff'] == 0.0
        assert result['significant'] is False
    
    def test_wilcoxon_signed_rank_test_insufficient_samples(self):
        """Test Wilcoxon signed-rank test with insufficient samples."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        group1 = [1, 2]
        group2 = [2, 3]
        
        result = StatisticalTests.wilcoxon_signed_rank_test(group1, group2)
        
        assert result['error'] == 'Insufficient samples'
        assert result['significant'] is False
    
    def test_compute_confidence_interval(self):
        """Test confidence interval computation."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        ci = StatisticalTests.compute_confidence_interval(data, confidence_level=0.95)
        
        assert len(ci) == 2
        assert ci[0] < ci[1]  # Lower bound < upper bound
        assert ci[0] < 3.0 < ci[1]  # Mean should be within CI
    
    def test_compute_confidence_interval_insufficient_data(self):
        """Test confidence interval with insufficient data."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        ci = StatisticalTests.compute_confidence_interval([1.0])
        assert ci == (0.0, 0.0)
        
        ci = StatisticalTests.compute_confidence_interval([])
        assert ci == (0.0, 0.0)
    
    def test_multiple_comparisons_correction_bonferroni(self):
        """Test Bonferroni correction."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        
        corrected = StatisticalTests.multiple_comparisons_correction(
            p_values, method='bonferroni'
        )
        
        assert len(corrected) == 5
        # Bonferroni: multiply by number of tests
        assert corrected[0] == 0.01 * 5  # 0.05
        assert corrected[1] == 0.02 * 5  # 0.10
        assert all(c <= 1.0 for c in corrected)  # Capped at 1.0
    
    def test_multiple_comparisons_correction_holm(self):
        """Test Holm correction."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        
        corrected = StatisticalTests.multiple_comparisons_correction(
            p_values, method='holm'
        )
        
        assert len(corrected) == 5
        assert all(c <= 1.0 for c in corrected)
        # Holm correction should be less conservative than Bonferroni
        bonferroni = StatisticalTests.multiple_comparisons_correction(
            p_values, method='bonferroni'
        )
        assert all(h <= b for h, b in zip(corrected, bonferroni))
    
    def test_effect_size_cohens_d(self):
        """Test Cohen's d effect size calculation."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        # Large effect size
        group1 = [1, 2, 3, 4, 5]
        group2 = [6, 7, 8, 9, 10]  # Mean difference = 5, pooled std ≈ 1.58
        
        cohens_d = StatisticalTests.effect_size_cohens_d(group1, group2)
        
        assert cohens_d > 2.0  # Large effect size (> 0.8)
    
    def test_effect_size_cohens_d_no_difference(self):
        """Test Cohen's d with no difference."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        group1 = [1, 2, 3, 4, 5]
        group2 = [1, 2, 3, 4, 5]
        
        cohens_d = StatisticalTests.effect_size_cohens_d(group1, group2)
        
        assert cohens_d == 0.0
    
    def test_effect_size_cohens_d_empty_groups(self):
        """Test Cohen's d with empty groups."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        cohens_d = StatisticalTests.effect_size_cohens_d([], [1, 2, 3])
        assert cohens_d == 0.0
        
        cohens_d = StatisticalTests.effect_size_cohens_d([1, 2, 3], [])
        assert cohens_d == 0.0
    
    def test_compare_methods(self):
        """Test comprehensive method comparison."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        baseline_results = {
            'accuracy': [0.7, 0.72, 0.68, 0.71, 0.69],
            'f1_score': [0.65, 0.67, 0.63, 0.66, 0.64]
        }
        improved_results = {
            'accuracy': [0.8, 0.82, 0.78, 0.81, 0.79],
            'f1_score': [0.75, 0.77, 0.73, 0.76, 0.74]
        }
        
        comparison = StatisticalTests.compare_methods(baseline_results, improved_results)
        
        assert 'accuracy' in comparison
        assert 'f1_score' in comparison
        
        # Check accuracy results
        acc_results = comparison['accuracy']
        assert 'baseline_mean' in acc_results
        assert 'improved_mean' in acc_results
        assert 't_test' in acc_results
        assert 'wilcoxon_test' in acc_results
        assert 'effect_size_cohens_d' in acc_results
        
        # Improved should have higher mean
        assert acc_results['improved_mean'] > acc_results['baseline_mean']
        
        # Should be significant (large consistent improvement)
        assert acc_results['t_test']['significant'] is True
        assert acc_results['wilcoxon_test']['significant'] is True
    
    def test_format_significance_stars(self):
        """Test significance star formatting."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        assert StatisticalTests.format_significance_stars(0.0005) == "***"
        assert StatisticalTests.format_significance_stars(0.005) == "**"
        assert StatisticalTests.format_significance_stars(0.03) == "*"
        assert StatisticalTests.format_significance_stars(0.1) == ""
    
    def test_generate_comparison_table_markdown(self):
        """Test Markdown table generation."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        comparison_results = {
            'accuracy': {
                'baseline_mean': 0.7,
                'improved_mean': 0.8,
                't_test': {'p_value': 0.01},
                'wilcoxon_test': {'p_value': 0.02},
                'effect_size_cohens_d': 1.5
            }
        }
        
        table = StatisticalTests.generate_comparison_table(
            comparison_results, format_type='markdown'
        )
        
        assert '| Metric |' in table
        assert '| accuracy |' in table
        assert '0.7000' in table  # Baseline mean
        assert '0.8000' in table  # Improved mean
        assert '+14.29%' in table  # Improvement percentage
        assert '**' in table      # Significance stars
    
    def test_generate_comparison_table_latex(self):
        """Test LaTeX table generation."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        comparison_results = {
            'test_metric': {
                'baseline_mean': 0.5,
                'improved_mean': 0.6,
                't_test': {'p_value': 0.001},
                'wilcoxon_test': {'p_value': 0.002},
                'effect_size_cohens_d': 0.8
            }
        }
        
        table = StatisticalTests.generate_comparison_table(
            comparison_results, format_type='latex'
        )
        
        assert '\\begin{table}' in table
        assert '\\end{table}' in table
        assert 'test\\_metric' in table  # Escaped underscore
        assert '***' in table            # Significance stars
        assert '\\\\' in table           # LaTeX line breaks
    
    def test_generate_comparison_table_empty(self):
        """Test table generation with empty results."""
        from hypergraphrag.evaluation.metrics import StatisticalTests
        
        table = StatisticalTests.generate_comparison_table({})
        assert "No comparison results available." in table


if __name__ == "__main__":
    pytest.main([__file__])