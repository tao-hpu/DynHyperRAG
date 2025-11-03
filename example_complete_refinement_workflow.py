"""
Complete Refinement Workflow Example

This example demonstrates the complete workflow of quality-aware hyperedge
refinement in DynHyperRAG, including:
1. Document insertion and hyperedge extraction
2. Quality score computation
3. Low-quality hyperedge identification
4. Iterative refinement with improved prompts
5. Quality comparison and selective replacement
6. Final quality distribution analysis

This showcases how iterative refinement integrates with the overall
DynHyperRAG quality-aware dynamic hypergraph system.

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
import os
from hypergraphrag import HyperGraphRAG
from hypergraphrag.quality.scorer import QualityScorer
from hypergraphrag.dynamic.refiner import HyperedgeRefiner


async def main():
    """Demonstrate complete refinement workflow."""
    
    print("=" * 80)
    print("Complete DynHyperRAG Refinement Workflow")
    print("=" * 80)
    
    # ========================================================================
    # Phase 1: System Initialization
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 1: System Initialization")
    print("=" * 80)
    
    working_dir = "./complete_refinement_workspace"
    os.makedirs(working_dir, exist_ok=True)
    
    print("\nInitializing HyperGraphRAG system...")
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_llm_cache=True,
    )
    
    # ========================================================================
    # Phase 2: Document Insertion and Hyperedge Extraction
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 2: Document Insertion and Hyperedge Extraction")
    print("=" * 80)
    
    documents = [
        "Alice is a software engineer at TechCorp. She specializes in artificial intelligence and machine learning.",
        "Bob works as a data scientist at TechCorp. He collaborates with Alice on AI research projects.",
        "TechCorp is a technology company founded in 2020. It focuses on developing AI solutions for healthcare.",
        "The AI team at TechCorp recently published a paper on neural networks. Alice and Bob were the lead authors.",
        "TechCorp's headquarters is located in San Francisco. The company has over 100 employees.",
    ]
    
    print(f"\nInserting {len(documents)} documents...")
    await rag.insert(documents)
    
    # Get all hyperedges
    print("\nCollecting hyperedges...")
    all_hyperedge_ids = []
    async for node_id in rag.knowledge_graph_inst.index_done_callback():
        node = await rag.knowledge_graph_inst.get_node(node_id)
        if node and node.get('role') == 'hyperedge':
            all_hyperedge_ids.append(node_id)
    
    print(f"Found {len(all_hyperedge_ids)} hyperedges")
    
    # ========================================================================
    # Phase 3: Quality Score Computation
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 3: Quality Score Computation")
    print("=" * 80)
    
    print("\nInitializing quality scorer...")
    quality_config = {
        'feature_weights': {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        }
    }
    
    scorer = QualityScorer(
        rag.knowledge_graph_inst,
        quality_config
    )
    
    print("\nComputing quality scores for all hyperedges...")
    quality_scores = {}
    
    for he_id in all_hyperedge_ids:
        try:
            result = await scorer.compute_quality_score(he_id)
            quality_scores[he_id] = result['quality_score']
            
            # Update node with quality score
            node = await rag.knowledge_graph_inst.get_node(he_id)
            node['quality_score'] = result['quality_score']
            node['quality_features'] = result['features']
            await rag.knowledge_graph_inst.upsert_node(he_id, node)
            
            print(f"  {he_id[:50]}... : {result['quality_score']:.3f}")
            
        except Exception as e:
            print(f"  Warning: Failed to compute quality for {he_id}: {e}")
            quality_scores[he_id] = 0.5
    
    # Display initial quality distribution
    if quality_scores:
        print("\nInitial Quality Distribution:")
        avg_quality = sum(quality_scores.values()) / len(quality_scores)
        min_quality = min(quality_scores.values())
        max_quality = max(quality_scores.values())
        
        print(f"  Average: {avg_quality:.3f}")
        print(f"  Min: {min_quality:.3f}")
        print(f"  Max: {max_quality:.3f}")
        
        low_quality = sum(1 for q in quality_scores.values() if q < 0.4)
        medium_quality = sum(1 for q in quality_scores.values() if 0.4 <= q < 0.7)
        high_quality = sum(1 for q in quality_scores.values() if q >= 0.7)
        
        print(f"\n  Quality Breakdown:")
        print(f"    Low (<0.4):    {low_quality:3d} ({low_quality/len(quality_scores)*100:.1f}%)")
        print(f"    Medium (0.4-0.7): {medium_quality:3d} ({medium_quality/len(quality_scores)*100:.1f}%)")
        print(f"    High (≥0.7):   {high_quality:3d} ({high_quality/len(quality_scores)*100:.1f}%)")
    
    # ========================================================================
    # Phase 4: Low-Quality Hyperedge Identification
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 4: Low-Quality Hyperedge Identification")
    print("=" * 80)
    
    quality_threshold = 0.5
    print(f"\nIdentifying hyperedges with quality < {quality_threshold}...")
    
    low_quality_ids = [
        he_id for he_id, quality in quality_scores.items()
        if quality < quality_threshold
    ]
    
    print(f"Found {len(low_quality_ids)} low-quality hyperedges")
    
    if low_quality_ids:
        print("\nLow-quality hyperedges:")
        for he_id in low_quality_ids[:5]:  # Show first 5
            node = await rag.knowledge_graph_inst.get_node(he_id)
            quality = quality_scores[he_id]
            text = node.get('hyperedge', '')[:80]
            print(f"  [{quality:.3f}] {text}...")
    
    # ========================================================================
    # Phase 5: Iterative Refinement
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 5: Iterative Refinement")
    print("=" * 80)
    
    if low_quality_ids:
        print("\nInitializing hyperedge refiner...")
        refiner_config = {
            'quality_threshold': quality_threshold,
            'filter_mode': 'soft',
            'threshold_strategy': 'fixed',
        }
        
        refiner = HyperedgeRefiner(
            rag.knowledge_graph_inst,
            refiner_config
        )
        
        print(f"\nPerforming iterative refinement on {len(low_quality_ids)} hyperedges...")
        print("This process will:")
        print("  1. Retrieve source text for each hyperedge")
        print("  2. Re-extract using improved prompts with quality feedback")
        print("  3. Compute quality scores for new hyperedges")
        print("  4. Compare new vs. old quality scores")
        print("  5. Replace hyperedges if quality improves")
        
        refinement_result = await refiner.iterative_refine_hyperedges(
            hyperedge_ids=low_quality_ids,
            text_chunks_db=rag.text_chunks,
            llm_model_func=rag.llm_model_func,
            embedding_func=rag.embedding_func,
            quality_scorer=scorer,
            global_config=rag.global_config,
            max_iterations=2  # Try up to 2 refinement iterations
        )
        
        # ====================================================================
        # Phase 6: Refinement Results Analysis
        # ====================================================================
        print("\n" + "=" * 80)
        print("Phase 6: Refinement Results Analysis")
        print("=" * 80)
        
        print("\nRefinement Summary:")
        print(f"  Hyperedges processed: {refinement_result['refined_count']}")
        print(f"  Hyperedges improved:  {refinement_result['improved_count']}")
        print(f"  Failed refinements:   {refinement_result['failed_count']}")
        print(f"  Improvement rate:     {refinement_result['improvement_rate']:.1%}")
        
        if refinement_result['improved_count'] > 0:
            print(f"  Avg quality gain:     +{refinement_result['avg_quality_improvement']:.3f}")
            
            print("\nTop Improvements:")
            sorted_details = sorted(
                refinement_result['refinement_details'],
                key=lambda x: x['improvement'],
                reverse=True
            )
            
            for i, detail in enumerate(sorted_details[:3], 1):
                print(f"\n  {i}. Hyperedge: {detail['hyperedge_id'][:50]}...")
                print(f"     Old quality: {detail['old_quality']:.3f}")
                print(f"     New quality: {detail['new_quality']:.3f}")
                print(f"     Improvement: +{detail['improvement']:.3f}")
                print(f"     Old text: {detail['old_text'][:60]}...")
                print(f"     New text: {detail['new_text'][:60]}...")
        
        # ====================================================================
        # Phase 7: Final Quality Distribution
        # ====================================================================
        print("\n" + "=" * 80)
        print("Phase 7: Final Quality Distribution")
        print("=" * 80)
        
        print("\nRecomputing quality distribution after refinement...")
        final_quality_scores = {}
        
        for he_id in all_hyperedge_ids:
            node = await rag.knowledge_graph_inst.get_node(he_id)
            if node:
                final_quality_scores[he_id] = node.get('quality_score', 0.5)
        
        if final_quality_scores:
            avg_quality = sum(final_quality_scores.values()) / len(final_quality_scores)
            min_quality = min(final_quality_scores.values())
            max_quality = max(final_quality_scores.values())
            
            print(f"\nFinal Quality Distribution:")
            print(f"  Average: {avg_quality:.3f}")
            print(f"  Min: {min_quality:.3f}")
            print(f"  Max: {max_quality:.3f}")
            
            low_quality = sum(1 for q in final_quality_scores.values() if q < 0.4)
            medium_quality = sum(1 for q in final_quality_scores.values() if 0.4 <= q < 0.7)
            high_quality = sum(1 for q in final_quality_scores.values() if q >= 0.7)
            
            print(f"\n  Quality Breakdown:")
            print(f"    Low (<0.4):    {low_quality:3d} ({low_quality/len(final_quality_scores)*100:.1f}%)")
            print(f"    Medium (0.4-0.7): {medium_quality:3d} ({medium_quality/len(final_quality_scores)*100:.1f}%)")
            print(f"    High (≥0.7):   {high_quality:3d} ({high_quality/len(final_quality_scores)*100:.1f}%)")
            
            # Compare before and after
            initial_avg = sum(quality_scores.values()) / len(quality_scores)
            improvement = avg_quality - initial_avg
            
            print(f"\n  Overall Improvement:")
            print(f"    Initial avg: {initial_avg:.3f}")
            print(f"    Final avg:   {avg_quality:.3f}")
            print(f"    Change:      {improvement:+.3f}")
    
    else:
        print("\nNo low-quality hyperedges found. Skipping refinement.")
    
    # ========================================================================
    # Phase 8: Query Testing
    # ========================================================================
    print("\n" + "=" * 80)
    print("Phase 8: Query Testing with Refined Hyperedges")
    print("=" * 80)
    
    test_queries = [
        "Who works at TechCorp?",
        "What does Alice do?",
        "Tell me about TechCorp's AI research.",
    ]
    
    print("\nTesting queries with refined knowledge graph...")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            response = await rag.query(query)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("Workflow Complete!")
    print("=" * 80)
    
    print("\nWorkflow Summary:")
    print("✓ Phase 1: System initialized")
    print(f"✓ Phase 2: {len(documents)} documents inserted, {len(all_hyperedge_ids)} hyperedges extracted")
    print(f"✓ Phase 3: Quality scores computed for all hyperedges")
    print(f"✓ Phase 4: {len(low_quality_ids)} low-quality hyperedges identified")
    
    if low_quality_ids:
        print(f"✓ Phase 5: Iterative refinement performed")
        print(f"✓ Phase 6: {refinement_result['improved_count']} hyperedges improved")
        print(f"✓ Phase 7: Final quality distribution analyzed")
        print(f"✓ Phase 8: Query testing completed")
    else:
        print("✓ Phase 5-7: Skipped (no low-quality hyperedges)")
        print(f"✓ Phase 8: Query testing completed")
    
    print("\nKey Achievements:")
    print("• Automatic quality assessment of all hyperedges")
    print("• Identification of low-quality hyperedges")
    print("• Iterative refinement with improved prompts")
    print("• Quality-based selective replacement")
    print("• Comprehensive refinement statistics")
    print("• Improved overall knowledge graph quality")


if __name__ == "__main__":
    asyncio.run(main())
