"""
Data Models for DynHyperRAG

This module defines the extended data models for DynHyperRAG, including
quality-related fields for hyperedges and entities.

Note: These are documentation models. The actual storage uses dictionaries
that are passed to BaseGraphStorage.upsert_node() method.
"""

from typing import TypedDict, Optional, Dict, List
from datetime import datetime


class QualityFeatures(TypedDict, total=False):
    """Quality features for hyperedge assessment."""
    degree_centrality: float  # Node degree centrality (0-1)
    betweenness: float  # Edge betweenness centrality (0-1)
    clustering: float  # Local clustering coefficient (0-1)
    coherence: float  # Hyperedge coherence score (0-1)
    text_quality: float  # Text quality score (0-1)


class HyperedgeNodeData(TypedDict, total=False):
    """
    Extended hyperedge node data schema for DynHyperRAG.
    
    Original fields (from HyperGraphRAG):
        role: Always "hyperedge"
        weight: Original LLM confidence weight
        source_id: Source document ID(s)
        hyperedge_name: The hyperedge description text
    
    New fields (for DynHyperRAG):
        quality_score: Overall quality score (0-1)
        quality_features: Dictionary of individual quality features
        dynamic_weight: Dynamically updated weight based on feedback
        feedback_count: Number of feedback signals received
        last_updated: Timestamp of last weight update
        retrieval_count: Number of times retrieved
        usage_count: Number of times used in answer generation
    """
    # Original fields
    role: str  # "hyperedge"
    weight: float  # Original LLM confidence weight
    source_id: str  # Source document ID(s), separated by GRAPH_FIELD_SEP
    hyperedge_name: str  # The hyperedge description text
    
    # Quality assessment fields (Task 1.2)
    quality_score: Optional[float]  # Overall quality score (0-1)
    quality_features: Optional[QualityFeatures]  # Individual feature scores
    
    # Dynamic update fields (Task 1.2)
    dynamic_weight: Optional[float]  # Dynamically adjusted weight
    feedback_count: Optional[int]  # Number of feedback signals
    last_updated: Optional[str]  # ISO format timestamp
    
    # Usage statistics (Task 1.2)
    retrieval_count: Optional[int]  # Times retrieved in queries
    usage_count: Optional[int]  # Times used in answer generation


class EntityNodeData(TypedDict, total=False):
    """
    Extended entity node data schema for DynHyperRAG.
    
    Original fields (from HyperGraphRAG):
        role: Always "entity"
        entity_name: The entity name
        entity_type: Entity type (e.g., "person", "organization")
        description: Entity description
        source_id: Source document ID(s)
    
    New fields (for DynHyperRAG):
        embedding_cache: Cached embedding vector (optional optimization)
    """
    # Original fields
    role: str  # "entity"
    entity_name: str  # The entity name
    entity_type: str  # Entity type classification
    description: str  # Entity description
    source_id: str  # Source document ID(s), separated by GRAPH_FIELD_SEP
    
    # Optimization fields (Task 1.2)
    embedding_cache: Optional[List[float]]  # Cached embedding vector


def create_hyperedge_node(
    hyperedge_name: str,
    weight: float,
    source_id: str,
    quality_score: Optional[float] = None,
    quality_features: Optional[Dict[str, float]] = None,
    dynamic_weight: Optional[float] = None,
) -> HyperedgeNodeData:
    """
    Create a hyperedge node data dictionary with optional quality fields.
    
    Args:
        hyperedge_name: The hyperedge description text
        weight: Original LLM confidence weight
        source_id: Source document ID(s)
        quality_score: Overall quality score (0-1)
        quality_features: Dictionary of individual quality features
        dynamic_weight: Initial dynamic weight (defaults to quality_score or weight)
    
    Returns:
        Dictionary conforming to HyperedgeNodeData schema
    """
    node_data: HyperedgeNodeData = {
        "role": "hyperedge",
        "weight": weight,
        "source_id": source_id,
        "hyperedge_name": hyperedge_name,
    }
    
    # Add quality fields if provided
    if quality_score is not None:
        node_data["quality_score"] = quality_score
    
    if quality_features is not None:
        node_data["quality_features"] = quality_features
    
    # Initialize dynamic weight
    if dynamic_weight is not None:
        node_data["dynamic_weight"] = dynamic_weight
    elif quality_score is not None:
        node_data["dynamic_weight"] = quality_score
    else:
        node_data["dynamic_weight"] = weight / 100.0  # Normalize original weight
    
    # Initialize counters
    node_data["feedback_count"] = 0
    node_data["retrieval_count"] = 0
    node_data["usage_count"] = 0
    node_data["last_updated"] = datetime.utcnow().isoformat()
    
    return node_data


def create_entity_node(
    entity_name: str,
    entity_type: str,
    description: str,
    source_id: str,
    embedding_cache: Optional[List[float]] = None,
) -> EntityNodeData:
    """
    Create an entity node data dictionary with optional embedding cache.
    
    Args:
        entity_name: The entity name
        entity_type: Entity type classification
        description: Entity description
        source_id: Source document ID(s)
        embedding_cache: Cached embedding vector (optional)
    
    Returns:
        Dictionary conforming to EntityNodeData schema
    """
    node_data: EntityNodeData = {
        "role": "entity",
        "entity_name": entity_name,
        "entity_type": entity_type,
        "description": description,
        "source_id": source_id,
    }
    
    if embedding_cache is not None:
        node_data["embedding_cache"] = embedding_cache
    
    return node_data


def update_hyperedge_quality(
    node_data: HyperedgeNodeData,
    quality_score: float,
    quality_features: Dict[str, float],
) -> HyperedgeNodeData:
    """
    Update hyperedge node data with quality assessment results.
    
    Args:
        node_data: Existing hyperedge node data
        quality_score: Computed quality score (0-1)
        quality_features: Dictionary of individual quality features
    
    Returns:
        Updated node data dictionary
    """
    node_data["quality_score"] = quality_score
    node_data["quality_features"] = quality_features
    
    # Initialize dynamic weight if not set
    if "dynamic_weight" not in node_data:
        node_data["dynamic_weight"] = quality_score
    
    node_data["last_updated"] = datetime.utcnow().isoformat()
    
    return node_data


def update_hyperedge_weight(
    node_data: HyperedgeNodeData,
    new_weight: float,
    feedback_signal: float,
) -> HyperedgeNodeData:
    """
    Update hyperedge dynamic weight based on feedback.
    
    Args:
        node_data: Existing hyperedge node data
        new_weight: New dynamic weight value
        feedback_signal: Feedback signal that triggered the update
    
    Returns:
        Updated node data dictionary
    """
    node_data["dynamic_weight"] = new_weight
    node_data["feedback_count"] = node_data.get("feedback_count", 0) + 1
    node_data["last_updated"] = datetime.utcnow().isoformat()
    
    return node_data


def increment_retrieval_count(node_data: HyperedgeNodeData) -> HyperedgeNodeData:
    """
    Increment the retrieval count for a hyperedge.
    
    Args:
        node_data: Existing hyperedge node data
    
    Returns:
        Updated node data dictionary
    """
    node_data["retrieval_count"] = node_data.get("retrieval_count", 0) + 1
    return node_data


def increment_usage_count(node_data: HyperedgeNodeData) -> HyperedgeNodeData:
    """
    Increment the usage count for a hyperedge.
    
    Args:
        node_data: Existing hyperedge node data
    
    Returns:
        Updated node data dictionary
    """
    node_data["usage_count"] = node_data.get("usage_count", 0) + 1
    return node_data


# Example usage and documentation
if __name__ == "__main__":
    # Example: Create a hyperedge with quality assessment
    hyperedge = create_hyperedge_node(
        hyperedge_name="Patient exhibits symptoms of diabetes",
        weight=85.0,
        source_id="doc_001",
        quality_score=0.82,
        quality_features={
            "degree_centrality": 0.75,
            "betweenness": 0.68,
            "clustering": 0.85,
            "coherence": 0.90,
            "text_quality": 0.92,
        },
    )
    
    print("Hyperedge node data:")
    print(hyperedge)
    
    # Example: Create an entity
    entity = create_entity_node(
        entity_name="Diabetes",
        entity_type="disease",
        description="A metabolic disorder characterized by high blood sugar",
        source_id="doc_001",
    )
    
    print("\nEntity node data:")
    print(entity)
