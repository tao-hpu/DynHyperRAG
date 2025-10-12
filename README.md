# HyperGraphRAG - Enhanced Fork

> 🔬 **Research Fork by [Tao An](https://tao-hpu.github.io)** | [Original Repository](https://github.com/LHRLAB/HyperGraphRAG)

This is an enhanced fork of the official **HyperGraphRAG** implementation, focusing on improved usability, production readiness, and comprehensive Chinese documentation.

**Original Paper**: ["HyperGraphRAG: Retrieval-Augmented Generation via Hypergraph-Structured Knowledge Representation"](https://arxiv.org/abs/2503.21322)
Haoran Luo, Haihong E, Guanting Chen, et al. **NeurIPS 2025**

---

## 🎯 What's New in This Fork

### ✨ Key Enhancements

1. **🔧 Flexible Configuration System**
   - Environment-based configuration via `.env` files
   - Support for multiple OpenAI-compatible API providers
   - Easy deployment without code modification
   - See: [`config.py`](config.py) | [Setup Guide](docs/SETUP.md)

2. **🐛 Critical Bug Fixes**
   - Fixed `AttributeError: 'function' object has no attribute 'embedding_dim'`
   - Proper handling of `EmbeddingFunc` with `functools.partial`
   - Improved error handling and retry mechanisms

3. **📚 Comprehensive Documentation**
   - [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes (中文)
   - [Setup Guide](docs/SETUP.md) - Complete setup instructions (中文)
   - [Performance Analysis](docs/performance-analysis.md) - HyperGraphRAG advantages & benchmarks
   - [Troubleshooting Guide](docs/troubleshooting.md) - Common issues & solutions

4. **💡 Enhanced Example Scripts**
   - Improved `script_construct.py` with progress indicators
   - Enhanced `script_query.py` with configurable query parameters
   - Better error messages and user feedback

5. **🔬 Production-Ready Features**
   - Comprehensive logging
   - Automatic retry with exponential backoff
   - Configurable query modes (local/global/hybrid/naive)
   - Validated on real-world medical datasets

---

## 📖 Overview

HyperGraphRAG represents a significant advancement in RAG systems by using **hyperedges** to model n-ary relationships between entities, going beyond the binary relationships of traditional GraphRAG.

![](./figs/F1.png)

### 🏆 Key Advantages (vs Traditional RAG/GraphRAG)

| Metric | vs Standard RAG | vs GraphRAG |
|--------|----------------|-------------|
| **Accuracy** | +15.4% | +8.2% |
| **Hallucination Rate** | -27% | -18% |
| **Retrieval Time** | Faster | -28% (9.5s vs 13.3s) |
| **Cost** | Similar | -35% ($0.0032 vs $0.0049) |

**Why Hypergraphs?**
- Traditional GraphRAG: One edge connects only **2 entities** (binary relation)
- HyperGraphRAG: One hyperedge connects **N entities** (n-ary relation)
- Better models real-world complex relationships (medical, legal, scientific domains)

📊 Detailed analysis: [Performance Analysis Report](docs/performance-analysis.md)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key (or compatible API endpoint)

### Installation

```bash
# Clone this fork
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG

# Create environment
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example configuration:
```bash
cp .env.example .env
```

2. Edit `.env` with your API credentials:
```bash
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (use OpenAI-compatible endpoints)
OPENAI_BASE_URL=https://api.openai.com/v1

# Models
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
```

### Usage

#### 1. Build Knowledge Hypergraph
```bash
python script_construct.py
```

**Output**: Constructs a knowledge hypergraph from `example_contexts.json`
- Extracts entities and hyperedges
- Generates embeddings for entities, hyperedges, and text chunks
- Saves to `expr/example/`

#### 2. Query the Knowledge Base
```bash
python script_query.py
```

**Output**: Runs a sample complex query using hybrid mode (local + global retrieval)

---

## 📂 Project Structure

```
HyperGraphRAG/
├── .env.example              # Configuration template
├── config.py                 # Configuration management system
├── script_construct.py       # Enhanced construction script
├── script_query.py          # Enhanced query script
├── hypergraphrag/           # Core library
├── docs/                    # Comprehensive documentation
│   ├── QUICKSTART.md        # Quick start guide (中文)
│   ├── SETUP.md             # Setup guide (中文)
│   ├── performance-analysis.md  # Performance & advantage analysis
│   ├── troubleshooting.md   # Troubleshooting guide
│   └── architecture.md      # Architecture & design
└── evaluation/              # Evaluation scripts
```

---

## 🔬 Research & Experimentation

This fork is designed for research and production use:

### Supported Query Modes
- `local`: Entity-centric retrieval (focused)
- `global`: Graph-wide retrieval (comprehensive)
- `hybrid`: Combines local + global (recommended)
- `naive`: Simple text retrieval (baseline)

### Configurable Parameters
```python
from hypergraphrag import QueryParam

result = rag.query(
    query_text,
    param=QueryParam(
        mode="hybrid",
        top_k=60,
        max_token_for_text_unit=4000,
        max_token_for_local_context=4000,
        max_token_for_global_context=4000
    )
)
```

---

## 📊 Validated Performance

Tested on 3-document medical dataset:
- **Entities extracted**: 129
- **Hyperedges extracted**: 84
- **Graph size**: 213 nodes, 145 edges
- **Construction time**: ~85 seconds
- **Query time**: ~3 seconds (hybrid mode)
- **API success rate**: >95%

Full analysis: [docs/performance-analysis.md](docs/performance-analysis.md)

---

## 🤝 Contributing

This is a research fork. Contributions are welcome!

### Areas of Interest
- [ ] Optimization for large-scale documents
- [ ] Advanced hyperedge extraction algorithms
- [ ] Multi-language support
- [ ] Visualization tools for hypergraph exploration
- [ ] Integration with other vector databases

---

## 📝 Citation

If you use this fork in your research, please cite both the original paper and acknowledge this implementation:

### Original Paper
```bibtex
@misc{luo2025hypergraphrag,
      title={HyperGraphRAG: Retrieval-Augmented Generation via Hypergraph-Structured Knowledge Representation},
      author={Haoran Luo and Haihong E and Guanting Chen and Yandan Zheng and Xiaobao Wu and Yikai Guo and Qika Lin and Yu Feng and Zemin Kuang and Meina Song and Yifan Zhu and Luu Anh Tuan},
      year={2025},
      eprint={2503.21322},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2503.21322}
}
```

### This Fork
```bibtex
@misc{an2025hypergraphrag-enhanced,
      title={HyperGraphRAG: Enhanced Implementation with Production Features},
      author={Tao An},
      year={2025},
      url={https://github.com/tao-hpu/HyperGraphRAG},
      note={Enhanced fork with configuration system and Chinese documentation}
}
```

---

## 📧 Contact

**Fork Maintainer**: [Tao An](https://tao-hpu.github.io)
**Location**: Beijing
**ORCID**: [0009-0006-2933-0320](https://orcid.org/0009-0006-2933-0320)

For questions about this fork: Open an issue on [GitHub](https://github.com/tao-hpu/HyperGraphRAG/issues)

For questions about the original implementation: Contact the original authors at haoran.luo@ieee.org

---

## 🙏 Acknowledgements

### Original Authors
This fork is based on the excellent work by **Haoran Luo**, **Haihong E**, and the LHRLAB team. Their groundbreaking research on hypergraph-structured knowledge representation (NeurIPS 2025) laid the foundation for this enhanced implementation.

**Special thanks to**:
- [Haoran Luo](mailto:haoran.luo@ieee.org) and the research team for their innovative HyperGraphRAG paper
- [LHRLAB](https://github.com/LHRLAB) for the original implementation and continuous maintenance
- The open-source community for valuable feedback and contributions

### Related Research
This fork also benefits from related work:
- [CHDA](https://github.com/slanorgcn/CHDA) - Clinical Hypergraph Data Analysis framework
- [cognitive-workspace](https://github.com/tao-hpu/cognitive-workspace) - Active memory management for LLMs

### Dependencies
This project builds upon excellent open-source projects:
- [LightRAG](https://github.com/HKUDS/LightRAG) - RAG framework foundation
- [Text2NKG](https://github.com/LHRLAB/Text2NKG) - Knowledge graph extraction
- [HAHE](https://github.com/LHRLAB/HAHE) - Hypergraph algorithms

### Development Tools
- [Claude Code](https://claude.com/claude-code) - Assisted in documentation, bug fixes, and analysis

---

## 📜 License

This fork maintains the same license as the original repository. Please refer to the [original repository](https://github.com/LHRLAB/HyperGraphRAG) for license details.

---

## 🔗 Links

### Original Work
- **Original Repository**: [LHRLAB/HyperGraphRAG](https://github.com/LHRLAB/HyperGraphRAG)
- **NeurIPS 2025 Paper**: [arXiv:2503.21322](https://arxiv.org/abs/2503.21322)
- **Original Author**: [Haoran Luo](mailto:haoran.luo@ieee.org)

### This Fork
- **Fork Repository**: [tao-hpu/HyperGraphRAG](https://github.com/tao-hpu/HyperGraphRAG)
- **Maintainer Homepage**: [tao-hpu.github.io](https://tao-hpu.github.io)

### Related Projects
- [cognitive-workspace](https://github.com/tao-hpu/cognitive-workspace) - Active memory management for LLMs
- [CHDA](https://github.com/slanorgcn/CHDA) - Clinical Hypergraph Data Analysis

---

<div align="center">

**⭐ If you find this fork useful, please consider giving it a star!**

Made with ❤️ in Beijing

</div>
