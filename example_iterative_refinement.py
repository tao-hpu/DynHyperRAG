"""
Example: Iterative Hyperedge Refinement

This example demonstrates how to use the iterative refinement mechanism
to improve low-quality hyperedges by triggering re-extraction with improved prompts.

The iterative refinement process:
1. Identifies low-quality hyperedges
2. Retrieves source text chunks
3. Re-extracts hyperedges using improved prompts with feedback
4. Compares quality scores
5. Replaces hyperedges if quality improves

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
import os
from hypergraphrag import HyperGraphRAG
from hypergraphrag.dynamic.refiner import HyperedgeRefiner
from hypergraphrag.quality.scorer import QualityScorer


async def main():
    """Demonstrate iterative hyperedge refinement."""
    
    print("=" * 80)
    print("Iterative Hyperedge Refinement Example")
    print("=" * 80)
    
    # Initialize HyperGraphRAG
    print("\n1. Initializing HyperGraphRAG system...")
    
    working_dir = "./example_iterative_refinement_workspace"
    os.makedirs(working_dir, exist_ok=True)
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_llm_cache=True,
    )
    
    # Sample documents for testing
    documents = [
        "Alice works at TechCorp as a software engineer. She collaborates with Bob on AI projects.",
        "Bob is a data scientist at TechCorp. He specializes in machine learning and works with Alice.",
        "TechCorp is a technology company founded in 2020. It focuses on AI and machine learning solutions.",
    ]
    
    print(f"\n2. Inserting {len(documents)} documents...")
    await rag.insert(documents)
    
    print("\n3. Computing quality scores for all hyperedges...")
    
    # Get all hyperedges
    all_nodes = []
    async for node_id in rag.knowledge_graph_inst.index_done_callback():
        node = await rag.knowledge_graph_inst.get_node(node_id)
        if node and node.get('role') == 'hyperedge':
            all_nodes.append(node_id)
    
    print(f"   Found {len(all_nodes)} hyperedges")
    
    # Initialize quality scorer
    quality_config = {
        'feature_weights': {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        }
    }
    
    quality_scorer = QualityScorer(
        rag.knowledge_graph_inst,
        quality_config
    )
    
    # Compute quality scores
    quality_scores = {}
    for he_id in all_nodes:
        try:
            result = await quality_scorer.compute_quality_score(he_id)
            quality_scores[he_id] = result['quality_score']
            
            # Update node with quality score
            node = await rag.knowledge_graph_inst.get_node(he_id)
            node['quality_score'] = result['quality_score']
            node['quality_features'] = result['features']
            await rag.knowledge_graph_inst.upsert_node(he_id, node)
            
        except Exception as e:
            print(f"   Warning: Failed to compute quality for {he_id}: {e}")
            quality_scores[he_id] = 0.5
    
    # Display quality distribution
    if quality_scores:
        avg_quality = sum(quality_scores.values()) / len(quality_scores)
        min_quality = min(quality_scores.values())
        max_quality = max(quality_scores.values())
        
        print(f"\n   Quality distribution:")
        print(f"   - Average: {avg_quality:.3f}")
        print(f"   - Min: {min_quality:.3f}")
        print(f"   - Max: {max_quality:.3f}")
        
        # Show quality breakdown
        low_quality = sum(1 for q in quality_scores.values() if q < 0.4)
        medium_quality = sum(1 for q in quality_scores.values() if 0.4 <= q < 0.7)
        high_quality = sum(1 for q in quality_scores.values() if q >= 0.7)
        
        print(f"   - Low quality (<0.4): {low_quality}")
        print(f"   - Medium quality (0.4-0.7): {medium_quality}")
        print(f"   - High quality (≥0.7): {high_quality}")
    
    print("\n4. Identifying low-quality hyperedges for refinement...")
    
    # Initialize refiner with low threshold to catch low-quality hyperedges
    refiner_config = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    
    refiner = HyperedgeRefiner(
        rag.knowledge_graph_inst,
        refiner_config
    )
    
    # Identify low-quality hyperedges
    low_quality_ids = [
        he_id for he_id, quality in quality_scores.items()
        if quality < 0.5
    ]
    
    print(f"   Found {len(low_quality_ids)} low-quality hyperedges")
    
    if not low_quality_ids:
        print("\n   No low-quality hyperedges found. Creating a synthetic example...")
        
        # For demonstration, artificially lower quality of first hyperedge
        if all_nodes:
            demo_id = all_nodes[0]
            node = await rag.knowledge_graph_inst.get_node(demo_id)
            node['quality_score'] = 0.3
            await rag.knowledge_graph_inst.upsert_node(demo_id, node)
            low_quality_ids = [demo_id]
            print(f"   Artificially lowered quality of {demo_id} to 0.3")
    
    if low_quality_ids:
        print(f"\n5. Performing iterative refinement on {len(low_quality_ids)} hyperedges...")
        print("   This will:")
        print("   - Retrieve source text for each hyperedge")
        print("   - Re-extract using improved prompts with quality feedback")
        print("   - Compare new vs. old quality scores")
        print("   - Replace if quality improves")
        
        # Perform iterative refinement
        refinement_result = await refiner.iterative_refine_hyperedges(
            hyperedge_ids=low_quality_ids,
            text_chunks_db=rag.text_chunks,
            llm_model_func=rag.llm_model_func,
            embedding_func=rag.embedding_func,
            quality_scorer=quality_scorer,
            global_config=rag.global_config,
            max_iterations=2  # Try up to 2 refinement iterations per hyperedge
        )
        
        print("\n6. Refinement Results:")
        print(f"   - Hyperedges processed: {refinement_result['refined_count']}")
        print(f"   - Hyperedges improved: {refinement_result['improved_count']}")
        print(f"   - Failed refinements: {refinement_result['failed_count']}")
        print(f"   - Improvement rate: {refinement_result['improvement_rate']:.1%}")
        
        if refinement_result['improved_count'] > 0:
            print(f"   - Average quality improvement: {refinement_result['avg_quality_improvement']:.3f}")
            
            print("\n   Detailed improvements:")
            for detail in refinement_result['refinement_details'][:5]:  # Show first 5
                print(f"\n   Hyperedge: {detail['hyperedge_id']}")
                print(f"   - Old quality: {detail['old_quality']:.3f}")
                print(f"   - New quality: {detail['new_quality']:.3f}")
                print(f"   - Improvement: +{detail['improvement']:.3f}")
                print(f"   - Old text: {detail['old_text'][:80]}...")
                print(f"   - New text: {detail['new_text'][:80]}...")
        
        # Show final quality distribution
        print("\n7. Final quality distribution after refinement:")
        
        final_quality_scores = {}
        for he_id in all_nodes:
            node = await rag.knowledge_graph_inst.get_node(he_id)
            if node:
                final_quality_scores[he_id] = node.get('quality_score', 0.5)
        
        if final_quality_scores:
            avg_quality = sum(final_quality_scores.values()) / len(final_quality_scores)
            min_quality = min(final_quality_scores.values())
            max_quality = max(final_quality_scores.values())
            
            print(f"   - Average: {avg_quality:.3f}")
            print(f"   - Min: {min_quality:.3f}")
            print(f"   - Max: {max_quality:.3f}")
            
            low_quality = sum(1 for q in final_quality_scores.values() if q < 0.4)
            medium_quality = sum(1 for q in final_quality_scores.values() if 0.4 <= q < 0.7)
            high_quality = sum(1 for q in final_quality_scores.values() if q >= 0.7)
            
            print(f"   - Low quality (<0.4): {low_quality}")
            print(f"   - Medium quality (0.4-0.7): {medium_quality}")
            print(f"   - High quality (≥0.7): {high_quality}")
    
    else:
        print("\n   No low-quality hyperedges to refine.")
    
    print("\n" + "=" * 80)
    print("Iterative Refinement Example Complete!")
    print("=" * 80)
    
    print("\nKey Features Demonstrated:")
    print("✓ Automatic identification of low-quality hyperedges")
    print("✓ Source text retrieval for re-extraction")
    print("✓ Improved prompts with quality feedback")
    print("✓ Quality comparison and selective replacement")
    print("✓ Iterative refinement with multiple attempts")
    print("✓ Detailed refinement statistics and reporting")


if __name__ == "__main__":
    asyncio.run(main())
