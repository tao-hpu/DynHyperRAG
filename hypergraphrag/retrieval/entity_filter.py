"""
Entity Type Filter for Efficient Retrieval

This module implements entity type filtering to reduce search space during retrieval.
It identifies relevant entity types from queries and filters hyperedges based on
the types of entities they connect.

Key Features:
- Keyword-based entity type identification
- Domain-specific entity taxonomies (medical, legal, academic)
- Hyperedge filtering by connected entity types
- Search space reduction metrics

Usage:
    from hypergraphrag.retrieval.entity_filter import EntityTypeFilter
    
    filter = EntityTypeFilter(graph, config)
    relevant_types = await filter.identify_relevant_types(query)
    filtered_ids = await filter.filter_hyperedges_by_type(hyperedge_ids, relevant_types)
"""

import asyncio
import logging
from typing import Optional
from hypergraphrag.base import BaseGraphStorage

logger = logging.getLogger(__name__)


class EntityTypeFilter:
    """
    Entity type filter for efficient hyperedge retrieval.
    
    This class implements entity type filtering to narrow the search space
    during retrieval by identifying relevant entity types from queries and
    filtering hyperedges based on the types of entities they connect.
    
    Attributes:
        graph: BaseGraphStorage instance for accessing graph data
        entity_taxonomy: Dict mapping domains to entity type lists
        domain: Current domain (medical, legal, academic)
        use_llm_classification: Whether to use LLM for type identification
        llm_model_func: Optional LLM function for advanced type classification
    """
    
    def __init__(
        self,
        graph: BaseGraphStorage,
        config: dict,
        llm_model_func: Optional[callable] = None
    ):
        """
        Initialize EntityTypeFilter.
        
        Args:
            graph: BaseGraphStorage instance
            config: Configuration dict with keys:
                - entity_taxonomy: Dict[str, List[str]] - domain to entity types mapping
                - domain: str - current domain (medical, legal, academic)
                - use_llm_classification: bool - whether to use LLM (default: False)
            llm_model_func: Optional LLM function for type classification
        """
        self.graph = graph
        self.entity_taxonomy = config.get("entity_taxonomy", {
            "medical": ["disease", "symptom", "treatment", "medication", "procedure", "anatomy"],
            "legal": ["law", "article", "court", "party", "crime", "penalty"],
            "academic": ["paper", "author", "institution", "keyword", "conference"]
        })
        self.domain = config.get("domain", "medical")
        self.use_llm_classification = config.get("use_llm_classification", False)
        self.llm_model_func = llm_model_func
        
        # Validate domain
        if self.domain not in self.entity_taxonomy:
            logger.warning(
                f"Domain '{self.domain}' not in taxonomy. "
                f"Available domains: {list(self.entity_taxonomy.keys())}"
            )
            # Use first available domain as fallback
            self.domain = list(self.entity_taxonomy.keys())[0]
            logger.info(f"Using fallback domain: {self.domain}")
        
        logger.info(
            f"EntityTypeFilter initialized for domain '{self.domain}' "
            f"with {len(self.entity_taxonomy[self.domain])} entity types"
        )
    
    async def identify_relevant_types(self, query: str) -> list[str]:
        """
        Identify relevant entity types from a query.
        
        This method uses keyword matching to identify which entity types
        are relevant to the query. If no types are identified, it can
        optionally use LLM-based classification or return all types.
        
        Args:
            query: Query string
            
        Returns:
            List of relevant entity type strings
            
        Example:
            >>> filter = EntityTypeFilter(graph, {"domain": "legal"})
            >>> types = await filter.identify_relevant_types("What is the penalty for theft?")
            >>> print(types)
            ['crime', 'penalty']
        """
        relevant_types = []
        query_lower = query.lower()
        
        # Method 1: Keyword-based matching
        for entity_type in self.entity_taxonomy[self.domain]:
            # Check if entity type appears in query
            if entity_type.lower() in query_lower:
                relevant_types.append(entity_type)
                logger.debug(f"Matched entity type '{entity_type}' in query")
        
        # Method 2: LLM-based classification (optional)
        if not relevant_types and self.use_llm_classification and self.llm_model_func:
            try:
                relevant_types = await self._llm_classify_types(query)
                logger.info(f"LLM identified types: {relevant_types}")
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")
        
        # Fallback: If no types identified, return all types
        if not relevant_types:
            relevant_types = self.entity_taxonomy[self.domain]
            logger.debug(
                f"No specific types identified, using all {len(relevant_types)} types"
            )
        
        logger.info(
            f"Identified {len(relevant_types)} relevant types for query: {relevant_types}"
        )
        return relevant_types
    
    async def _llm_classify_types(self, query: str) -> list[str]:
        """
        Use LLM to classify relevant entity types from query.
        
        This is an optional advanced method that uses an LLM to identify
        which entity types are relevant to the query. The LLM analyzes
        the query semantically and determines which entity types would
        be most useful for answering it.
        
        Args:
            query: Query string
            
        Returns:
            List of relevant entity type strings
            
        Example:
            >>> filter = EntityTypeFilter(graph, config, llm_model_func=llm_func)
            >>> types = await filter._llm_classify_types("What medication treats diabetes?")
            >>> print(types)
            ['medication', 'disease', 'treatment']
        """
        if not self.llm_model_func:
            logger.warning("LLM classification requested but llm_model_func not provided")
            return []
        
        # Construct prompt for LLM
        entity_types_str = ", ".join(self.entity_taxonomy[self.domain])
        
        system_prompt = """You are an expert at analyzing queries and identifying relevant entity types.
Your task is to determine which entity types are most relevant for answering a given query.
Be precise and only select types that are directly relevant to the query."""
        
        prompt = f"""Analyze the following query and identify which entity types are most relevant for answering it.

Query: "{query}"

Available entity types in the {self.domain} domain: {entity_types_str}

Instructions:
1. Consider what information would be needed to answer the query
2. Select only the entity types that are directly relevant
3. If multiple types are relevant, include all of them
4. Return ONLY the entity types as a comma-separated list, nothing else

Relevant entity types:"""
        
        try:
            # Call LLM with the prompt
            response = await self.llm_model_func(
                prompt,
                system_prompt=system_prompt,
                hashing_kv=None  # No caching for this operation
            )
            
            logger.debug(f"LLM response for type classification: {response}")
            
            # Parse response - expect comma-separated types
            # Clean up the response (remove quotes, extra whitespace, etc.)
            response = response.strip().strip('"').strip("'")
            
            # Split by comma and clean each type
            identified_types = [t.strip().lower() for t in response.split(",") if t.strip()]
            
            # Filter to only valid types (case-insensitive matching)
            entity_types_lower = [et.lower() for et in self.entity_taxonomy[self.domain]]
            valid_types = []
            
            for identified_type in identified_types:
                # Try exact match first
                if identified_type in entity_types_lower:
                    # Get the original case version
                    idx = entity_types_lower.index(identified_type)
                    valid_types.append(self.entity_taxonomy[self.domain][idx])
                else:
                    # Try partial match (e.g., "medications" -> "medication")
                    for i, et in enumerate(entity_types_lower):
                        if et in identified_type or identified_type in et:
                            valid_types.append(self.entity_taxonomy[self.domain][i])
                            break
            
            # Remove duplicates while preserving order
            valid_types = list(dict.fromkeys(valid_types))
            
            if valid_types:
                logger.info(
                    f"LLM identified {len(valid_types)} relevant types: {valid_types}"
                )
            else:
                logger.warning(
                    f"LLM response '{response}' did not match any valid entity types. "
                    f"Available types: {self.entity_taxonomy[self.domain]}"
                )
            
            return valid_types
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}", exc_info=True)
            return []
    
    async def filter_hyperedges_by_type(
        self,
        hyperedge_ids: list[str],
        relevant_types: list[str]
    ) -> tuple[list[str], dict]:
        """
        Filter hyperedges by entity types they connect.
        
        This method filters hyperedges to only keep those that connect
        entities of relevant types. It also returns statistics about
        the filtering process.
        
        Args:
            hyperedge_ids: List of hyperedge node IDs to filter
            relevant_types: List of relevant entity type strings
            
        Returns:
            Tuple of (filtered_hyperedge_ids, statistics_dict)
            
            statistics_dict contains:
                - original_count: Number of input hyperedges
                - filtered_count: Number of hyperedges after filtering
                - reduction_rate: Percentage of search space reduction
                - types_used: Entity types that were matched
                
        Example:
            >>> filtered_ids, stats = await filter.filter_hyperedges_by_type(
            ...     hyperedge_ids, ["crime", "penalty"]
            ... )
            >>> print(f"Reduced search space by {stats['reduction_rate']:.1f}%")
        """
        if not hyperedge_ids:
            return [], {
                "original_count": 0,
                "filtered_count": 0,
                "reduction_rate": 0.0,
                "types_used": []
            }
        
        original_count = len(hyperedge_ids)
        filtered_ids = []
        types_matched = set()
        
        # Convert relevant types to lowercase for case-insensitive matching
        relevant_types_lower = [t.lower() for t in relevant_types]
        
        logger.info(
            f"Filtering {original_count} hyperedges by types: {relevant_types}"
        )
        
        # Process hyperedges in batches for efficiency
        batch_size = 50
        for i in range(0, len(hyperedge_ids), batch_size):
            batch = hyperedge_ids[i:i + batch_size]
            batch_results = await self._filter_batch(batch, relevant_types_lower)
            
            for he_id, matched, matched_types in batch_results:
                if matched:
                    filtered_ids.append(he_id)
                    types_matched.update(matched_types)
        
        filtered_count = len(filtered_ids)
        reduction_rate = (
            (original_count - filtered_count) / original_count * 100
            if original_count > 0 else 0.0
        )
        
        statistics = {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "reduction_rate": reduction_rate,
            "types_used": sorted(list(types_matched))
        }
        
        logger.info(
            f"Filtered to {filtered_count}/{original_count} hyperedges "
            f"({reduction_rate:.1f}% reduction). "
            f"Matched types: {statistics['types_used']}"
        )
        
        return filtered_ids, statistics
    
    async def _filter_batch(
        self,
        hyperedge_ids: list[str],
        relevant_types_lower: list[str]
    ) -> list[tuple[str, bool, set]]:
        """
        Filter a batch of hyperedges.
        
        Args:
            hyperedge_ids: Batch of hyperedge IDs
            relevant_types_lower: Lowercase relevant entity types
            
        Returns:
            List of tuples (hyperedge_id, is_matched, matched_types)
        """
        results = []
        
        for he_id in hyperedge_ids:
            try:
                # Get edges connected to this hyperedge
                edges = await self.graph.get_node_edges(he_id)
                
                if not edges:
                    # No edges means no entities, skip this hyperedge
                    results.append((he_id, False, set()))
                    continue
                
                # Extract entity IDs (edges are tuples of (source, target))
                # In bipartite graph: hyperedge connects to entities
                entity_ids = [e[1] for e in edges]
                
                # Get entity nodes to check their types
                entity_nodes = await asyncio.gather(
                    *[self.graph.get_node(eid) for eid in entity_ids],
                    return_exceptions=True
                )
                
                # Check if any entity has a relevant type
                matched = False
                matched_types = set()
                
                for entity_node in entity_nodes:
                    if isinstance(entity_node, Exception) or entity_node is None:
                        continue
                    
                    entity_type = entity_node.get("entity_type", "").lower()
                    
                    if entity_type in relevant_types_lower:
                        matched = True
                        matched_types.add(entity_type)
                
                results.append((he_id, matched, matched_types))
                
            except Exception as e:
                logger.warning(f"Error filtering hyperedge {he_id}: {e}")
                # On error, include the hyperedge to be safe
                results.append((he_id, True, set()))
        
        return results
    
    def get_domain_types(self, domain: Optional[str] = None) -> list[str]:
        """
        Get entity types for a specific domain.
        
        Args:
            domain: Domain name (if None, uses current domain)
            
        Returns:
            List of entity type strings for the domain
        """
        domain = domain or self.domain
        return self.entity_taxonomy.get(domain, [])
    
    def set_domain(self, domain: str):
        """
        Change the current domain.
        
        Args:
            domain: New domain name
            
        Raises:
            ValueError: If domain is not in taxonomy
        """
        if domain not in self.entity_taxonomy:
            raise ValueError(
                f"Domain '{domain}' not in taxonomy. "
                f"Available: {list(self.entity_taxonomy.keys())}"
            )
        
        self.domain = domain
        logger.info(f"Domain changed to: {domain}")
    
    def add_entity_type(self, domain: str, entity_type: str):
        """
        Add a new entity type to a domain's taxonomy.
        
        Args:
            domain: Domain name
            entity_type: Entity type to add
        """
        if domain not in self.entity_taxonomy:
            self.entity_taxonomy[domain] = []
        
        if entity_type not in self.entity_taxonomy[domain]:
            self.entity_taxonomy[domain].append(entity_type)
            logger.info(f"Added entity type '{entity_type}' to domain '{domain}'")
