# Attention-Based Feedback Extraction

## Overview

The attention-based feedback extraction method analyzes LLM attention weights to determine which retrieved hyperedges contributed most to the generated answer. This provides a more direct and interpretable signal compared to embedding-based or citation-based methods.

## How It Works

When an LLM generates an answer, it assigns attention weights to different parts of the input context. By analyzing these attention patterns, we can identify which hyperedges the model "paid attention to" during generation.

### Attention to Feedback Conversion

The attention score is converted to a feedback signal using a threshold-based approach:

- **High attention** (≥ threshold): Positive feedback (0.7-1.0)
- **Low attention** (< threshold): Negative feedback (0.3-0.5)

The conversion formula:

```python
if attention >= threshold:
    # Scale from threshold to 1.0 -> positive_feedback to 1.0
    normalized = (attention - threshold) / (1.0 - threshold)
    feedback = positive_feedback + normalized * (1.0 - positive_feedback)
else:
    # Scale from 0 to threshold -> negative_feedback to neutral_feedback
    normalized = attention / threshold
    feedback = negative_feedback + normalized * (neutral_feedback - negative_feedback)
```

## Usage

### Method 1: Direct Hyperedge Attention Scores

The simplest method - provide attention scores directly for each hyperedge:

```python
from hypergraphrag.dynamic.feedback_extractor import FeedbackExtractor

config = {
    'method': 'attention',
    'attention_threshold': 0.1,  # Minimum attention to be considered useful
    'positive_feedback': 1.0,
    'negative_feedback': 0.3,
    'neutral_feedback': 0.5
}

extractor = FeedbackExtractor(embedding_func, config)

# Metadata with direct attention scores
metadata = {
    'hyperedge_attention': {
        'he1': 0.45,  # High attention
        'he2': 0.05,  # Low attention
        'he3': 0.15   # Medium attention
    }
}

feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
# Returns: {'he1': 1.0, 'he2': 0.4, 'he3': 1.0}
```

### Method 2: Attention Weights with Context Mapping

When you have token-level attention weights and know which tokens correspond to which hyperedges:

```python
metadata = {
    'attention_weights': {
        0: 0.15,  # Token 0 attention
        1: 0.20,  # Token 1 attention
        2: 0.10,  # Token 2 attention
        3: 0.05,  # Token 3 attention
        4: 0.03   # Token 4 attention
    },
    'context_mapping': {
        'he1': [0, 1, 2],  # he1 spans tokens 0-2
        'he2': [3, 4]      # he2 spans tokens 3-4
    }
}

feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
```

The extractor will:
1. Find which tokens correspond to each hyperedge
2. Aggregate attention across those tokens (average)
3. Convert to feedback signal

### Method 3: Raw Attention Matrix

For advanced use cases with full attention matrices:

```python
import numpy as np

# Attention matrix: [layers, heads, seq_len, seq_len]
# or [heads, seq_len, seq_len]
# or [seq_len, seq_len]
attention_matrix = model.get_attention_weights()

metadata = {
    'attention_matrix': attention_matrix,
    'context_texts': [
        'Entity A relates to Entity B...',  # Context chunk 1
        'Entity C connects to Entity D...'  # Context chunk 2
    ],
    'answer_start_pos': 6,  # Where answer tokens start
    'context_end_pos': 6    # Where context tokens end
}

feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
```

The extractor will:
1. Aggregate attention across layers and heads
2. Extract attention from answer tokens to context tokens
3. Match hyperedges to context chunks using text matching
4. Compute feedback based on aggregated attention

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `method` | `'embedding'` | Set to `'attention'` to use attention-based feedback |
| `attention_threshold` | `0.1` | Minimum attention score to be considered useful |
| `positive_feedback` | `1.0` | Feedback value for high attention |
| `negative_feedback` | `0.3` | Feedback value for low attention |
| `neutral_feedback` | `0.5` | Feedback value for uncertain cases |

## Fallback Behavior

If attention data is not available in the metadata, the extractor automatically falls back to embedding-based feedback extraction. This ensures robustness even when the LLM doesn't support attention weight extraction.

## Requirements

### LLM Support

Not all LLMs expose attention weights. To use this method, your LLM must:

1. **Support attention weight extraction**: Models like GPT-2, BERT, T5, LLaMA (with modifications) can expose attention weights
2. **Provide attention in the response**: You need to configure the model to return attention weights along with the generated text

### Example: Extracting Attention from Hugging Face Models

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Generate with attention weights
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(
    **inputs,
    output_attentions=True,  # Enable attention output
    return_dict_in_generate=True
)

# Extract attention weights
attentions = outputs.attentions  # Tuple of attention tensors
# Process attentions to create metadata...
```

### Example: OpenAI API (Limited Support)

OpenAI's API doesn't directly expose attention weights, but you can use logprobs as a proxy:

```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[...],
    logprobs=True,  # Get token probabilities
    top_logprobs=5
)

# Use logprobs to estimate which context was most relevant
# This is an approximation, not true attention
```

## Advantages

1. **Direct Signal**: Attention weights directly show what the model focused on
2. **Interpretable**: Easy to understand why a hyperedge got high/low feedback
3. **No Embedding Computation**: Faster than embedding-based methods
4. **Model-Aware**: Reflects the actual model's decision-making process

## Limitations

1. **LLM Support Required**: Not all LLMs expose attention weights
2. **API Limitations**: Many commercial APIs don't provide attention data
3. **Attention ≠ Importance**: High attention doesn't always mean high importance
4. **Complexity**: Requires additional infrastructure to extract and process attention

## Best Practices

1. **Use with Open-Source Models**: Works best with models you control (Hugging Face, local deployments)
2. **Combine with Other Methods**: Use hybrid approach when attention is available, fallback to embedding otherwise
3. **Tune Threshold**: Adjust `attention_threshold` based on your model's attention distribution
4. **Validate**: Compare attention-based feedback with embedding-based to ensure consistency

## Performance

Attention-based feedback is typically **faster** than embedding-based methods because:
- No need to compute embeddings for answer and hyperedges
- Direct use of model's internal representations
- Can be extracted during generation (no post-processing)

However, it requires:
- Additional memory to store attention weights
- Processing logic to aggregate and map attention to hyperedges

## Integration Example

```python
from hypergraphrag.dynamic.feedback_extractor import FeedbackExtractor
from hypergraphrag.dynamic.weight_updater import WeightUpdater

# Initialize with attention method
config = {
    'method': 'attention',
    'attention_threshold': 0.1
}

extractor = FeedbackExtractor(embedding_func, config)
updater = WeightUpdater(graph, {'strategy': 'ema', 'update_alpha': 0.1})

# During query processing
async def process_query(query, retrieved_hyperedges):
    # Generate answer with attention
    answer, attention_data = await llm_generate_with_attention(query, retrieved_hyperedges)
    
    # Extract feedback using attention
    metadata = {
        'hyperedge_attention': attention_data
    }
    feedback = await extractor.extract_feedback(answer, retrieved_hyperedges, metadata)
    
    # Update weights
    for he_id, signal in feedback.items():
        await updater.update_weights(he_id, signal)
    
    return answer
```

## Future Enhancements

1. **Multi-Head Analysis**: Analyze different attention heads separately
2. **Layer-Specific Attention**: Use attention from specific layers (e.g., last layer)
3. **Attention Patterns**: Detect attention patterns (e.g., copy mechanism, reasoning chains)
4. **Cross-Attention**: For encoder-decoder models, analyze cross-attention specifically
5. **Attention Visualization**: Generate visualizations of attention distributions

## References

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) - Original Transformer paper
- [BERTology: What does BERT learn about language?](https://arxiv.org/abs/2002.12327) - Analysis of BERT attention
- [Analyzing Multi-Head Self-Attention](https://arxiv.org/abs/1905.09418) - Understanding attention patterns

## See Also

- [README_FEEDBACK_EXTRACTOR.md](README_FEEDBACK_EXTRACTOR.md) - Overview of all feedback extraction methods
- [README_WEIGHT_UPDATER.md](README_WEIGHT_UPDATER.md) - How feedback signals are used to update weights
- [README_QUERY_INTEGRATION.md](README_QUERY_INTEGRATION.md) - Integration into query pipeline
