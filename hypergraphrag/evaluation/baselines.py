"""
Baseline methods for comparison with DynHyperRAG.

This module implements various baseline methods for evaluating hyperedge quality
and retrieval performance, providing comparison points for the DynHyperRAG system.
"""

import random
import logging
from typing import Dict, List, Optional, Union
import numpy as np

from ..base import BaseGraphStorage

logger = logging.getLogger(__name__)


class BaselineMethods:
    """
    Baseline methods for hyperedge quality assessment and retrieval.
    
    This class implements several baseline approaches:
    1. LLM Confidence Baseline - uses original LLM weights as quality scores
    2. Rule-based Baseline - combines degree and text length heuristics
    3. Random Baseline - assigns random quality scores
    4. Static HyperGraphRAG - original system without dynamic updates
    """
    
    def __init__(self, graph_storage: BaseGraphStorage, config: Optional[Dict] = None):
        """
        Initialize baseline methods.
        
        Args:
            graph_storage: Graph storage instance
            config: Configuration dictionary
        """
        self.graph_storage = graph_storage
        self.config = config or {}
        self.random_seed = self.config.get('random_seed', 42)
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)
    
    async def llm_confidence_baseline(self, hyperedge_id: str) -> float:
        """
        Baseline 1: LLM Confidence
        
        Uses the original LLM-assigned weight as a confidence/quality score.
        This represents the baseline approach of trusting LLM extraction confidence.
        
        Args:
            hyperedge_id: ID of the hyperedge to evaluate
            
        Returns:
            Quality score based on LLM confidence (0-1)
        """
        try:
            node = await self.graph_storage.get_node(hyperedge_id)
            if not node:
                logger.warning(f"Node {hyperedge_id} not found for LLM confidence baseline")
                return 0.5  # Default score
            
            # Use original weight field as confidence
            weight = node.get('weight', 1.0)
            
            # Normalize weight to 0-1 range
            # Assuming weights are typically in range [0, 100] based on LLM extraction
            normalized_score = min(1.0, max(0.0, weight / 100.0))
            
            return normalized_score
            
        except Exception as e:
            logger.error(f"Error computing LLM confidence baseline for {hyperedge_id}: {e}")
            return 0.5
    
    async def rule_based_baseline(self, hyperedge_id: str) -> float:
        """
        Baseline 2: Rule-based Quality Assessment
        
        Combines simple heuristics:
        - Node degree (connectivity)
        - Text length (completeness)
        
        Args:
            hyperedge_id: ID of the hyperedge to evaluate
            
        Returns:
            Quality score based on rules (0-1)
        """
        try:
            node = await self.graph_storage.get_node(hyperedge_id)
            if not node:
                logger.warning(f"Node {hyperedge_id} not found for rule-based baseline")
                return 0.5
            
            # Feature 1: Node degree (connectivity)
            degree = await self.graph_storage.node_degree(hyperedge_id)
            degree_score = min(1.0, degree / 5.0)  # Normalize assuming max useful degree ~5
            
            # Feature 2: Text length (completeness)
            hyperedge_text = node.get('hyperedge', '')
            text_length = len(hyperedge_text)
            text_score = min(1.0, text_length / 100.0)  # Normalize assuming good length ~100 chars
            
            # Simple weighted combination
            rule_score = 0.5 * degree_score + 0.5 * text_score
            
            return rule_score
            
        except Exception as e:
            logger.error(f"Error computing rule-based baseline for {hyperedge_id}: {e}")
            return 0.5
    
    async def random_baseline(self, hyperedge_id: str) -> float:
        """
        Baseline 3: Random Quality Assignment
        
        Assigns random quality scores to provide a lower bound for comparison.
        
        Args:
            hyperedge_id: ID of the hyperedge to evaluate
            
        Returns:
            Random quality score (0-1)
        """
        try:
            # Use hyperedge_id as seed for reproducible randomness
            local_random = random.Random(hash(hyperedge_id) % (2**32))
            return local_random.random()
            
        except Exception as e:
            logger.error(f"Error computing random baseline for {hyperedge_id}: {e}")
            return 0.5
    
    async def compute_baseline_scores(self, hyperedge_ids: List[str], 
                                    method: str = 'all') -> Dict[str, Dict[str, float]]:
        """
        Compute baseline scores for multiple hyperedges.
        
        Args:
            hyperedge_ids: List of hyperedge IDs to evaluate
            method: Baseline method ('llm_confidence', 'rule_based', 'random', 'all')
            
        Returns:
            Dictionary mapping method names to {hyperedge_id: score} dictionaries
        """
        results = {}
        
        if method == 'all' or method == 'llm_confidence':
            logger.info("Computing LLM confidence baseline scores...")
            llm_scores = {}
            for he_id in hyperedge_ids:
                llm_scores[he_id] = await self.llm_confidence_baseline(he_id)
            results['llm_confidence'] = llm_scores
        
        if method == 'all' or method == 'rule_based':
            logger.info("Computing rule-based baseline scores...")
            rule_scores = {}
            for he_id in hyperedge_ids:
                rule_scores[he_id] = await self.rule_based_baseline(he_id)
            results['rule_based'] = rule_scores
        
        if method == 'all' or method == 'random':
            logger.info("Computing random baseline scores...")
            random_scores = {}
            for he_id in hyperedge_ids:
                random_scores[he_id] = await self.random_baseline(he_id)
            results['random'] = random_scores
        
        return results
    
    async def get_all_hyperedge_ids(self) -> List[str]:
        """
        Get all hyperedge IDs from the graph storage.
        
        Returns:
            List of hyperedge IDs
        """
        try:
            # This is a simplified approach - in practice, you might need
            # to iterate through nodes and filter by role='hyperedge'
            # For now, we'll assume the graph storage provides a way to get all nodes
            
            # Since NetworkXStorage doesn't have a direct method to get all nodes,
            # we'll need to work with what's available
            logger.warning("get_all_hyperedge_ids not fully implemented - requires graph traversal")
            return []
            
        except Exception as e:
            logger.error(f"Error getting hyperedge IDs: {e}")
            return []


class StaticHyperGraphRAG:
    """
    Static HyperGraphRAG Baseline
    
    This class implements the original HyperGraphRAG system without dynamic updates,
    serving as a baseline for comparison with DynHyperRAG. It uses the same core
    logic as the original system but disables:
    - Quality-aware ranking
    - Dynamic weight updates  
    - Entity type filtering
    - Hyperedge refinement
    """
    
    def __init__(self, graph_storage: BaseGraphStorage, entities_vdb, hyperedges_vdb,
                 text_chunks_db, embedding_func, llm_func, config: Optional[Dict] = None):
        """
        Initialize static HyperGraphRAG baseline.
        
        Args:
            graph_storage: Graph storage instance
            entities_vdb: Entity vector database
            hyperedges_vdb: Hyperedge vector database  
            text_chunks_db: Text chunks database
            embedding_func: Embedding function
            llm_func: LLM function
            config: Configuration dictionary
        """
        self.graph_storage = graph_storage
        self.entities_vdb = entities_vdb
        self.hyperedges_vdb = hyperedges_vdb
        self.text_chunks_db = text_chunks_db
        self.embedding_func = embedding_func
        self.llm_func = llm_func
        self.config = config or {}
        
        # Ensure static behavior by disabling dynamic features
        self.config['enable_quality_ranking'] = False
        self.config['enable_dynamic_updates'] = False
        self.config['enable_entity_filtering'] = False
        self.config['enable_hyperedge_refinement'] = False
    
    async def query(self, query: str, query_param=None, **kwargs) -> str:
        """
        Generate answer using static HyperGraphRAG approach.
        
        This method replicates the original kg_query function but without
        dynamic updates and quality-aware features.
        
        Args:
            query: Query string
            query_param: Query parameters (optional)
            **kwargs: Additional parameters
            
        Returns:
            Generated answer
        """
        try:
            # Import here to avoid circular imports
            from ..base import QueryParam
            from ..operate import _build_query_context
            from ..prompt import PROMPTS
            from ..utils import (
                split_string_by_multi_markers, clean_str, 
                compute_args_hash, handle_cache, save_to_cache, CacheData
            )
            import re
            
            if query_param is None:
                query_param = QueryParam()
            
            # Use the same entity extraction logic as original system
            language = self.config.get("language", PROMPTS["DEFAULT_LANGUAGE"])
            entity_types = self.config.get("entity_types", PROMPTS["DEFAULT_ENTITY_TYPES"])
            
            # Entity extraction prompt (same as original)
            entity_extract_prompt = PROMPTS["entity_extraction"]
            context_base = dict(
                tuple_delimiter=PROMPTS["DEFAULT_TUPLE_DELIMITER"],
                record_delimiter=PROMPTS["DEFAULT_RECORD_DELIMITER"],
                completion_delimiter=PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
                examples="\n".join(PROMPTS["entity_extraction_examples"]),
                language=language,
            )
            
            hint_prompt = entity_extract_prompt.format(
                **context_base, input_text=query
            )
            
            final_result = await self.llm_func(hint_prompt)
            
            # Parse extraction results (same logic as original)
            hl_keywords, ll_keywords = [], []
            try:
                records = split_string_by_multi_markers(
                    final_result,
                    [context_base["record_delimiter"], context_base["completion_delimiter"]],
                )
                for record in records:
                    record = re.search(r"\((.*)\)", record)
                    if record is None:
                        continue
                    record = record.group(1)
                    record_attributes = split_string_by_multi_markers(
                        record, [context_base["tuple_delimiter"]]
                    )
                    if len(record_attributes) == 3 and record_attributes[0] == '"hyper-relation"':
                        hl_keywords.append("<hyperedge>"+clean_str(record_attributes[1]))
                    elif len(record_attributes) == 5 and record_attributes[0] == '"entity"':
                        ll_keywords.append(clean_str(record_attributes[1]).upper())
                    else:
                        continue
            except Exception as e:
                logger.error(f"Entity extraction parsing error: {e}")
                return PROMPTS["fail_response"]
            
            # Handle missing keywords
            if hl_keywords == [] and ll_keywords == []:
                logger.warning("No keywords extracted")
                return PROMPTS["fail_response"]
            
            ll_keywords = ", ".join(ll_keywords) if ll_keywords else ""
            hl_keywords = ", ".join(hl_keywords) if hl_keywords else ""
            
            # Build context using original logic (without dynamic features)
            keywords = [ll_keywords, hl_keywords]
            
            # Create a static config that disables dynamic features
            static_config = self.config.copy()
            static_config.update({
                'llm_model_func': self.llm_func,
                'enable_quality_ranking': False,
                'enable_dynamic_updates': False,
                'enable_entity_filtering': False
            })
            
            context, retrieved_hyperedges = await _build_query_context(
                keywords,
                self.graph_storage,
                self.entities_vdb,
                self.hyperedges_vdb,
                self.text_chunks_db,
                query_param,
                global_config=static_config,
                original_query=query,
            )
            
            if context is None:
                return PROMPTS["fail_response"]
            
            # Generate response using original prompt template
            sys_prompt_temp = PROMPTS["rag_response"]
            sys_prompt = sys_prompt_temp.format(
                context_data=context, 
                response_type=query_param.response_type
            )
            
            response = await self.llm_func(
                query,
                system_prompt=sys_prompt,
                stream=query_param.stream,
            )
            
            # Clean response (same as original)
            if isinstance(response, str) and len(response) > len(sys_prompt):
                response = (
                    response.replace(sys_prompt, "")
                    .replace("user", "")
                    .replace("model", "")
                    .replace(query, "")
                    .replace("<system>", "")
                    .replace("</system>", "")
                    .strip()
                )
            
            # NOTE: No dynamic weight updates in static baseline
            # This is the key difference from DynHyperRAG
            
            return response
            
        except Exception as e:
            logger.error(f"Error in static HyperGraphRAG query: {e}")
            return "Error generating answer."
    
    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Retrieve hyperedges using static approach (for evaluation purposes).
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of retrieved hyperedges with metadata
        """
        try:
            # Simple vector similarity search without quality ranking
            vector_results = await self.hyperedges_vdb.query(query, top_k=top_k)
            
            # Sort by similarity only (no quality awareness)
            vector_results.sort(key=lambda x: x.get('distance', 1.0))
            
            # Add metadata to indicate this is static baseline
            for result in vector_results:
                result['method'] = 'static_hypergraphrag'
                result['quality_score'] = None  # No quality assessment
                result['dynamic_weight'] = None  # No dynamic updates
                result['entity_filtered'] = False  # No entity filtering
            
            return vector_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in static HyperGraphRAG retrieval: {e}")
            return []


class BaselineComparator:
    """
    Utility class for comparing baseline methods with DynHyperRAG.
    """
    
    def __init__(self, baselines: BaselineMethods, static_rag: StaticHyperGraphRAG):
        """
        Initialize baseline comparator.
        
        Args:
            baselines: BaselineMethods instance
            static_rag: StaticHyperGraphRAG instance
        """
        self.baselines = baselines
        self.static_rag = static_rag
    
    async def compare_quality_methods(self, hyperedge_ids: List[str], 
                                    ground_truth: Dict[str, float]) -> Dict[str, Dict]:
        """
        Compare different quality assessment methods.
        
        Args:
            hyperedge_ids: List of hyperedge IDs to evaluate
            ground_truth: Ground truth quality scores
            
        Returns:
            Comparison results for each baseline method
        """
        # Get baseline scores
        baseline_scores = await self.baselines.compute_baseline_scores(hyperedge_ids, 'all')
        
        results = {}
        
        for method_name, scores in baseline_scores.items():
            # Compute correlation with ground truth
            common_ids = set(scores.keys()) & set(ground_truth.keys())
            if len(common_ids) >= 2:
                pred_values = [scores[id_] for id_ in common_ids]
                true_values = [ground_truth[id_] for id_ in common_ids]
                
                from scipy.stats import spearmanr
                correlation, p_value = spearmanr(pred_values, true_values)
                
                results[method_name] = {
                    'correlation': correlation,
                    'p_value': p_value,
                    'n_samples': len(common_ids),
                    'mean_score': np.mean(pred_values),
                    'std_score': np.std(pred_values)
                }
            else:
                results[method_name] = {
                    'correlation': 0.0,
                    'p_value': 1.0,
                    'n_samples': len(common_ids),
                    'mean_score': 0.0,
                    'std_score': 0.0
                }
        
        return results
    
    async def compare_retrieval_methods(self, queries: List[str], 
                                      ground_truth_answers: List[str]) -> Dict[str, Dict]:
        """
        Compare retrieval performance between static and dynamic approaches.
        
        Args:
            queries: List of test queries
            ground_truth_answers: Expected answers
            
        Returns:
            Comparison results
        """
        static_results = []
        
        # Test static HyperGraphRAG
        for query in queries:
            try:
                answer = await self.static_rag.query(query)
                static_results.append(answer)
            except Exception as e:
                logger.error(f"Error in static retrieval for query '{query}': {e}")
                static_results.append("")
        
        # Compute basic metrics (simplified)
        results = {
            'static_hypergraphrag': {
                'n_queries': len(queries),
                'n_successful': len([r for r in static_results if r.strip()]),
                'avg_answer_length': np.mean([len(r) for r in static_results]),
                'answers': static_results
            }
        }
        
        return results


# Utility functions for baseline evaluation
def ensure_fair_comparison(config_dynhyperrag: Dict, config_static: Dict) -> bool:
    """
    Ensure fair comparison between DynHyperRAG and static baselines.
    
    Args:
        config_dynhyperrag: DynHyperRAG configuration
        config_static: Static baseline configuration
        
    Returns:
        True if configurations are compatible for fair comparison
    """
    # Check that key parameters are the same
    key_params = ['embedding_model', 'llm_model', 'top_k', 'max_token_for_text_unit']
    
    for param in key_params:
        if config_dynhyperrag.get(param) != config_static.get(param):
            logger.warning(f"Parameter mismatch: {param}")
            return False
    
    return True


def create_baseline_config(dynhyperrag_config: Dict) -> Dict:
    """
    Create baseline configuration that matches DynHyperRAG for fair comparison.
    
    Args:
        dynhyperrag_config: DynHyperRAG configuration
        
    Returns:
        Baseline configuration
    """
    baseline_config = dynhyperrag_config.copy()
    
    # Remove DynHyperRAG-specific parameters
    dynhyperrag_params = [
        'quality_weights', 'dynamic_update_alpha', 'entity_taxonomy',
        'similarity_weight', 'quality_weight', 'dynamic_weight'
    ]
    
    for param in dynhyperrag_params:
        baseline_config.pop(param, None)
    
    return baseline_config


def create_static_hypergraphrag_from_dynhyperrag(dynhyperrag_instance) -> StaticHyperGraphRAG:
    """
    Create a StaticHyperGraphRAG instance from an existing DynHyperRAG instance.
    
    This ensures fair comparison by using the same storage instances and configuration,
    but disabling dynamic features.
    
    Args:
        dynhyperrag_instance: Existing DynHyperRAG instance
        
    Returns:
        StaticHyperGraphRAG instance configured for fair comparison
    """
    try:
        # Extract components from DynHyperRAG instance
        graph_storage = dynhyperrag_instance.knowledge_graph_inst
        entities_vdb = dynhyperrag_instance.entities_vdb
        hyperedges_vdb = dynhyperrag_instance.hyperedges_vdb
        text_chunks_db = dynhyperrag_instance.text_chunks_db
        embedding_func = dynhyperrag_instance.embedding_func
        llm_func = dynhyperrag_instance.llm_model_func
        
        # Create static configuration
        static_config = create_baseline_config(dynhyperrag_instance.global_config)
        
        # Create static instance
        static_rag = StaticHyperGraphRAG(
            graph_storage=graph_storage,
            entities_vdb=entities_vdb,
            hyperedges_vdb=hyperedges_vdb,
            text_chunks_db=text_chunks_db,
            embedding_func=embedding_func,
            llm_func=llm_func,
            config=static_config
        )
        
        logger.info("Created StaticHyperGraphRAG baseline from DynHyperRAG instance")
        return static_rag
        
    except Exception as e:
        logger.error(f"Error creating static baseline: {e}")
        raise


async def compare_static_vs_dynamic(static_rag: StaticHyperGraphRAG, 
                                   dynhyperrag_instance,
                                   test_queries: List[str],
                                   ground_truth_answers: Optional[List[str]] = None) -> Dict:
    """
    Compare static HyperGraphRAG baseline with DynHyperRAG.
    
    Args:
        static_rag: StaticHyperGraphRAG instance
        dynhyperrag_instance: DynHyperRAG instance
        test_queries: List of test queries
        ground_truth_answers: Optional ground truth answers
        
    Returns:
        Comparison results
    """
    results = {
        'static_results': [],
        'dynamic_results': [],
        'comparison_metrics': {}
    }
    
    logger.info(f"Comparing static vs dynamic on {len(test_queries)} queries...")
    
    # Test static baseline
    for i, query in enumerate(test_queries):
        try:
            static_answer = await static_rag.query(query)
            results['static_results'].append({
                'query': query,
                'answer': static_answer,
                'method': 'static_hypergraphrag'
            })
        except Exception as e:
            logger.error(f"Static query {i} failed: {e}")
            results['static_results'].append({
                'query': query,
                'answer': "Error",
                'method': 'static_hypergraphrag'
            })
    
    # Test dynamic system
    for i, query in enumerate(test_queries):
        try:
            # Assuming DynHyperRAG has a query method
            dynamic_answer = await dynhyperrag_instance.query(query)
            results['dynamic_results'].append({
                'query': query,
                'answer': dynamic_answer,
                'method': 'dynhyperrag'
            })
        except Exception as e:
            logger.error(f"Dynamic query {i} failed: {e}")
            results['dynamic_results'].append({
                'query': query,
                'answer': "Error",
                'method': 'dynhyperrag'
            })
    
    # Compute basic comparison metrics
    static_answers = [r['answer'] for r in results['static_results']]
    dynamic_answers = [r['answer'] for r in results['dynamic_results']]
    
    results['comparison_metrics'] = {
        'n_queries': len(test_queries),
        'static_success_rate': len([a for a in static_answers if a != "Error"]) / len(test_queries),
        'dynamic_success_rate': len([a for a in dynamic_answers if a != "Error"]) / len(test_queries),
        'static_avg_length': np.mean([len(a) for a in static_answers if a != "Error"]),
        'dynamic_avg_length': np.mean([len(a) for a in dynamic_answers if a != "Error"]),
    }
    
    # If ground truth is available, compute similarity metrics
    if ground_truth_answers and len(ground_truth_answers) == len(test_queries):
        try:
            from ..evaluation.metrics import ExtrinsicMetrics
            
            # Compute BLEU scores
            static_bleu = ExtrinsicMetrics.bleu_score(static_answers, ground_truth_answers)
            dynamic_bleu = ExtrinsicMetrics.bleu_score(dynamic_answers, ground_truth_answers)
            
            results['comparison_metrics'].update({
                'static_bleu': static_bleu,
                'dynamic_bleu': dynamic_bleu,
                'bleu_improvement': dynamic_bleu - static_bleu
            })
            
        except Exception as e:
            logger.warning(f"Could not compute similarity metrics: {e}")
    
    logger.info("Static vs Dynamic comparison completed")
    return results