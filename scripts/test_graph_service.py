#!/usr/bin/env python
"""
Test script for GraphService

Verifies that GraphService can load data and perform basic operations.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_graph_service():
    """Test GraphService functionality"""
    
    print("🧪 Testing GraphService...")
    print()
    
    try:
        # Import GraphService
        print("1. Importing GraphService...")
        from api.services.graph_service import GraphService
        print("   ✓ Import successful")
        
        # Initialize service
        print("2. Initializing GraphService...")
        service = GraphService()
        
        # Check if data exists
        import os
        if not os.path.exists("expr/example/graph_chunk_entity_relation.graphml"):
            print("   ⚠️  Warning: No data found in expr/example/")
            print("   Please run script_construct.py first to generate data")
            return
        
        await service.initialize()
        print("   ✓ Initialization successful")
        
        # Test get_stats
        print("3. Testing get_stats()...")
        stats = await service.get_stats()
        print(f"   Nodes: {stats.num_nodes}")
        print(f"   Edges: {stats.num_edges}")
        print(f"   Hyperedges: {stats.num_hyperedges}")
        print(f"   Avg Degree: {stats.avg_degree:.2f}")
        print(f"   Density: {stats.density:.4f}")
        print("   ✓ get_stats() successful")
        
        # Test get_nodes
        print("4. Testing get_nodes()...")
        nodes = await service.get_nodes(limit=5, offset=0)
        print(f"   Retrieved {len(nodes)} nodes")
        if nodes:
            print(f"   Sample node: {nodes[0].label} ({nodes[0].type})")
        print("   ✓ get_nodes() successful")
        
        # Test get_edges
        print("5. Testing get_edges()...")
        edges = await service.get_edges(limit=5, offset=0)
        print(f"   Retrieved {len(edges)} edges")
        if edges:
            print(f"   Sample edge: {edges[0].source} -> {edges[0].target}")
            print(f"   Is hyperedge: {edges[0].is_hyperedge}")
        print("   ✓ get_edges() successful")
        
        # Test search_nodes
        if nodes:
            print("6. Testing search_nodes()...")
            search_keyword = nodes[0].label.split()[0] if nodes[0].label else "test"
            results = await service.search_nodes(search_keyword, limit=3)
            print(f"   Search '{search_keyword}' returned {len(results)} results")
            if results:
                print(f"   Top result: {results[0].label} (score: {results[0].relevance_score:.2f})")
            print("   ✓ search_nodes() successful")
        
        # Test get_subgraph
        if nodes:
            print("7. Testing get_subgraph()...")
            center_node = nodes[0].id
            subgraph = await service.get_subgraph(center_node, depth=1)
            print(f"   Subgraph around '{nodes[0].label}':")
            print(f"   Nodes: {len(subgraph.nodes)}")
            print(f"   Edges: {len(subgraph.edges)}")
            print("   ✓ get_subgraph() successful")
        
        print()
        print("✅ All GraphService tests passed!")
        print()
        print("GraphService is ready to use in the API.")
        
    except FileNotFoundError as e:
        print(f"❌ Data files not found: {e}")
        print()
        print("Please run the construction script first:")
        print("  python script_construct.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_graph_service())
