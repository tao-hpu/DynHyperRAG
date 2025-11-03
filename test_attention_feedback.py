"""
Test script for attention-based feedback extraction.

This script demonstrates and tests the attention-based feedback extraction
functionality in the FeedbackExtractor class.
"""

import asyncio
import numpy as np
from hypergraphrag.dynamic.feedback_extractor import FeedbackExtractor


async def mock_embedding_func(texts):
    """Mock embedding function for testing."""
    # Return random embeddings
    return [np.random.rand(384) for _ in texts]


async def test_attention_based_feedback_direct():
    """Test attention-based feedback with direct hyperedge attention scores."""
    print("\n=== Test 1: Direct Hyperedge Attention ===")
    
    config = {
        'method': 'attention',
        'attention_threshold': 0.1,
        'positive_feedback': 1.0,
        'negative_feedback': 0.3,
        'neutral_feedback': 0.5
    }
    
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # Mock retrieved hyperedges
    retrieved_hyperedges = [
        {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'},
        {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'},
        {'id': 'he3', 'hyperedge': 'Entity E is associated with Entity F'}
    ]
    
    # Mock answer
    answer = "Entity A and Entity B are related through their connection."
    
    # Mock metadata with direct attention scores
    metadata = {
        'hyperedge_attention': {
            'he1': 0.45,  # High attention (above threshold)
            'he2': 0.05,  # Low attention (below threshold)
            'he3': 0.12   # Just above threshold
        }
    }
    
    # Extract feedback
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
    
    print(f"Answer: {answer}")
    print(f"\nFeedback signals:")
    for he_id, signal in feedback.items():
        attention = metadata['hyperedge_attention'][he_id]
        print(f"  {he_id}: attention={attention:.3f}, feedback={signal:.3f}")
    
    # Verify results
    assert 'he1' in feedback
    assert feedback['he1'] >= 0.7, "High attention should give positive feedback"
    assert feedback['he2'] < 0.5, "Low attention should give negative feedback"
    assert feedback['he3'] > feedback['he2'], "Medium attention should be higher than low attention"
    # Both he1 and he3 are above threshold, so both get positive feedback
    # he1 should be equal or higher since it has higher attention
    assert feedback['he1'] >= feedback['he3'], "Higher attention should give equal or higher feedback"
    
    print("\n✓ Test 1 passed!")


async def test_attention_based_feedback_with_mapping():
    """Test attention-based feedback with attention weights and context mapping."""
    print("\n=== Test 2: Attention Weights with Context Mapping ===")
    
    config = {
        'method': 'attention',
        'attention_threshold': 0.1
    }
    
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # Mock retrieved hyperedges
    retrieved_hyperedges = [
        {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'},
        {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'}
    ]
    
    answer = "Entity A and Entity B are related."
    
    # Mock metadata with attention weights and context mapping
    # Simulate that he1 appears at positions 0-2, he2 at positions 3-4
    metadata = {
        'attention_weights': {
            0: 0.15,  # he1 positions
            1: 0.20,
            2: 0.10,
            3: 0.05,  # he2 positions
            4: 0.03
        },
        'context_mapping': {
            'he1': [0, 1, 2],
            'he2': [3, 4]
        }
    }
    
    # Extract feedback
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
    
    print(f"Answer: {answer}")
    print(f"\nFeedback signals:")
    for he_id, signal in feedback.items():
        positions = metadata['context_mapping'][he_id]
        avg_attention = np.mean([metadata['attention_weights'][p] for p in positions])
        print(f"  {he_id}: positions={positions}, avg_attention={avg_attention:.3f}, feedback={signal:.3f}")
    
    # Verify results
    assert 'he1' in feedback
    assert 'he2' in feedback
    assert feedback['he1'] > feedback['he2'], "he1 should have higher feedback due to higher attention"
    
    print("\n✓ Test 2 passed!")


async def test_attention_based_feedback_with_matrix():
    """Test attention-based feedback with raw attention matrix."""
    print("\n=== Test 3: Raw Attention Matrix ===")
    
    config = {
        'method': 'attention',
        'attention_threshold': 0.1
    }
    
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # Mock retrieved hyperedges
    retrieved_hyperedges = [
        {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'},
        {'id': 'he2', 'hyperedge': 'Entity C connects to Entity D'}
    ]
    
    answer = "Entity A and Entity B are related."
    
    # Mock attention matrix: [seq_len, seq_len]
    # Simulate 10 tokens: 6 context + 4 answer
    seq_len = 10
    attention_matrix = np.random.rand(seq_len, seq_len)
    
    # Make answer tokens (6-9) attend more to first context chunk (0-2)
    attention_matrix[6:, 0:3] = 0.3  # High attention to first chunk
    attention_matrix[6:, 3:6] = 0.05  # Low attention to second chunk
    
    # Normalize rows to sum to 1
    attention_matrix = attention_matrix / attention_matrix.sum(axis=1, keepdims=True)
    
    metadata = {
        'attention_matrix': attention_matrix,
        'context_texts': [
            'Entity A relates to Entity B in the context',  # Matches he1
            'Entity C connects to Entity D in another way',  # Matches he2
        ],
        'answer_start_pos': 6,
        'context_end_pos': 6
    }
    
    # Extract feedback
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
    
    print(f"Answer: {answer}")
    print(f"\nFeedback signals:")
    for he_id, signal in feedback.items():
        print(f"  {he_id}: feedback={signal:.3f}")
    
    # Verify results
    assert 'he1' in feedback
    assert 'he2' in feedback
    
    print("\n✓ Test 3 passed!")


async def test_attention_fallback_to_embedding():
    """Test that attention method falls back to embedding when no attention data."""
    print("\n=== Test 4: Fallback to Embedding ===")
    
    config = {
        'method': 'attention',
        'similarity_threshold': 0.7
    }
    
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # Mock retrieved hyperedges
    retrieved_hyperedges = [
        {'id': 'he1', 'hyperedge': 'Entity A relates to Entity B'}
    ]
    
    answer = "Entity A and Entity B are related."
    
    # No metadata provided - should fall back to embedding
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata=None)
    
    print(f"Answer: {answer}")
    print(f"\nFeedback signals (fallback to embedding):")
    for he_id, signal in feedback.items():
        print(f"  {he_id}: feedback={signal:.3f}")
    
    # Verify results
    assert 'he1' in feedback
    assert 0.0 <= feedback['he1'] <= 1.0
    
    print("\n✓ Test 4 passed!")


async def test_attention_to_feedback_conversion():
    """Test attention score to feedback signal conversion."""
    print("\n=== Test 5: Attention to Feedback Conversion ===")
    
    config = {
        'method': 'attention',
        'attention_threshold': 0.1,
        'positive_feedback': 1.0,
        'negative_feedback': 0.3,
        'neutral_feedback': 0.5
    }
    
    extractor = FeedbackExtractor(mock_embedding_func, config)
    
    # Test various attention scores
    test_cases = [
        (0.0, "zero attention"),
        (0.05, "low attention (below threshold)"),
        (0.1, "threshold attention"),
        (0.3, "medium attention"),
        (0.5, "high attention"),
        (1.0, "maximum attention")
    ]
    
    print("\nAttention to Feedback Conversion:")
    for attention_score, description in test_cases:
        feedback = extractor._attention_to_feedback(attention_score)
        print(f"  Attention={attention_score:.2f} ({description}) -> Feedback={feedback:.3f}")
        
        # Verify feedback is in valid range
        assert 0.0 <= feedback <= 1.0
        
        # Verify threshold behavior
        if attention_score >= config['attention_threshold']:
            assert feedback >= config['positive_feedback'], f"High attention should give positive feedback"
        else:
            assert feedback < config['neutral_feedback'], f"Low attention should give negative feedback"
    
    print("\n✓ Test 5 passed!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Attention-Based Feedback Extraction")
    print("=" * 60)
    
    try:
        await test_attention_based_feedback_direct()
        await test_attention_based_feedback_with_mapping()
        await test_attention_based_feedback_with_matrix()
        await test_attention_fallback_to_embedding()
        await test_attention_to_feedback_conversion()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
