"""Evaluation metrics for DynHyperRAG."""

import numpy as np
import time
import psutil
from typing import Dict, List, Set, Union, Optional, Tuple
from scipy.stats import spearmanr, ttest_rel, wilcoxon
try:
    from sklearn.metrics import roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    roc_auc_score = None
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None
import asyncio
import logging

logger = logging.getLogger(__name__)


class IntrinsicMetrics:
    """内在质量指标 - 评估超边抽取质量"""
    
    @staticmethod
    def precision_recall_f1(predicted: Set[str], ground_truth: Set[str]) -> Dict[str, float]:
        """
        计算精确率、召回率、F1分数
        
        Args:
            predicted: 预测的超边ID集合
            ground_truth: 真实的超边ID集合
            
        Returns:
            包含precision, recall, f1的字典
        """
        if not predicted and not ground_truth:
            return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0}
        
        if not predicted:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        if not ground_truth:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        tp = len(predicted & ground_truth)
        fp = len(predicted - ground_truth)
        fn = len(ground_truth - predicted)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }
    
    @staticmethod
    def quality_score_correlation(predicted_scores: Dict[str, float], 
                                ground_truth_labels: Dict[str, float]) -> Dict[str, float]:
        """
        计算质量分数与真实标签的相关性
        
        Args:
            predicted_scores: 预测的质量分数 {hyperedge_id: score}
            ground_truth_labels: 真实标签 {hyperedge_id: label}
            
        Returns:
            包含correlation和p_value的字典
        """
        # 获取共同的ID
        common_ids = set(predicted_scores.keys()) & set(ground_truth_labels.keys())
        
        if len(common_ids) < 2:
            logger.warning(f"Not enough common IDs for correlation: {len(common_ids)}")
            return {'correlation': 0.0, 'p_value': 1.0, 'n_samples': len(common_ids)}
        
        # 提取对应的分数和标签
        pred_values = [predicted_scores[id_] for id_ in common_ids]
        true_values = [ground_truth_labels[id_] for id_ in common_ids]
        
        try:
            correlation, p_value = spearmanr(pred_values, true_values)
            # 处理NaN值
            if np.isnan(correlation):
                correlation = 0.0
            if np.isnan(p_value):
                p_value = 1.0
        except Exception as e:
            logger.error(f"Error computing correlation: {e}")
            correlation, p_value = 0.0, 1.0
        
        return {
            'correlation': correlation,
            'p_value': p_value,
            'n_samples': len(common_ids)
        }
    
    @staticmethod
    def roc_auc(predicted_scores: Dict[str, float], 
                ground_truth_labels: Dict[str, Union[int, float]]) -> Dict[str, float]:
        """
        计算ROC AUC分数
        
        Args:
            predicted_scores: 预测的质量分数 {hyperedge_id: score}
            ground_truth_labels: 二元标签 {hyperedge_id: 0/1}
            
        Returns:
            包含auc_score的字典
        """
        # 获取共同的ID
        common_ids = set(predicted_scores.keys()) & set(ground_truth_labels.keys())
        
        if len(common_ids) < 2:
            logger.warning(f"Not enough common IDs for ROC AUC: {len(common_ids)}")
            return {'auc_score': 0.5, 'n_samples': len(common_ids)}
        
        # 提取对应的分数和标签
        y_score = [predicted_scores[id_] for id_ in common_ids]
        y_true = [int(ground_truth_labels[id_]) for id_ in common_ids]
        
        # 检查是否有两个类别
        unique_labels = set(y_true)
        if len(unique_labels) < 2:
            logger.warning(f"Only one class present in labels: {unique_labels}")
            return {'auc_score': 0.5, 'n_samples': len(common_ids)}
        
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("sklearn not available, returning default ROC AUC")
                auc_score = 0.5
            else:
                auc_score = roc_auc_score(y_true, y_score)
        except Exception as e:
            logger.error(f"Error computing ROC AUC: {e}")
            auc_score = 0.5
        
        return {
            'auc_score': auc_score,
            'n_samples': len(common_ids)
        }
    
    @staticmethod
    def compute_all_intrinsic_metrics(predicted_hyperedges: Set[str],
                                    ground_truth_hyperedges: Set[str],
                                    predicted_scores: Dict[str, float],
                                    ground_truth_labels: Dict[str, float]) -> Dict[str, Dict]:
        """
        计算所有内在质量指标
        
        Args:
            predicted_hyperedges: 预测的超边集合
            ground_truth_hyperedges: 真实的超边集合
            predicted_scores: 预测的质量分数
            ground_truth_labels: 真实标签
            
        Returns:
            包含所有指标的字典
        """
        results = {}
        
        # 精确率、召回率、F1
        results['precision_recall_f1'] = IntrinsicMetrics.precision_recall_f1(
            predicted_hyperedges, ground_truth_hyperedges
        )
        
        # 质量分数相关性
        results['quality_correlation'] = IntrinsicMetrics.quality_score_correlation(
            predicted_scores, ground_truth_labels
        )
        
        # ROC AUC（需要将连续标签转换为二元标签）
        binary_labels = {k: 1 if v > 0.5 else 0 for k, v in ground_truth_labels.items()}
        results['roc_auc'] = IntrinsicMetrics.roc_auc(
            predicted_scores, binary_labels
        )
        
        return results


class ExtrinsicMetrics:
    """外在性能指标 - 评估端到端检索性能"""
    
    @staticmethod
    def mean_reciprocal_rank(results: List[List[str]], ground_truth: List[str]) -> float:
        """
        计算平均倒数排名 (MRR)
        
        Args:
            results: 每个查询的检索结果列表 [[result1, result2, ...], ...]
            ground_truth: 每个查询的正确答案 [answer1, answer2, ...]
            
        Returns:
            MRR分数
        """
        if not results or not ground_truth or len(results) != len(ground_truth):
            return 0.0
        
        mrr = 0.0
        for result_list, truth in zip(results, ground_truth):
            for i, item in enumerate(result_list):
                if item == truth:
                    mrr += 1.0 / (i + 1)
                    break
        
        return mrr / len(results)
    
    @staticmethod
    def precision_at_k(results: List[List[str]], ground_truth: List[Set[str]], k: int) -> float:
        """
        计算Precision@K
        
        Args:
            results: 每个查询的检索结果列表
            ground_truth: 每个查询的正确答案集合
            k: 截断位置
            
        Returns:
            Precision@K分数
        """
        if not results or not ground_truth or len(results) != len(ground_truth):
            return 0.0
        
        precisions = []
        for result_list, truth_set in zip(results, ground_truth):
            top_k = set(result_list[:k])
            if k > 0:
                precision = len(top_k & truth_set) / k
            else:
                precision = 0.0
            precisions.append(precision)
        
        return np.mean(precisions) if precisions else 0.0
    
    @staticmethod
    def recall_at_k(results: List[List[str]], ground_truth: List[Set[str]], k: int) -> float:
        """
        计算Recall@K
        
        Args:
            results: 每个查询的检索结果列表
            ground_truth: 每个查询的正确答案集合
            k: 截断位置
            
        Returns:
            Recall@K分数
        """
        if not results or not ground_truth or len(results) != len(ground_truth):
            return 0.0
        
        recalls = []
        for result_list, truth_set in zip(results, ground_truth):
            top_k = set(result_list[:k])
            if len(truth_set) > 0:
                recall = len(top_k & truth_set) / len(truth_set)
            else:
                recall = 0.0
            recalls.append(recall)
        
        return np.mean(recalls) if recalls else 0.0
    
    @staticmethod
    def f1_at_k(results: List[List[str]], ground_truth: List[Set[str]], k: int) -> float:
        """
        计算F1@K
        
        Args:
            results: 每个查询的检索结果列表
            ground_truth: 每个查询的正确答案集合
            k: 截断位置
            
        Returns:
            F1@K分数
        """
        precision = ExtrinsicMetrics.precision_at_k(results, ground_truth, k)
        recall = ExtrinsicMetrics.recall_at_k(results, ground_truth, k)
        
        if precision + recall > 0:
            return 2 * precision * recall / (precision + recall)
        else:
            return 0.0
    
    @staticmethod
    def bleu_score(predictions: List[str], references: List[str]) -> float:
        """
        计算BLEU分数
        
        Args:
            predictions: 预测的答案列表
            references: 参考答案列表
            
        Returns:
            BLEU分数
        """
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            import nltk
            
            # 确保下载必要的数据
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            if len(predictions) != len(references):
                logger.warning(f"Length mismatch: predictions={len(predictions)}, references={len(references)}")
                return 0.0
            
            smoothing = SmoothingFunction().method1
            scores = []
            
            for pred, ref in zip(predictions, references):
                # 分词
                pred_tokens = pred.split()
                ref_tokens = [ref.split()]  # BLEU需要参考答案列表
                
                if not pred_tokens or not ref_tokens[0]:
                    scores.append(0.0)
                    continue
                
                try:
                    score = sentence_bleu(ref_tokens, pred_tokens, smoothing_function=smoothing)
                    scores.append(score)
                except Exception as e:
                    logger.warning(f"Error computing BLEU for pair: {e}")
                    scores.append(0.0)
            
            return np.mean(scores) if scores else 0.0
            
        except ImportError:
            logger.warning("NLTK not available, returning 0.0 for BLEU score")
            return 0.0
    
    @staticmethod
    def rouge_score(predictions: List[str], references: List[str], rouge_type: str = 'rouge-l') -> float:
        """
        计算ROUGE分数
        
        Args:
            predictions: 预测的答案列表
            references: 参考答案列表
            rouge_type: ROUGE类型 ('rouge-1', 'rouge-2', 'rouge-l')
            
        Returns:
            ROUGE分数
        """
        try:
            from rouge_score import rouge_scorer
            
            if len(predictions) != len(references):
                logger.warning(f"Length mismatch: predictions={len(predictions)}, references={len(references)}")
                return 0.0
            
            scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=True)
            scores = []
            
            for pred, ref in zip(predictions, references):
                try:
                    score = scorer.score(ref, pred)
                    scores.append(score[rouge_type].fmeasure)
                except Exception as e:
                    logger.warning(f"Error computing ROUGE for pair: {e}")
                    scores.append(0.0)
            
            return np.mean(scores) if scores else 0.0
            
        except ImportError:
            logger.warning("rouge-score not available, returning 0.0 for ROUGE score")
            return 0.0
    
    @staticmethod
    def bert_score(predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        计算BERTScore
        
        Args:
            predictions: 预测的答案列表
            references: 参考答案列表
            
        Returns:
            包含precision, recall, f1的字典
        """
        try:
            from bert_score import score
            
            if len(predictions) != len(references):
                logger.warning(f"Length mismatch: predictions={len(predictions)}, references={len(references)}")
                return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
            
            if not predictions or not references:
                return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
            
            P, R, F1 = score(predictions, references, lang='zh', verbose=False)
            
            return {
                'precision': P.mean().item(),
                'recall': R.mean().item(),
                'f1': F1.mean().item()
            }
            
        except ImportError:
            logger.warning("bert-score not available, returning 0.0 for BERTScore")
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        except Exception as e:
            logger.error(f"Error computing BERTScore: {e}")
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
    
    @staticmethod
    def hallucination_rate(answers: List[str], contexts: List[str]) -> float:
        """
        计算幻觉率 - 检测答案中未在上下文出现的关键信息
        
        Args:
            answers: 生成的答案列表
            contexts: 对应的上下文列表
            
        Returns:
            幻觉率 (0-1)
        """
        if len(answers) != len(contexts):
            logger.warning(f"Length mismatch: answers={len(answers)}, contexts={len(contexts)}")
            return 1.0
        
        if not answers or not contexts:
            return 0.0
        
        hallucination_scores = []
        
        for answer, context in zip(answers, contexts):
            if not answer.strip() or not context.strip():
                hallucination_scores.append(0.0)
                continue
            
            # 简化实现：基于关键词重叠
            answer_words = set(answer.lower().split())
            context_words = set(context.lower().split())
            
            # 过滤停用词（简化版）
            stop_words = {'的', '了', '在', '是', '有', '和', '与', '或', '但', '而', '因为', '所以', '如果', '那么'}
            answer_words = answer_words - stop_words
            context_words = context_words - stop_words
            
            if not answer_words:
                hallucination_scores.append(0.0)
                continue
            
            # 计算未支持的词汇比例
            unsupported_words = answer_words - context_words
            hallucination_rate = len(unsupported_words) / len(answer_words)
            hallucination_scores.append(hallucination_rate)
        
        return np.mean(hallucination_scores) if hallucination_scores else 0.0
    
    @staticmethod
    def reasoning_completeness(answers: List[str], expected_entities: List[Set[str]]) -> float:
        """
        计算推理完整性 - 检查答案中是否包含预期的实体关联
        
        Args:
            answers: 生成的答案列表
            expected_entities: 每个答案应包含的实体集合列表
            
        Returns:
            推理完整性分数 (0-1)
        """
        if len(answers) != len(expected_entities):
            logger.warning(f"Length mismatch: answers={len(answers)}, expected_entities={len(expected_entities)}")
            return 0.0
        
        if not answers or not expected_entities:
            return 0.0
        
        completeness_scores = []
        
        for answer, expected_set in zip(answers, expected_entities):
            if not expected_set:
                completeness_scores.append(1.0)
                continue
            
            answer_lower = answer.lower()
            found_entities = 0
            
            for entity in expected_set:
                if entity.lower() in answer_lower:
                    found_entities += 1
            
            completeness = found_entities / len(expected_set)
            completeness_scores.append(completeness)
        
        return np.mean(completeness_scores) if completeness_scores else 0.0
    
    @staticmethod
    def compute_all_extrinsic_metrics(retrieval_results: List[List[str]],
                                    ground_truth_retrieval: List[Set[str]],
                                    generated_answers: List[str],
                                    reference_answers: List[str],
                                    contexts: List[str],
                                    expected_entities: List[Set[str]],
                                    k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, Dict]:
        """
        计算所有外在性能指标
        
        Args:
            retrieval_results: 检索结果列表
            ground_truth_retrieval: 真实检索结果
            generated_answers: 生成的答案
            reference_answers: 参考答案
            contexts: 上下文
            expected_entities: 预期实体
            k_values: K值列表
            
        Returns:
            包含所有指标的字典
        """
        results = {}
        
        # 检索指标
        if retrieval_results and ground_truth_retrieval:
            # MRR (假设每个查询只有一个正确答案)
            single_truth = [list(truth_set)[0] if truth_set else "" for truth_set in ground_truth_retrieval]
            results['mrr'] = ExtrinsicMetrics.mean_reciprocal_rank(retrieval_results, single_truth)
            
            # Precision@K, Recall@K, F1@K
            for k in k_values:
                results[f'precision_at_{k}'] = ExtrinsicMetrics.precision_at_k(retrieval_results, ground_truth_retrieval, k)
                results[f'recall_at_{k}'] = ExtrinsicMetrics.recall_at_k(retrieval_results, ground_truth_retrieval, k)
                results[f'f1_at_{k}'] = ExtrinsicMetrics.f1_at_k(retrieval_results, ground_truth_retrieval, k)
        
        # 答案质量指标
        if generated_answers and reference_answers:
            results['bleu'] = ExtrinsicMetrics.bleu_score(generated_answers, reference_answers)
            results['rouge_1'] = ExtrinsicMetrics.rouge_score(generated_answers, reference_answers, 'rouge-1')
            results['rouge_2'] = ExtrinsicMetrics.rouge_score(generated_answers, reference_answers, 'rouge-2')
            results['rouge_l'] = ExtrinsicMetrics.rouge_score(generated_answers, reference_answers, 'rouge-l')
            results['bert_score'] = ExtrinsicMetrics.bert_score(generated_answers, reference_answers)
        
        # 幻觉率
        if generated_answers and contexts:
            results['hallucination_rate'] = ExtrinsicMetrics.hallucination_rate(generated_answers, contexts)
        
        # 推理完整性
        if generated_answers and expected_entities:
            results['reasoning_completeness'] = ExtrinsicMetrics.reasoning_completeness(generated_answers, expected_entities)
        
        return results


class EfficiencyMetrics:
    """效率指标 - 测量计算效率和资源使用"""
    
    @staticmethod
    def measure_retrieval_time(retrieval_func, queries: List[str], 
                             warmup_runs: int = 3) -> Dict[str, float]:
        """
        测量检索时间
        
        Args:
            retrieval_func: 检索函数
            queries: 查询列表
            warmup_runs: 预热运行次数
            
        Returns:
            包含时间统计的字典
        """
        if not queries:
            return {'mean_time': 0.0, 'std_time': 0.0, 'median_time': 0.0, 'p95_time': 0.0}
        
        # 预热
        for i in range(min(warmup_runs, len(queries))):
            try:
                _ = retrieval_func(queries[i])
            except Exception as e:
                logger.warning(f"Warmup run {i} failed: {e}")
        
        # 实际测量
        times = []
        for query in queries:
            start_time = time.perf_counter()
            try:
                _ = retrieval_func(query)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                logger.error(f"Retrieval failed for query '{query}': {e}")
                # 记录失败但不影响其他测量
                continue
        
        if not times:
            logger.warning("No successful retrievals for timing measurement")
            return {'mean_time': 0.0, 'std_time': 0.0, 'median_time': 0.0, 'p95_time': 0.0}
        
        return {
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'median_time': np.median(times),
            'p95_time': np.percentile(times, 95),
            'min_time': np.min(times),
            'max_time': np.max(times),
            'total_time': np.sum(times),
            'n_queries': len(times)
        }
    
    @staticmethod
    async def measure_async_retrieval_time(retrieval_func, queries: List[str], 
                                         warmup_runs: int = 3) -> Dict[str, float]:
        """
        测量异步检索时间
        
        Args:
            retrieval_func: 异步检索函数
            queries: 查询列表
            warmup_runs: 预热运行次数
            
        Returns:
            包含时间统计的字典
        """
        if not queries:
            return {'mean_time': 0.0, 'std_time': 0.0, 'median_time': 0.0, 'p95_time': 0.0}
        
        # 预热
        for i in range(min(warmup_runs, len(queries))):
            try:
                await retrieval_func(queries[i])
            except Exception as e:
                logger.warning(f"Async warmup run {i} failed: {e}")
        
        # 实际测量
        times = []
        for query in queries:
            start_time = time.perf_counter()
            try:
                await retrieval_func(query)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                logger.error(f"Async retrieval failed for query '{query}': {e}")
                continue
        
        if not times:
            logger.warning("No successful async retrievals for timing measurement")
            return {'mean_time': 0.0, 'std_time': 0.0, 'median_time': 0.0, 'p95_time': 0.0}
        
        return {
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'median_time': np.median(times),
            'p95_time': np.percentile(times, 95),
            'min_time': np.min(times),
            'max_time': np.max(times),
            'total_time': np.sum(times),
            'n_queries': len(times)
        }
    
    @staticmethod
    def measure_resource_usage() -> Dict[str, float]:
        """
        测量当前进程的资源使用情况
        
        Returns:
            包含CPU、内存等资源使用的字典
        """
        try:
            process = psutil.Process()
            
            # CPU使用率（需要一小段时间来计算）
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # 内存使用
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # 线程数
            num_threads = process.num_threads()
            
            # 文件描述符数量（Unix系统）
            try:
                num_fds = process.num_fds()
            except (AttributeError, psutil.AccessDenied):
                num_fds = -1
            
            # 系统整体资源
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory()
            
            return {
                'process_cpu_percent': cpu_percent,
                'process_memory_mb': memory_mb,
                'process_memory_percent': memory_percent,
                'process_num_threads': num_threads,
                'process_num_fds': num_fds,
                'system_cpu_percent': system_cpu,
                'system_memory_total_gb': system_memory.total / 1024 / 1024 / 1024,
                'system_memory_available_gb': system_memory.available / 1024 / 1024 / 1024,
                'system_memory_percent': system_memory.percent
            }
            
        except Exception as e:
            logger.error(f"Error measuring resource usage: {e}")
            return {
                'process_cpu_percent': 0.0,
                'process_memory_mb': 0.0,
                'process_memory_percent': 0.0,
                'process_num_threads': 0,
                'process_num_fds': -1,
                'system_cpu_percent': 0.0,
                'system_memory_total_gb': 0.0,
                'system_memory_available_gb': 0.0,
                'system_memory_percent': 0.0
            }
    
    @staticmethod
    def measure_api_cost(texts: List[str], model_name: str = "gpt-3.5-turbo") -> Dict[str, int]:
        """
        测量API成本（token数量）
        
        Args:
            texts: 文本列表
            model_name: 模型名称
            
        Returns:
            包含token统计的字典
        """
        try:
            if not TIKTOKEN_AVAILABLE:
                logger.warning("tiktoken not available, returning 0 for token counts")
                return {
                    'total_tokens': 0,
                    'mean_tokens_per_text': 0,
                    'max_tokens_per_text': 0,
                    'min_tokens_per_text': 0,
                    'n_texts': len(texts)
                }
            
            # 获取对应模型的编码器
            if "gpt-4" in model_name.lower():
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model_name.lower():
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # 默认使用cl100k_base编码
                encoding = tiktoken.get_encoding("cl100k_base")
            
            token_counts = []
            total_tokens = 0
            
            for text in texts:
                if not text:
                    token_counts.append(0)
                    continue
                
                try:
                    tokens = encoding.encode(text)
                    count = len(tokens)
                    token_counts.append(count)
                    total_tokens += count
                except Exception as e:
                    logger.warning(f"Error encoding text: {e}")
                    token_counts.append(0)
            
            return {
                'total_tokens': total_tokens,
                'mean_tokens_per_text': np.mean(token_counts) if token_counts else 0,
                'max_tokens_per_text': max(token_counts) if token_counts else 0,
                'min_tokens_per_text': min(token_counts) if token_counts else 0,
                'n_texts': len(texts)
            }
            

        except Exception as e:
            logger.error(f"Error measuring API cost: {e}")
            return {
                'total_tokens': 0,
                'mean_tokens_per_text': 0,
                'max_tokens_per_text': 0,
                'min_tokens_per_text': 0,
                'n_texts': len(texts)
            }
    
    @staticmethod
    def measure_storage_requirements(graph_storage, vector_storage=None) -> Dict[str, Union[int, float]]:
        """
        测量存储需求
        
        Args:
            graph_storage: 图存储实例
            vector_storage: 向量存储实例（可选）
            
        Returns:
            包含存储统计的字典
        """
        try:
            storage_stats = {
                'graph_nodes': 0,
                'graph_edges': 0,
                'graph_size_estimate_mb': 0.0,
                'vector_size_estimate_mb': 0.0,
                'total_size_estimate_mb': 0.0
            }
            
            # 图存储统计
            if hasattr(graph_storage, 'get_node_count'):
                storage_stats['graph_nodes'] = graph_storage.get_node_count()
            
            if hasattr(graph_storage, 'get_edge_count'):
                storage_stats['graph_edges'] = graph_storage.get_edge_count()
            
            # 估算图存储大小（粗略估计）
            # 假设每个节点平均1KB，每条边平均100B
            estimated_graph_size = (storage_stats['graph_nodes'] * 1024 + 
                                  storage_stats['graph_edges'] * 100) / 1024 / 1024
            storage_stats['graph_size_estimate_mb'] = estimated_graph_size
            
            # 向量存储统计
            if vector_storage:
                if hasattr(vector_storage, 'get_vector_count'):
                    vector_count = vector_storage.get_vector_count()
                    # 假设每个向量1536维，每维4字节（float32）
                    estimated_vector_size = vector_count * 1536 * 4 / 1024 / 1024
                    storage_stats['vector_size_estimate_mb'] = estimated_vector_size
            
            storage_stats['total_size_estimate_mb'] = (storage_stats['graph_size_estimate_mb'] + 
                                                     storage_stats['vector_size_estimate_mb'])
            
            return storage_stats
            
        except Exception as e:
            logger.error(f"Error measuring storage requirements: {e}")
            return {
                'graph_nodes': 0,
                'graph_edges': 0,
                'graph_size_estimate_mb': 0.0,
                'vector_size_estimate_mb': 0.0,
                'total_size_estimate_mb': 0.0
            }
    
    @staticmethod
    def compute_efficiency_improvement(baseline_metrics: Dict[str, float], 
                                     improved_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        计算效率改进
        
        Args:
            baseline_metrics: 基线指标
            improved_metrics: 改进后指标
            
        Returns:
            包含改进百分比的字典
        """
        improvements = {}
        
        for metric_name in baseline_metrics:
            if metric_name in improved_metrics:
                baseline_val = baseline_metrics[metric_name]
                improved_val = improved_metrics[metric_name]
                
                if baseline_val != 0:
                    # 对于时间类指标，减少是改进
                    if 'time' in metric_name.lower():
                        improvement = (baseline_val - improved_val) / baseline_val * 100
                    # 对于其他指标，增加是改进
                    else:
                        improvement = (improved_val - baseline_val) / baseline_val * 100
                    
                    improvements[f'{metric_name}_improvement_percent'] = improvement
                else:
                    improvements[f'{metric_name}_improvement_percent'] = 0.0
        
        return improvements
    
    @staticmethod
    def compute_all_efficiency_metrics(retrieval_func, queries: List[str],
                                     texts_for_cost: List[str],
                                     graph_storage, vector_storage=None,
                                     model_name: str = "gpt-3.5-turbo") -> Dict[str, Dict]:
        """
        计算所有效率指标
        
        Args:
            retrieval_func: 检索函数
            queries: 查询列表
            texts_for_cost: 用于成本计算的文本
            graph_storage: 图存储
            vector_storage: 向量存储
            model_name: 模型名称
            
        Returns:
            包含所有效率指标的字典
        """
        results = {}
        
        # 检索时间
        if retrieval_func and queries:
            results['retrieval_time'] = EfficiencyMetrics.measure_retrieval_time(retrieval_func, queries)
        
        # 资源使用
        results['resource_usage'] = EfficiencyMetrics.measure_resource_usage()
        
        # API成本
        if texts_for_cost:
            results['api_cost'] = EfficiencyMetrics.measure_api_cost(texts_for_cost, model_name)
        
        # 存储需求
        if graph_storage:
            results['storage_requirements'] = EfficiencyMetrics.measure_storage_requirements(
                graph_storage, vector_storage
            )
        
        return results


class StatisticalTests:
    """统计显著性检验 - 验证实验结果的统计显著性"""
    
    @staticmethod
    def paired_t_test(group1: List[float], group2: List[float], 
                     alternative: str = 'two-sided') -> Dict[str, float]:
        """
        配对t检验 - 比较两组配对样本的均值差异
        
        Args:
            group1: 第一组数据（如基线方法的性能）
            group2: 第二组数据（如改进方法的性能）
            alternative: 检验类型 ('two-sided', 'less', 'greater')
            
        Returns:
            包含t统计量、p值和置信区间的字典
        """
        if len(group1) != len(group2):
            logger.error(f"Groups must have same length: {len(group1)} vs {len(group2)}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'confidence_interval': (0.0, 0.0),
                'mean_diff': 0.0,
                'std_diff': 0.0,
                'n_samples': 0,
                'significant': False,
                'error': 'Length mismatch'
            }
        
        if len(group1) < 2:
            logger.warning(f"Not enough samples for t-test: {len(group1)}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'confidence_interval': (0.0, 0.0),
                'mean_diff': 0.0,
                'std_diff': 0.0,
                'n_samples': len(group1),
                'significant': False,
                'error': 'Insufficient samples'
            }
        
        try:
            # 执行配对t检验
            statistic, p_value = ttest_rel(group2, group1, alternative=alternative)
            
            # 计算差值统计
            differences = np.array(group2) - np.array(group1)
            mean_diff = np.mean(differences)
            std_diff = np.std(differences, ddof=1)
            
            # 计算95%置信区间
            from scipy.stats import t
            n = len(differences)
            t_critical = t.ppf(0.975, n-1)  # 95% 置信区间
            margin_error = t_critical * std_diff / np.sqrt(n)
            confidence_interval = (mean_diff - margin_error, mean_diff + margin_error)
            
            # 判断是否显著（α = 0.05）
            significant = p_value < 0.05
            
            return {
                'statistic': float(statistic),
                'p_value': float(p_value),
                'confidence_interval': confidence_interval,
                'mean_diff': float(mean_diff),
                'std_diff': float(std_diff),
                'n_samples': n,
                'significant': significant,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error in paired t-test: {e}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'confidence_interval': (0.0, 0.0),
                'mean_diff': 0.0,
                'std_diff': 0.0,
                'n_samples': len(group1),
                'significant': False,
                'error': str(e)
            }
    
    @staticmethod
    def wilcoxon_signed_rank_test(group1: List[float], group2: List[float],
                                 alternative: str = 'two-sided') -> Dict[str, float]:
        """
        Wilcoxon符号秩检验 - 非参数配对样本检验
        
        Args:
            group1: 第一组数据（如基线方法的性能）
            group2: 第二组数据（如改进方法的性能）
            alternative: 检验类型 ('two-sided', 'less', 'greater')
            
        Returns:
            包含统计量、p值等的字典
        """
        if len(group1) != len(group2):
            logger.error(f"Groups must have same length: {len(group1)} vs {len(group2)}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'median_diff': 0.0,
                'n_samples': 0,
                'significant': False,
                'error': 'Length mismatch'
            }
        
        if len(group1) < 3:
            logger.warning(f"Not enough samples for Wilcoxon test: {len(group1)}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'median_diff': 0.0,
                'n_samples': len(group1),
                'significant': False,
                'error': 'Insufficient samples'
            }
        
        try:
            # 计算差值
            differences = np.array(group2) - np.array(group1)
            
            # 过滤零差值
            non_zero_diffs = differences[differences != 0]
            
            if len(non_zero_diffs) < 3:
                logger.warning("Too many zero differences for Wilcoxon test")
                return {
                    'statistic': 0.0,
                    'p_value': 1.0,
                    'median_diff': float(np.median(differences)),
                    'n_samples': len(group1),
                    'significant': False,
                    'error': 'Too many zero differences'
                }
            
            # 执行Wilcoxon符号秩检验
            statistic, p_value = wilcoxon(non_zero_diffs, alternative=alternative)
            
            # 计算中位数差值
            median_diff = np.median(differences)
            
            # 判断是否显著（α = 0.05）
            significant = p_value < 0.05
            
            return {
                'statistic': float(statistic),
                'p_value': float(p_value),
                'median_diff': float(median_diff),
                'n_samples': len(group1),
                'n_non_zero': len(non_zero_diffs),
                'significant': significant,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error in Wilcoxon signed-rank test: {e}")
            return {
                'statistic': 0.0,
                'p_value': 1.0,
                'median_diff': 0.0,
                'n_samples': len(group1),
                'significant': False,
                'error': str(e)
            }
    
    @staticmethod
    def compute_confidence_interval(data: List[float], confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        计算置信区间
        
        Args:
            data: 数据列表
            confidence_level: 置信水平（默认0.95）
            
        Returns:
            置信区间元组 (lower_bound, upper_bound)
        """
        if not data or len(data) < 2:
            return (0.0, 0.0)
        
        try:
            from scipy.stats import t
            
            data_array = np.array(data)
            n = len(data_array)
            mean = np.mean(data_array)
            std = np.std(data_array, ddof=1)
            
            # 计算t临界值
            alpha = 1 - confidence_level
            t_critical = t.ppf(1 - alpha/2, n-1)
            
            # 计算边际误差
            margin_error = t_critical * std / np.sqrt(n)
            
            return (mean - margin_error, mean + margin_error)
            
        except Exception as e:
            logger.error(f"Error computing confidence interval: {e}")
            return (0.0, 0.0)
    
    @staticmethod
    def multiple_comparisons_correction(p_values: List[float], 
                                      method: str = 'bonferroni') -> List[float]:
        """
        多重比较校正
        
        Args:
            p_values: p值列表
            method: 校正方法 ('bonferroni', 'holm')
            
        Returns:
            校正后的p值列表
        """
        if not p_values:
            return []
        
        try:
            p_array = np.array(p_values)
            n = len(p_array)
            
            if method == 'bonferroni':
                # Bonferroni校正：p_corrected = p * n
                corrected = np.minimum(p_array * n, 1.0)
            
            elif method == 'holm':
                # Holm校正
                sorted_indices = np.argsort(p_array)
                corrected = np.zeros_like(p_array)
                
                for i, idx in enumerate(sorted_indices):
                    corrected[idx] = min(p_array[idx] * (n - i), 1.0)
                    
                # 确保单调性
                for i in range(1, n):
                    idx = sorted_indices[i]
                    prev_idx = sorted_indices[i-1]
                    corrected[idx] = max(corrected[idx], corrected[prev_idx])
            
            else:
                logger.warning(f"Unknown correction method: {method}, returning original p-values")
                corrected = p_array
            
            return corrected.tolist()
            
        except Exception as e:
            logger.error(f"Error in multiple comparisons correction: {e}")
            return p_values
    
    @staticmethod
    def effect_size_cohens_d(group1: List[float], group2: List[float]) -> float:
        """
        计算Cohen's d效应量
        
        Args:
            group1: 第一组数据
            group2: 第二组数据
            
        Returns:
            Cohen's d效应量
        """
        if not group1 or not group2:
            return 0.0
        
        try:
            group1_array = np.array(group1)
            group2_array = np.array(group2)
            
            mean1 = np.mean(group1_array)
            mean2 = np.mean(group2_array)
            
            # 计算合并标准差
            n1, n2 = len(group1_array), len(group2_array)
            var1 = np.var(group1_array, ddof=1)
            var2 = np.var(group2_array, ddof=1)
            
            pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            
            if pooled_std == 0:
                return 0.0
            
            cohens_d = (mean2 - mean1) / pooled_std
            return float(cohens_d)
            
        except Exception as e:
            logger.error(f"Error computing Cohen's d: {e}")
            return 0.0
    
    @staticmethod
    def compare_methods(baseline_results: Dict[str, List[float]], 
                       improved_results: Dict[str, List[float]],
                       alpha: float = 0.05) -> Dict[str, Dict]:
        """
        比较多个方法的性能并进行统计检验
        
        Args:
            baseline_results: 基线方法结果 {metric_name: [values]}
            improved_results: 改进方法结果 {metric_name: [values]}
            alpha: 显著性水平
            
        Returns:
            包含所有比较结果的字典
        """
        comparison_results = {}
        
        # 收集所有p值用于多重比较校正
        all_p_values = []
        metric_names = []
        
        for metric_name in baseline_results:
            if metric_name not in improved_results:
                logger.warning(f"Metric {metric_name} not found in improved results")
                continue
            
            baseline_values = baseline_results[metric_name]
            improved_values = improved_results[metric_name]
            
            if len(baseline_values) != len(improved_values):
                logger.warning(f"Length mismatch for {metric_name}: {len(baseline_values)} vs {len(improved_values)}")
                continue
            
            # 配对t检验
            t_test_result = StatisticalTests.paired_t_test(baseline_values, improved_values)
            
            # Wilcoxon符号秩检验
            wilcoxon_result = StatisticalTests.wilcoxon_signed_rank_test(baseline_values, improved_values)
            
            # 效应量
            effect_size = StatisticalTests.effect_size_cohens_d(baseline_values, improved_values)
            
            # 置信区间
            baseline_ci = StatisticalTests.compute_confidence_interval(baseline_values)
            improved_ci = StatisticalTests.compute_confidence_interval(improved_values)
            
            comparison_results[metric_name] = {
                'baseline_mean': np.mean(baseline_values),
                'baseline_std': np.std(baseline_values),
                'baseline_ci': baseline_ci,
                'improved_mean': np.mean(improved_values),
                'improved_std': np.std(improved_values),
                'improved_ci': improved_ci,
                't_test': t_test_result,
                'wilcoxon_test': wilcoxon_result,
                'effect_size_cohens_d': effect_size,
                'n_samples': len(baseline_values)
            }
            
            # 收集p值
            all_p_values.append(t_test_result['p_value'])
            metric_names.append(f"{metric_name}_t_test")
            
            all_p_values.append(wilcoxon_result['p_value'])
            metric_names.append(f"{metric_name}_wilcoxon")
        
        # 多重比较校正
        if all_p_values:
            corrected_p_bonferroni = StatisticalTests.multiple_comparisons_correction(
                all_p_values, method='bonferroni'
            )
            corrected_p_holm = StatisticalTests.multiple_comparisons_correction(
                all_p_values, method='holm'
            )
            
            # 将校正后的p值添加到结果中
            p_idx = 0
            for metric_name in comparison_results:
                comparison_results[metric_name]['t_test']['p_value_bonferroni'] = corrected_p_bonferroni[p_idx]
                comparison_results[metric_name]['t_test']['p_value_holm'] = corrected_p_holm[p_idx]
                comparison_results[metric_name]['t_test']['significant_bonferroni'] = corrected_p_bonferroni[p_idx] < alpha
                comparison_results[metric_name]['t_test']['significant_holm'] = corrected_p_holm[p_idx] < alpha
                p_idx += 1
                
                comparison_results[metric_name]['wilcoxon_test']['p_value_bonferroni'] = corrected_p_bonferroni[p_idx]
                comparison_results[metric_name]['wilcoxon_test']['p_value_holm'] = corrected_p_holm[p_idx]
                comparison_results[metric_name]['wilcoxon_test']['significant_bonferroni'] = corrected_p_bonferroni[p_idx] < alpha
                comparison_results[metric_name]['wilcoxon_test']['significant_holm'] = corrected_p_holm[p_idx] < alpha
                p_idx += 1
        
        return comparison_results
    
    @staticmethod
    def format_significance_stars(p_value: float) -> str:
        """
        将p值转换为显著性星号标记
        
        Args:
            p_value: p值
            
        Returns:
            显著性标记字符串
        """
        if p_value < 0.001:
            return "***"
        elif p_value < 0.01:
            return "**"
        elif p_value < 0.05:
            return "*"
        else:
            return ""
    
    @staticmethod
    def generate_comparison_table(comparison_results: Dict[str, Dict], 
                                format_type: str = 'markdown') -> str:
        """
        生成比较结果表格
        
        Args:
            comparison_results: 比较结果字典
            format_type: 表格格式 ('markdown', 'latex')
            
        Returns:
            格式化的表格字符串
        """
        if not comparison_results:
            return "No comparison results available."
        
        try:
            if format_type == 'markdown':
                return StatisticalTests._generate_markdown_table(comparison_results)
            elif format_type == 'latex':
                return StatisticalTests._generate_latex_table(comparison_results)
            else:
                logger.warning(f"Unknown format type: {format_type}, using markdown")
                return StatisticalTests._generate_markdown_table(comparison_results)
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")
            return f"Error generating table: {e}"
    
    @staticmethod
    def _generate_markdown_table(comparison_results: Dict[str, Dict]) -> str:
        """生成Markdown格式的比较表格"""
        lines = []
        lines.append("| Metric | Baseline | Improved | Improvement | t-test p-value | Wilcoxon p-value | Effect Size | Significance |")
        lines.append("|--------|----------|----------|-------------|----------------|------------------|-------------|--------------|")
        
        for metric_name, results in comparison_results.items():
            baseline_mean = results['baseline_mean']
            improved_mean = results['improved_mean']
            
            # 计算改进百分比
            if baseline_mean != 0:
                improvement = (improved_mean - baseline_mean) / baseline_mean * 100
            else:
                improvement = 0.0
            
            t_p_value = results['t_test']['p_value']
            wilcoxon_p_value = results['wilcoxon_test']['p_value']
            effect_size = results['effect_size_cohens_d']
            
            # 显著性标记
            t_stars = StatisticalTests.format_significance_stars(t_p_value)
            wilcoxon_stars = StatisticalTests.format_significance_stars(wilcoxon_p_value)
            
            lines.append(
                f"| {metric_name} | {baseline_mean:.4f} | {improved_mean:.4f} | "
                f"{improvement:+.2f}% | {t_p_value:.4f}{t_stars} | "
                f"{wilcoxon_p_value:.4f}{wilcoxon_stars} | {effect_size:.3f} | "
                f"{'Yes' if t_p_value < 0.05 else 'No'} |"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_latex_table(comparison_results: Dict[str, Dict]) -> str:
        """生成LaTeX格式的比较表格"""
        lines = []
        lines.append("\\begin{table}[htbp]")
        lines.append("\\centering")
        lines.append("\\caption{Performance Comparison Results}")
        lines.append("\\begin{tabular}{|l|c|c|c|c|c|c|c|}")
        lines.append("\\hline")
        lines.append("Metric & Baseline & Improved & Improvement & t-test & Wilcoxon & Effect Size & Significant \\\\")
        lines.append("\\hline")
        
        for metric_name, results in comparison_results.items():
            baseline_mean = results['baseline_mean']
            improved_mean = results['improved_mean']
            
            # 计算改进百分比
            if baseline_mean != 0:
                improvement = (improved_mean - baseline_mean) / baseline_mean * 100
            else:
                improvement = 0.0
            
            t_p_value = results['t_test']['p_value']
            wilcoxon_p_value = results['wilcoxon_test']['p_value']
            effect_size = results['effect_size_cohens_d']
            
            # 显著性标记
            t_stars = StatisticalTests.format_significance_stars(t_p_value)
            wilcoxon_stars = StatisticalTests.format_significance_stars(wilcoxon_p_value)
            
            # 转义LaTeX特殊字符
            metric_name_escaped = metric_name.replace('_', '\\_')
            
            lines.append(
                f"{metric_name_escaped} & {baseline_mean:.4f} & {improved_mean:.4f} & "
                f"{improvement:+.2f}\\% & {t_p_value:.4f}{t_stars} & "
                f"{wilcoxon_p_value:.4f}{wilcoxon_stars} & {effect_size:.3f} & "
                f"{'Yes' if t_p_value < 0.05 else 'No'} \\\\"
            )
        
        lines.append("\\hline")
        lines.append("\\end{tabular}")
        lines.append("\\label{tab:performance_comparison}")
        lines.append("\\end{table}")
        
        return "\n".join(lines)
