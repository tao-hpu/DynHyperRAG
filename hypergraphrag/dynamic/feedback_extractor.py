"""
Feedback Signal Extractor for DynHyperRAG

This module implements feedback signal extraction from LLM generation to identify
which retrieved hyperedges were actually useful. It supports multiple extraction
methods including embedding-based and citation-based approaches.

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
import re
import numpy as np
from typing import Dict, List, Optional, Callable
from difflib import SequenceMatcher

from ..utils import logger


class FeedbackExtractor:
    """
    Feedback signal extractor for hyperedges.
    
    This class extracts feedback signals from LLM-generated answers to determine
    which retrieved hyperedges contributed to the answer. It supports multiple
    extraction methods:
    
    - Embedding-based: Computes semantic similarity between answer and hyperedges
    - Citation-based: Detects if hyperedge content is referenced in the answer
    - Attention-based: Analyzes LLM attention weights (if available)
    - Hybrid: Combines embedding and citation methods
    
    Args:
        embedding_func: Embedding function that takes text list and returns embeddings
        config: Configuration dictionary with the following keys:
            - method: Extraction method ('embedding', 'citation', 'hybrid', 'attention')
            - similarity_threshold: Threshold for embedding similarity (default: 0.7)
            - citation_threshold: Threshold for fuzzy matching (default: 0.8)
            - attention_threshold: Threshold for attention weights (default: 0.1)
            - positive_feedback: Feedback value for useful hyperedges (default: 1.0)
            - negative_feedback: Feedback value for unused hyperedges (default: 0.3)
            - neutral_feedback: Feedback value for uncertain cases (default: 0.5)
    
    Example:
        >>> config = {
        ...     'method': 'embedding',
        ...     'similarity_threshold': 0.7
        ... }
        >>> extractor = FeedbackExtractor(embedding_func, config)
        >>> feedback = await extractor.extract_feedback(answer, retrieved_hyperedges)
    """
    
    def __init__(self, embedding_func: Callable, config: dict):
        """Initialize the feedback extractor."""
        self.embedding_func = embedding_func
        
        # Extraction method
        self.method = config.get('method', 'embedding')
        if self.method not in ['embedding', 'citation', 'hybrid', 'attention']:
            raise ValueError(
                f"Invalid method: {self.method}. "
                f"Must be 'embedding', 'citation', 'hybrid', or 'attention'"
            )
        
        # Thresholds
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.citation_threshold = config.get('citation_threshold', 0.8)
        self.attention_threshold = config.get('attention_threshold', 0.1)
        
        # Feedback values
        self.positive_feedback = config.get('positive_feedback', 1.0)
        self.negative_feedback = config.get('negative_feedback', 0.3)
        self.neutral_feedback = config.get('neutral_feedback', 0.5)
        
        # Cache for answer embeddings (to avoid recomputation)
        self._answer_embedding_cache = {}
        
        logger.info(
            f"FeedbackExtractor initialized with method={self.method}, "
            f"similarity_threshold={self.similarity_threshold}"
        )
    
    async def extract_feedback(
        self,
        answer: str,
        retrieved_hyperedges: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Extract feedback signals from answer and retrieved hyperedges.
        
        Args:
            answer: The generated answer text
            retrieved_hyperedges: List of retrieved hyperedge dictionaries, each containing:
                - id: Hyperedge ID
                - hyperedge: Hyperedge content/description
                - (optional) distance: Similarity score from retrieval
            metadata: Optional metadata (e.g., query, timestamp)
        
        Returns:
            Dictionary mapping hyperedge_id to feedback signal (0-1):
                - 1.0: Highly useful (referenced/similar)
                - 0.5: Neutral (uncertain)
                - 0.3: Not useful (not referenced/dissimilar)
        
        Example:
            >>> hyperedges = [
            ...     {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'},
            ...     {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'}
            ... ]
            >>> feedback = await extractor.extract_feedback(answer, hyperedges)
            >>> # feedback = {'he1': 0.85, 'he2': 0.3}
        """
        if not answer or not retrieved_hyperedges:
            logger.warning("Empty answer or no retrieved hyperedges")
            return {}
        
        # Select extraction method
        if self.method == 'embedding':
            feedback_signals = await self._embedding_based_feedback(
                answer, retrieved_hyperedges
            )
        elif self.method == 'citation':
            feedback_signals = await self._citation_based_feedback(
                answer, retrieved_hyperedges
            )
        elif self.method == 'hybrid':
            feedback_signals = await self._hybrid_feedback(
                answer, retrieved_hyperedges
            )
        elif self.method == 'attention':
            feedback_signals = await self._attention_based_feedback(
                answer, retrieved_hyperedges, metadata
            )
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # Log feedback statistics
        if feedback_signals:
            avg_feedback = sum(feedback_signals.values()) / len(feedback_signals)
            positive_count = sum(1 for v in feedback_signals.values() if v >= 0.7)
            logger.debug(
                f"Extracted feedback for {len(feedback_signals)} hyperedges: "
                f"avg={avg_feedback:.3f}, positive={positive_count}"
            )
        
        return feedback_signals
    
    async def _embedding_based_feedback(
        self,
        answer: str,
        retrieved_hyperedges: List[Dict]
    ) -> Dict[str, float]:
        """
        Extract feedback based on embedding similarity.
        
        Computes semantic similarity between the answer and each hyperedge.
        High similarity indicates the hyperedge was likely useful.
        
        Args:
            answer: Generated answer text
            retrieved_hyperedges: List of retrieved hyperedge dictionaries
        
        Returns:
            Dictionary mapping hyperedge_id to feedback signal
        """
        feedback_signals = {}
        
        try:
            # 1. Compute answer embedding (with caching)
            answer_emb = await self._get_answer_embedding(answer)
            
            # 2. Extract hyperedge texts
            hyperedge_texts = [he.get('hyperedge', '') for he in retrieved_hyperedges]
            
            # 3. Compute hyperedge embeddings in batch
            hyperedge_embs = await self.embedding_func(hyperedge_texts)
            
            # 4. Compute similarities and assign feedback
            for he, he_emb in zip(retrieved_hyperedges, hyperedge_embs):
                he_id = he.get('id', he.get('hyperedge_name', ''))
                
                if not he_id:
                    logger.warning(f"Hyperedge missing ID: {he}")
                    continue
                
                # Compute cosine similarity
                similarity = self._cosine_similarity(answer_emb, he_emb)
                
                # Convert similarity to feedback signal
                if similarity >= self.similarity_threshold:
                    # High similarity -> positive feedback
                    # Scale from threshold to 1.0 -> positive_feedback to 1.0
                    normalized_sim = (similarity - self.similarity_threshold) / (1.0 - self.similarity_threshold)
                    feedback = self.positive_feedback + normalized_sim * (1.0 - self.positive_feedback)
                else:
                    # Low similarity -> negative feedback
                    # Scale from 0 to threshold -> negative_feedback to neutral_feedback
                    normalized_sim = similarity / self.similarity_threshold
                    feedback = self.negative_feedback + normalized_sim * (self.neutral_feedback - self.negative_feedback)
                
                feedback_signals[he_id] = feedback
                
                logger.debug(
                    f"Embedding feedback for {he_id}: similarity={similarity:.3f}, "
                    f"feedback={feedback:.3f}"
                )
        
        except Exception as e:
            logger.error(f"Embedding-based feedback extraction failed: {e}")
            # Return neutral feedback for all hyperedges
            for he in retrieved_hyperedges:
                he_id = he.get('id', he.get('hyperedge_name', ''))
                if he_id:
                    feedback_signals[he_id] = self.neutral_feedback
        
        return feedback_signals
    
    async def _citation_based_feedback(
        self,
        answer: str,
        retrieved_hyperedges: List[Dict]
    ) -> Dict[str, float]:
        """
        Extract feedback based on citation detection.
        
        Detects if hyperedge content is referenced in the answer using
        fuzzy text matching. This is more interpretable but less robust
        than embedding-based methods.
        
        Args:
            answer: Generated answer text
            retrieved_hyperedges: List of retrieved hyperedge dictionaries
        
        Returns:
            Dictionary mapping hyperedge_id to feedback signal
        """
        feedback_signals = {}
        
        # Normalize answer for matching
        answer_lower = answer.lower()
        answer_normalized = self._normalize_text(answer)
        
        for he in retrieved_hyperedges:
            he_id = he.get('id', he.get('hyperedge_name', ''))
            he_text = he.get('hyperedge', '')
            
            if not he_id or not he_text:
                continue
            
            # Normalize hyperedge text
            he_normalized = self._normalize_text(he_text)
            
            # Method 1: Exact substring match (case-insensitive)
            if he_text.lower() in answer_lower:
                feedback_signals[he_id] = self.positive_feedback
                logger.debug(f"Citation feedback for {he_id}: exact match -> {self.positive_feedback}")
                continue
            
            # Method 2: Fuzzy matching for partial matches
            # Check if significant portions of hyperedge appear in answer
            fuzzy_score = self._fuzzy_match_score(he_normalized, answer_normalized)
            
            if fuzzy_score >= self.citation_threshold:
                # Strong fuzzy match -> positive feedback
                feedback = self.positive_feedback * fuzzy_score
                feedback_signals[he_id] = feedback
                logger.debug(
                    f"Citation feedback for {he_id}: fuzzy match "
                    f"score={fuzzy_score:.3f} -> {feedback:.3f}"
                )
            else:
                # No match -> negative feedback
                feedback_signals[he_id] = self.negative_feedback
                logger.debug(
                    f"Citation feedback for {he_id}: no match -> {self.negative_feedback}"
                )
        
        return feedback_signals
    
    async def _hybrid_feedback(
        self,
        answer: str,
        retrieved_hyperedges: List[Dict]
    ) -> Dict[str, float]:
        """
        Extract feedback using hybrid approach.
        
        Combines embedding-based and citation-based methods:
        - If citation detected: Use positive feedback
        - Otherwise: Use embedding similarity
        
        This provides the interpretability of citation-based methods
        with the robustness of embedding-based methods.
        
        Args:
            answer: Generated answer text
            retrieved_hyperedges: List of retrieved hyperedge dictionaries
        
        Returns:
            Dictionary mapping hyperedge_id to feedback signal
        """
        # Get feedback from both methods
        embedding_feedback = await self._embedding_based_feedback(
            answer, retrieved_hyperedges
        )
        citation_feedback = await self._citation_based_feedback(
            answer, retrieved_hyperedges
        )
        
        # Combine: Use citation if positive, otherwise use embedding
        hybrid_feedback = {}
        
        for he in retrieved_hyperedges:
            he_id = he.get('id', he.get('hyperedge_name', ''))
            
            if not he_id:
                continue
            
            citation_score = citation_feedback.get(he_id, self.neutral_feedback)
            embedding_score = embedding_feedback.get(he_id, self.neutral_feedback)
            
            # If citation detected (high score), trust it
            if citation_score >= 0.7:
                hybrid_feedback[he_id] = citation_score
                logger.debug(
                    f"Hybrid feedback for {he_id}: citation={citation_score:.3f} (used)"
                )
            else:
                # Otherwise, use embedding similarity
                hybrid_feedback[he_id] = embedding_score
                logger.debug(
                    f"Hybrid feedback for {he_id}: embedding={embedding_score:.3f} (used)"
                )
        
        return hybrid_feedback
    
    async def _attention_based_feedback(
        self,
        answer: str,
        retrieved_hyperedges: List[Dict],
        metadata: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Extract feedback based on LLM attention weights.
        
        This method analyzes the attention distribution from the LLM to determine
        which retrieved hyperedges contributed most to the generated answer.
        
        Note: This requires the LLM to support outputting attention weights.
        If attention weights are not available in metadata, falls back to
        embedding-based feedback.
        
        Args:
            answer: Generated answer text
            retrieved_hyperedges: List of retrieved hyperedge dictionaries
            metadata: Optional metadata containing attention weights:
                - attention_weights: Dict mapping context position to attention score
                - context_mapping: Dict mapping hyperedge_id to context positions
                OR
                - hyperedge_attention: Dict mapping hyperedge_id to attention score
        
        Returns:
            Dictionary mapping hyperedge_id to feedback signal
        
        Example metadata format:
            {
                'attention_weights': {0: 0.15, 1: 0.25, 2: 0.10, ...},
                'context_mapping': {'he1': [0, 1], 'he2': [2, 3], ...}
            }
            OR
            {
                'hyperedge_attention': {'he1': 0.35, 'he2': 0.15, ...}
            }
        """
        feedback_signals = {}
        
        # Check if attention weights are available
        if not metadata:
            logger.warning(
                "Attention-based feedback requested but no metadata provided. "
                "Falling back to embedding-based feedback."
            )
            return await self._embedding_based_feedback(answer, retrieved_hyperedges)
        
        # Method 1: Direct hyperedge attention scores
        if 'hyperedge_attention' in metadata:
            hyperedge_attention = metadata['hyperedge_attention']
            
            for he in retrieved_hyperedges:
                he_id = he.get('id', he.get('hyperedge_name', ''))
                
                if not he_id:
                    continue
                
                # Get attention score for this hyperedge
                attention_score = hyperedge_attention.get(he_id, 0.0)
                
                # Convert attention score to feedback signal
                feedback = self._attention_to_feedback(attention_score)
                feedback_signals[he_id] = feedback
                
                logger.debug(
                    f"Attention feedback for {he_id}: "
                    f"attention={attention_score:.3f}, feedback={feedback:.3f}"
                )
            
            return feedback_signals
        
        # Method 2: Attention weights with context mapping
        if 'attention_weights' in metadata and 'context_mapping' in metadata:
            attention_weights = metadata['attention_weights']
            context_mapping = metadata['context_mapping']
            
            for he in retrieved_hyperedges:
                he_id = he.get('id', he.get('hyperedge_name', ''))
                
                if not he_id:
                    continue
                
                # Get context positions for this hyperedge
                positions = context_mapping.get(he_id, [])
                
                if not positions:
                    # No context positions -> no attention
                    feedback_signals[he_id] = self.negative_feedback
                    continue
                
                # Aggregate attention across all positions for this hyperedge
                total_attention = sum(
                    attention_weights.get(pos, 0.0) for pos in positions
                )
                
                # Normalize by number of positions (average attention)
                avg_attention = total_attention / len(positions) if positions else 0.0
                
                # Convert attention score to feedback signal
                feedback = self._attention_to_feedback(avg_attention)
                feedback_signals[he_id] = feedback
                
                logger.debug(
                    f"Attention feedback for {he_id}: "
                    f"positions={len(positions)}, avg_attention={avg_attention:.3f}, "
                    f"feedback={feedback:.3f}"
                )
            
            return feedback_signals
        
        # Method 3: Analyze attention distribution from raw attention matrix
        if 'attention_matrix' in metadata and 'context_texts' in metadata:
            attention_matrix = metadata['attention_matrix']  # Shape: [layers, heads, seq_len, seq_len]
            context_texts = metadata['context_texts']  # List of context text chunks
            
            # Aggregate attention across layers and heads (average)
            # Focus on attention from answer tokens to context tokens
            aggregated_attention = self._aggregate_attention_matrix(
                attention_matrix, metadata
            )
            
            # Map context texts to hyperedges
            for he in retrieved_hyperedges:
                he_id = he.get('id', he.get('hyperedge_name', ''))
                he_text = he.get('hyperedge', '')
                
                if not he_id or not he_text:
                    continue
                
                # Find which context chunks correspond to this hyperedge
                attention_score = self._match_hyperedge_to_attention(
                    he_text, context_texts, aggregated_attention
                )
                
                # Convert attention score to feedback signal
                feedback = self._attention_to_feedback(attention_score)
                feedback_signals[he_id] = feedback
                
                logger.debug(
                    f"Attention feedback for {he_id}: "
                    f"attention={attention_score:.3f}, feedback={feedback:.3f}"
                )
            
            return feedback_signals
        
        # No valid attention data found
        logger.warning(
            "Attention-based feedback requested but no valid attention data found. "
            "Expected 'hyperedge_attention', 'attention_weights' + 'context_mapping', "
            "or 'attention_matrix' + 'context_texts' in metadata. "
            "Falling back to embedding-based feedback."
        )
        return await self._embedding_based_feedback(answer, retrieved_hyperedges)
    
    def _attention_to_feedback(self, attention_score: float) -> float:
        """
        Convert attention score to feedback signal.
        
        Maps attention scores to feedback values using a threshold-based approach:
        - High attention (>= threshold) -> positive feedback
        - Low attention (< threshold) -> negative feedback
        
        Args:
            attention_score: Attention score (typically 0-1, but can be unnormalized)
        
        Returns:
            Feedback signal (0-1)
        """
        # Normalize attention score if needed (clip to [0, 1])
        attention_score = max(0.0, min(1.0, attention_score))
        
        if attention_score >= self.attention_threshold:
            # High attention -> positive feedback
            # Scale from threshold to 1.0 -> positive_feedback to 1.0
            normalized_attention = (attention_score - self.attention_threshold) / (
                1.0 - self.attention_threshold
            )
            feedback = self.positive_feedback + normalized_attention * (
                1.0 - self.positive_feedback
            )
        else:
            # Low attention -> negative feedback
            # Scale from 0 to threshold -> negative_feedback to neutral_feedback
            normalized_attention = attention_score / self.attention_threshold
            feedback = self.negative_feedback + normalized_attention * (
                self.neutral_feedback - self.negative_feedback
            )
        
        return feedback
    
    def _aggregate_attention_matrix(
        self,
        attention_matrix: np.ndarray,
        metadata: Dict
    ) -> np.ndarray:
        """
        Aggregate attention matrix across layers and heads.
        
        Args:
            attention_matrix: Attention matrix with shape [layers, heads, seq_len, seq_len]
                             or [heads, seq_len, seq_len] or [seq_len, seq_len]
            metadata: Metadata containing additional info (e.g., answer_start_pos)
        
        Returns:
            Aggregated attention vector for context tokens
        """
        # Convert to numpy array if needed
        if not isinstance(attention_matrix, np.ndarray):
            attention_matrix = np.array(attention_matrix)
        
        # Handle different attention matrix shapes
        if attention_matrix.ndim == 4:
            # [layers, heads, seq_len, seq_len] -> average across layers and heads
            attention_matrix = attention_matrix.mean(axis=(0, 1))
        elif attention_matrix.ndim == 3:
            # [heads, seq_len, seq_len] -> average across heads
            attention_matrix = attention_matrix.mean(axis=0)
        elif attention_matrix.ndim == 2:
            # [seq_len, seq_len] -> already aggregated
            pass
        else:
            logger.error(f"Unexpected attention matrix shape: {attention_matrix.shape}")
            return np.array([])
        
        # Extract attention from answer tokens to context tokens
        # Assume answer tokens are at the end of the sequence
        answer_start_pos = metadata.get('answer_start_pos', attention_matrix.shape[0] // 2)
        context_end_pos = metadata.get('context_end_pos', answer_start_pos)
        
        # Average attention from answer tokens to each context token
        answer_attention = attention_matrix[answer_start_pos:, :context_end_pos]
        aggregated_attention = answer_attention.mean(axis=0)
        
        return aggregated_attention
    
    def _match_hyperedge_to_attention(
        self,
        hyperedge_text: str,
        context_texts: List[str],
        attention_scores: np.ndarray
    ) -> float:
        """
        Match hyperedge text to context chunks and aggregate attention.
        
        Args:
            hyperedge_text: Hyperedge content text
            context_texts: List of context text chunks
            attention_scores: Attention scores for each context chunk
        
        Returns:
            Aggregated attention score for this hyperedge
        """
        if len(context_texts) != len(attention_scores):
            logger.warning(
                f"Mismatch between context_texts ({len(context_texts)}) "
                f"and attention_scores ({len(attention_scores)})"
            )
            return 0.0
        
        # Normalize hyperedge text
        he_normalized = self._normalize_text(hyperedge_text)
        
        # Find matching context chunks
        matching_scores = []
        for i, context_text in enumerate(context_texts):
            context_normalized = self._normalize_text(context_text)
            
            # Check if hyperedge text appears in this context chunk
            if he_normalized in context_normalized or context_normalized in he_normalized:
                matching_scores.append(attention_scores[i])
            else:
                # Use fuzzy matching for partial matches
                fuzzy_score = self._fuzzy_match_score(he_normalized, context_normalized)
                if fuzzy_score >= 0.6:  # Lower threshold for context matching
                    matching_scores.append(attention_scores[i] * fuzzy_score)
        
        # Aggregate attention from matching chunks
        if matching_scores:
            return float(np.mean(matching_scores))
        else:
            return 0.0
    
    async def _get_answer_embedding(self, answer: str) -> np.ndarray:
        """
        Get answer embedding with caching.
        
        Args:
            answer: Answer text
        
        Returns:
            Answer embedding as numpy array
        """
        # Use hash as cache key
        cache_key = hash(answer)
        
        if cache_key in self._answer_embedding_cache:
            return self._answer_embedding_cache[cache_key]
        
        # Compute embedding
        embeddings = await self.embedding_func([answer])
        answer_emb = embeddings[0]
        
        # Convert to numpy array if needed
        if not isinstance(answer_emb, np.ndarray):
            answer_emb = np.array(answer_emb)
        
        # Cache it
        self._answer_embedding_cache[cache_key] = answer_emb
        
        # Limit cache size
        if len(self._answer_embedding_cache) > 100:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._answer_embedding_cache))
            del self._answer_embedding_cache[oldest_key]
        
        return answer_emb
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity (0-1, normalized from -1 to 1)
        """
        # Ensure numpy arrays
        v1 = np.array(vec1) if not isinstance(vec1, np.ndarray) else vec1
        v2 = np.array(vec2) if not isinstance(vec2, np.ndarray) else vec2
        
        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Normalize to [0, 1] range
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize text for matching.
        
        - Convert to lowercase
        - Remove extra whitespace
        - Remove punctuation
        
        Args:
            text: Input text
        
        Returns:
            Normalized text
        """
        # Lowercase
        text = text.lower()
        
        # Remove punctuation (keep alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def _fuzzy_match_score(text1: str, text2: str) -> float:
        """
        Compute fuzzy matching score between two texts.
        
        Uses SequenceMatcher to find the longest common subsequence ratio.
        
        Args:
            text1: First text (typically shorter, e.g., hyperedge)
            text2: Second text (typically longer, e.g., answer)
        
        Returns:
            Fuzzy match score (0-1)
        """
        # Use SequenceMatcher for fuzzy matching
        matcher = SequenceMatcher(None, text1, text2)
        ratio = matcher.ratio()
        
        # Also check if text1 is a substring of text2 (after normalization)
        if text1 in text2:
            # Boost score if it's a substring
            ratio = max(ratio, 0.8)
        
        return ratio
    
    async def batch_extract_feedback(
        self,
        answers: List[str],
        retrieved_hyperedges_list: List[List[Dict]],
        metadata_list: Optional[List[Dict]] = None
    ) -> List[Dict[str, float]]:
        """
        Batch extract feedback for multiple queries.
        
        Args:
            answers: List of generated answers
            retrieved_hyperedges_list: List of retrieved hyperedge lists
            metadata_list: Optional list of metadata dictionaries
        
        Returns:
            List of feedback signal dictionaries
        
        Example:
            >>> answers = ["Answer 1", "Answer 2"]
            >>> hyperedges_list = [
            ...     [{'id': 'he1', 'hyperedge': 'text1'}],
            ...     [{'id': 'he2', 'hyperedge': 'text2'}]
            ... ]
            >>> feedback_list = await extractor.batch_extract_feedback(
            ...     answers, hyperedges_list
            ... )
        """
        if metadata_list is None:
            metadata_list = [None] * len(answers)
        
        # Parallel extraction
        tasks = [
            self.extract_feedback(answer, hyperedges, metadata)
            for answer, hyperedges, metadata in zip(
                answers, retrieved_hyperedges_list, metadata_list
            )
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        feedback_list = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch feedback extraction failed for item {i}: {result}")
                feedback_list.append({})
            else:
                feedback_list.append(result)
        
        return feedback_list
    
    def clear_cache(self):
        """Clear answer embedding cache."""
        self._answer_embedding_cache.clear()
        logger.info("Cleared answer embedding cache")
    
    def get_cache_size(self) -> int:
        """Get answer embedding cache size."""
        return len(self._answer_embedding_cache)
    
    def get_statistics(self) -> Dict:
        """
        Get extractor statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'method': self.method,
            'similarity_threshold': self.similarity_threshold,
            'citation_threshold': self.citation_threshold,
            'attention_threshold': self.attention_threshold,
            'cache_size': len(self._answer_embedding_cache),
            'positive_feedback': self.positive_feedback,
            'negative_feedback': self.negative_feedback,
            'neutral_feedback': self.neutral_feedback,
        }


# Helper functions

def compute_feedback_statistics(feedback_signals: Dict[str, float]) -> Dict:
    """
    Compute statistics for feedback signals.
    
    Args:
        feedback_signals: Dictionary mapping hyperedge_id to feedback signal
    
    Returns:
        Statistics dictionary
    """
    if not feedback_signals:
        return {}
    
    values = list(feedback_signals.values())
    
    return {
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'median': float(np.median(values)),
        'count': len(values),
        'positive_count': sum(1 for v in values if v >= 0.7),
        'negative_count': sum(1 for v in values if v < 0.5),
        'neutral_count': sum(1 for v in values if 0.5 <= v < 0.7),
    }


def analyze_feedback_distribution(
    feedback_signals_list: List[Dict[str, float]]
) -> Dict:
    """
    Analyze feedback distribution across multiple queries.
    
    Args:
        feedback_signals_list: List of feedback signal dictionaries
    
    Returns:
        Distribution analysis dictionary
    """
    all_values = []
    for feedback_signals in feedback_signals_list:
        all_values.extend(feedback_signals.values())
    
    if not all_values:
        return {}
    
    return {
        'total_feedbacks': len(all_values),
        'mean': float(np.mean(all_values)),
        'std': float(np.std(all_values)),
        'min': float(np.min(all_values)),
        'max': float(np.max(all_values)),
        'median': float(np.median(all_values)),
        'q25': float(np.percentile(all_values, 25)),
        'q75': float(np.percentile(all_values, 75)),
        'positive_ratio': sum(1 for v in all_values if v >= 0.7) / len(all_values),
        'negative_ratio': sum(1 for v in all_values if v < 0.5) / len(all_values),
        'neutral_ratio': sum(1 for v in all_values if 0.5 <= v < 0.7) / len(all_values),
    }
