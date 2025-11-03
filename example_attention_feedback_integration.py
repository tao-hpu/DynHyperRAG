"""
Example: Integrating Attention-Based Feedback into DynHyperRAG Query Pipeline

This example demonstrates how to use attention-based feedback extraction
in a real query pipeline with an LLM that supports attention weight extraction.
"""

import asyncio
import numpy as np
from hypergraphrag.dynamic.feedback_extractor import FeedbackExtractor
from hypergraphrag.dynamic.weight_updater import WeightUpdater


# Mock functions for demonstration
async def mock_embedding_func(texts):
    """Mock embedding function."""
    return [np.random.rand(384) for _ in texts]


async def mock_llm_generate_with_attention(query, context):
    """
    Mock LLM generation that returns both answer and attention weights.
    
    In practice, this would call a real LLM API that supports attention extraction,
    such as:
    - Hugging Face models with output_attentions=True
    - Custom deployed models with attention extraction
    - Local models with attention access
    """
    # Simulate answer generation
    answer = f"Based on the context, {query} is related to multiple entities."
    
    # Simulate attention weights for each hyperedge
    # In practice, these would come from the model's attention mechanism
    attention_weights = {
        'he1': 0.45,  # High attention - this hyperedge was important
        'he2': 0.15,  # Medium attention
        'he3': 0.05,  # Low attention - not very relevant
    }
    
    return answer, attention_weights


async def mock_retrieve_hyperedges(query, graph):
    """Mock hyperedge retrieval."""
    return [
        {
            'id': 'he1',
            'hyperedge': 'Entity A relates to Entity B through relationship X',
            'distance': 0.85
        },
        {
            'id': 'he2',
            'hyperedge': 'Entity C connects to Entity D via pathway Y',
            'distance': 0.72
        },
        {
            'id': 'he3',
            'hyperedge': 'Entity E is associated with Entity F',
            'distance': 0.65
        }
    ]


class DynHyperRAGWithAttention:
    """
    DynHyperRAG query processor with attention-based feedback.
    """
    
    def __init__(self, graph, embedding_func):
        self.graph = graph
        
        # Initialize feedback extractor with attention method
        self.feedback_extractor = FeedbackExtractor(
            embedding_func,
            {
                'method': 'attention',
                'attention_threshold': 0.1,
                'positive_feedback': 1.0,
                'negative_feedback': 0.3,
                'neutral_feedback': 0.5
            }
        )
        
        # Initialize weight updater
        self.weight_updater = WeightUpdater(
            graph,
            {
                'strategy': 'ema',
                'update_alpha': 0.1,
                'decay_factor': 0.99
            }
        )
        
        print("✓ DynHyperRAG initialized with attention-based feedback")
    
    async def query(self, query_text):
        """
        Process a query with attention-based feedback.
        
        Args:
            query_text: User query
        
        Returns:
            Generated answer
        """
        print(f"\n{'='*60}")
        print(f"Query: {query_text}")
        print(f"{'='*60}")
        
        # Step 1: Retrieve relevant hyperedges
        print("\n[1] Retrieving hyperedges...")
        retrieved_hyperedges = await mock_retrieve_hyperedges(query_text, self.graph)
        print(f"    Retrieved {len(retrieved_hyperedges)} hyperedges")
        
        # Step 2: Generate answer with attention weights
        print("\n[2] Generating answer with attention tracking...")
        context = "\n".join([he['hyperedge'] for he in retrieved_hyperedges])
        answer, attention_weights = await mock_llm_generate_with_attention(
            query_text, context
        )
        print(f"    Answer: {answer}")
        print(f"    Attention weights: {attention_weights}")
        
        # Step 3: Extract feedback using attention
        print("\n[3] Extracting feedback from attention...")
        metadata = {
            'hyperedge_attention': attention_weights
        }
        feedback_signals = await self.feedback_extractor.extract_feedback(
            answer, retrieved_hyperedges, metadata
        )
        
        print("    Feedback signals:")
        for he_id, signal in feedback_signals.items():
            attention = attention_weights.get(he_id, 0.0)
            print(f"      {he_id}: attention={attention:.3f} -> feedback={signal:.3f}")
        
        # Step 4: Update hyperedge weights asynchronously
        print("\n[4] Updating hyperedge weights...")
        asyncio.create_task(
            self._update_weights_async(feedback_signals)
        )
        print("    Weight update scheduled (async)")
        
        print(f"\n{'='*60}")
        print("Query processing complete!")
        print(f"{'='*60}\n")
        
        return answer
    
    async def _update_weights_async(self, feedback_signals):
        """Update weights asynchronously."""
        try:
            for he_id, signal in feedback_signals.items():
                # In practice, this would update the actual graph
                print(f"    [Background] Updating weight for {he_id}: signal={signal:.3f}")
                # await self.weight_updater.update_weights(he_id, signal)
            
            print("    [Background] All weights updated successfully")
        except Exception as e:
            print(f"    [Background] Weight update failed: {e}")


async def example_with_huggingface_model():
    """
    Example: Using attention-based feedback with Hugging Face models.
    
    This shows how to extract attention from a real Hugging Face model.
    """
    print("\n" + "="*60)
    print("Example: Hugging Face Model with Attention Extraction")
    print("="*60)
    
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Load a small model for demonstration
        model_name = "gpt2"
        print(f"\nLoading model: {model_name}...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        # Prepare input
        prompt = "The capital of France is"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate with attention
        print("Generating with attention tracking...")
        outputs = model.generate(
            **inputs,
            max_new_tokens=10,
            output_attentions=True,
            return_dict_in_generate=True
        )
        
        # Extract attention
        if hasattr(outputs, 'attentions') and outputs.attentions:
            print(f"✓ Attention extracted: {len(outputs.attentions)} layers")
            
            # Get attention from last layer
            last_layer_attention = outputs.attentions[-1]
            print(f"  Last layer attention shape: {last_layer_attention[0].shape}")
            
            # In practice, you would process this attention to map to hyperedges
            print("\n  This attention data can be used with FeedbackExtractor:")
            print("  metadata = {")
            print("      'attention_matrix': last_layer_attention,")
            print("      'context_texts': [...],")
            print("      'answer_start_pos': ...,")
            print("  }")
        else:
            print("✗ Model doesn't support attention extraction")
        
    except ImportError:
        print("\n⚠ transformers library not installed")
        print("  Install with: pip install transformers torch")
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def main():
    """Run examples."""
    print("\n" + "="*60)
    print("Attention-Based Feedback Integration Examples")
    print("="*60)
    
    # Example 1: Mock integration
    print("\n[Example 1] Mock Integration with Attention-Based Feedback")
    print("-" * 60)
    
    # Create mock graph
    mock_graph = None  # In practice, this would be a real graph instance
    
    # Initialize system
    system = DynHyperRAGWithAttention(mock_graph, mock_embedding_func)
    
    # Process a query
    answer = await system.query("What is the relationship between Entity A and Entity B?")
    
    # Wait a bit for async updates
    await asyncio.sleep(0.5)
    
    # Example 2: Hugging Face integration
    print("\n[Example 2] Hugging Face Model Integration")
    print("-" * 60)
    await example_with_huggingface_model()
    
    # Example 3: Comparison with other methods
    print("\n[Example 3] Comparing Feedback Methods")
    print("-" * 60)
    
    methods = ['embedding', 'citation', 'hybrid', 'attention']
    
    print("\nMethod Comparison:")
    print(f"{'Method':<15} {'Speed':<10} {'Accuracy':<10} {'LLM Support':<15}")
    print("-" * 50)
    print(f"{'embedding':<15} {'Medium':<10} {'High':<10} {'Not required':<15}")
    print(f"{'citation':<15} {'Fast':<10} {'Medium':<10} {'Not required':<15}")
    print(f"{'hybrid':<15} {'Medium':<10} {'High':<10} {'Not required':<15}")
    print(f"{'attention':<15} {'Fast':<10} {'Highest':<10} {'Required':<15}")
    
    print("\nRecommendation:")
    print("  • Use 'attention' when LLM supports it (most accurate)")
    print("  • Use 'hybrid' as default (good balance)")
    print("  • Use 'embedding' for semantic matching")
    print("  • Use 'citation' for speed")
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
