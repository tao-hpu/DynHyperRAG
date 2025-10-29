# HyperGraphRAG - Enhanced Fork & DynHyperRAG Research

> 🔬 **Research Fork by [Tao An](https://tao-hpu.github.io)** | [Original Repository](https://github.com/LHRLAB/HyperGraphRAG)

This is an enhanced fork of the official **HyperGraphRAG** implementation, serving as the foundation for **DynHyperRAG** - a novel quality-aware dynamic hypergraph RAG system for doctoral research.

**Original Paper**: ["HyperGraphRAG: Retrieval-Augmented Generation via Hypergraph-Structured Knowledge Representation"](https://arxiv.org/abs/2503.21322)
Haoran Luo, Haihong E, Guanting Chen, et al. **NeurIPS 2025**

**Research Project**: **DynHyperRAG: Quality-Aware Dynamic Hypergraph for Efficient Retrieval-Augmented Generation** (PhD Thesis, Expected 2025-06)

---

## 🚀 DynHyperRAG Research Project

### Core Innovation

DynHyperRAG extends static HyperGraphRAG with three major innovations:

1. **Graph-Structure-Based Quality Assessment** - Automatically evaluate hyperedge quality using 5 structural features (degree centrality, betweenness, clustering coefficient, hyperedge coherence, text quality)

2. **Quality-Aware Dynamic Weight Update** - Dynamically adjust hyperedge weights based on retrieval feedback and quality scores using EMA/additive/multiplicative strategies

3. **Efficient Retrieval with Entity Type Filtering** - Optimize retrieval speed by 30%+ through entity type filtering and quality-aware ranking

### Research Questions

1. How to automatically assess hyperedge quality using graph structural properties?
2. How to dynamically adjust hyperedge weights based on retrieval feedback and quality scores?
3. How to optimize retrieval efficiency while maintaining or improving accuracy?

### Expected Contributions

**Academic**:
- Novel graph-structure-based quality assessment algorithm
- New hyperedge coherence metric
- Quality-aware dynamic update mechanism
- Feature importance analysis with SHAP

**Experimental**:
- Validation on CAIL2019 (legal) and PubMed/AMiner (academic) datasets
- Retrieval accuracy improvement (MRR +X%)
- Retrieval time reduction (30%+)
- Statistical significance testing

**Engineering**:
- Complete open-source implementation
- Reproducible experiment pipeline
- Lightweight variant (Dyn-Hyper-RAG-Lite) for production

📖 Full thesis overview: [docs/THESIS_OVERVIEW.md](docs/THESIS_OVERVIEW.md)

📋 Project specs: [.kiro/specs/dynhyperrag-quality-aware/](.kiro/specs/dynhyperrag-quality-aware/)

### Research Timeline (18 Weeks)

| Phase | Weeks | Deliverables |
|-------|-------|--------------|
| **Phase 1: Quality Assessment** | 1-4 | Graph feature extraction, coherence metric, quality scorer, SHAP analysis |
| **Phase 2: Dynamic Update** | 5-7 | Weight updater (EMA/additive/multiplicative), feedback extractor, hyperedge refiner |
| **Phase 3: Efficient Retrieval** | 8-10 | Entity type filter, quality-aware ranker, Dyn-Hyper-RAG-Lite |
| **Phase 4: Data Preparation** | 11-12 | CAIL2019 loader, PubMed/AMiner loader, annotation interface, gold standard datasets |
| **Phase 5: Evaluation** | 13-14 | Metrics implementation, baseline methods, statistical tests |
| **Phase 6: Experiments** | 15-16 | Full pipeline, ablation studies, result generation |
| **Phase 7: Documentation** | 17-18 | API docs, user guide, thesis writing |

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

5. **🎨 Interactive Web Visualization**
   - Modern React-based web UI for graph exploration
   - Real-time search and filtering capabilities
   - Query path visualization with animation
   - Export functionality (PNG, SVG, JSON)
   - See: [Web UI Documentation](web_ui/README.md)

6. **🧪 Comprehensive Testing Suite**
   - 91+ unit and integration tests (88.3% pass rate)
   - Component tests for all UI elements
   - Service and store integration tests
   - E2E test framework with Playwright
   - See: [Testing Guide](web_ui/TESTING_GUIDE.md)

7. **🔬 Production-Ready Features**
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

#### 3. Launch Web Visualization (Optional)
```bash
# Start backend API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401

# In another terminal, start frontend
cd web_ui
pnpm install
pnpm dev
```

**Access**: Open http://localhost:3400 in your browser

**Features**:
- Interactive graph visualization with Cytoscape.js
- Real-time node/edge search and filtering
- Query execution with path visualization
- Export graphs as PNG, SVG, or JSON
- Responsive design for mobile/tablet/desktop

📖 Full guide: [Web UI Documentation](web_ui/README.md)

---

## 📂 Project Structure

```
HyperGraphRAG/
├── .env.example              # Configuration template
├── config.py                 # Configuration management system
├── script_construct.py       # Enhanced construction script
├── script_query.py          # Enhanced query script
│
├── hypergraphrag/           # Core library
│   ├── quality/             # 🆕 Quality assessment module (DynHyperRAG)
│   │   ├── scorer.py        # Quality scoring algorithm
│   │   ├── features.py      # Graph structure feature extraction
│   │   ├── coherence.py     # Hyperedge coherence metric
│   │   └── analyzer.py      # Feature importance analysis (SHAP)
│   ├── dynamic/             # 🆕 Dynamic update module (DynHyperRAG)
│   │   ├── weight_updater.py    # Weight update mechanism
│   │   ├── feedback_extractor.py # Feedback signal extraction
│   │   └── refiner.py       # Hyperedge refinement
│   ├── retrieval/           # 🆕 Efficient retrieval module (DynHyperRAG)
│   │   ├── entity_filter.py # Entity type filtering
│   │   ├── quality_ranker.py # Quality-aware ranking
│   │   └── lite_retriever.py # Lightweight retriever
│   ├── evaluation/          # 🆕 Evaluation framework (DynHyperRAG)
│   │   ├── metrics.py       # Evaluation metrics
│   │   ├── baselines.py     # Baseline methods
│   │   └── pipeline.py      # Experiment pipeline
│   └── data/                # 🆕 Data processing (DynHyperRAG)
│       ├── cail2019_loader.py   # CAIL2019 legal dataset
│       ├── academic_loader.py   # PubMed/AMiner academic dataset
│       └── annotator.py     # Annotation interface
│
├── api/                     # FastAPI backend for visualization
│   ├── main.py              # API entry point
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   └── models/              # Data models
│
├── web_ui/                  # React-based web visualization
│   ├── src/                 # Frontend source code
│   ├── e2e/                 # E2E tests (Playwright)
│   ├── TESTING_GUIDE.md     # Testing documentation
│   └── TEST_SUMMARY.md      # Test results
│
├── docs/                    # Comprehensive documentation
│   ├── THESIS_OVERVIEW.md   # 🆕 DynHyperRAG thesis overview
│   ├── QUICKSTART.md        # Quick start guide (中文)
│   ├── SETUP.md             # Setup guide (中文)
│   ├── performance-analysis.md  # Performance & advantage analysis
│   ├── troubleshooting.md   # Troubleshooting guide
│   ├── architecture.md      # Architecture & design
│   └── visualization/       # Visualization documentation
│
├── .kiro/specs/             # 🆕 Research specifications
│   └── dynhyperrag-quality-aware/
│       ├── requirements.md  # Research requirements
│       ├── design.md        # System design
│       └── tasks.md         # Implementation tasks
│
├── expr/                    # Experiment data
│   ├── example/             # Original medical dataset
│   ├── cail2019/            # 🆕 Legal dataset (planned)
│   └── pubmed/              # 🆕 Academic dataset (planned)
│
└── evaluation/              # Evaluation scripts
```

---

## 🔬 Research & Experimentation

### DynHyperRAG vs Static HyperGraphRAG

| Feature | Static HyperGraphRAG | **DynHyperRAG (This Research)** |
|---------|---------------------|--------------------------------|
| Relationship Type | n-ary | n-ary |
| Graph Structure | Static | **Dynamic** |
| Quality Assessment | None | **Graph structure features** |
| Weight Update | None | **Feedback-driven** |
| Retrieval Optimization | Graph traversal | **Type filtering + quality ranking** |
| Efficiency | Slow | **Optimized (-30%)** |

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

### DynHyperRAG Configuration (Planned)
```python
from hypergraphrag.quality import QualityScorer
from hypergraphrag.dynamic import WeightUpdater
from hypergraphrag.retrieval import EntityTypeFilter

# Quality assessment
scorer = QualityScorer(graph, config={
    'feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    }
})

# Dynamic weight update
updater = WeightUpdater(graph, config={
    'update_alpha': 0.1,
    'decay_factor': 0.99,
    'strategy': 'ema'  # ema, additive, multiplicative
})

# Entity type filtering
filter = EntityTypeFilter(graph, config={
    'domain': 'legal',  # legal, academic
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty']
    }
})
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

### Current Research Focus (DynHyperRAG)
- [ ] Quality assessment module (Week 1-4)
- [ ] Dynamic weight update module (Week 5-7)
- [ ] Efficient retrieval module (Week 8-10)
- [ ] CAIL2019 legal dataset preparation (Week 11-12)
- [ ] PubMed/AMiner academic dataset preparation (Week 11-12)
- [ ] Evaluation framework and experiments (Week 13-16)
- [ ] Thesis writing (Week 17-18)

### Completed Features
- [x] Visualization tools for hypergraph exploration ✅
- [x] Comprehensive testing infrastructure ✅
- [x] Production-ready configuration system ✅
- [x] Web UI with interactive graph exploration ✅

### Future Work
- [ ] Optimization for large-scale documents
- [ ] Advanced hyperedge extraction algorithms
- [ ] Multi-language support
- [ ] Integration with other vector databases
- [ ] Performance optimization for web UI

---

## 📝 Citation

If you use this fork or DynHyperRAG in your research, please cite:

### Original HyperGraphRAG Paper
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

### DynHyperRAG (This Research)
```bibtex
@phdthesis{an2025dynhyperrag,
      title={DynHyperRAG: Quality-Aware Dynamic Hypergraph for Efficient Retrieval-Augmented Generation},
      author={Tao An},
      year={2025},
      school={[University Name]},
      note={PhD Thesis, Expected June 2025},
      url={https://github.com/tao-hpu/HyperGraphRAG}
}
```

### This Enhanced Fork
```bibtex
@misc{an2025hypergraphrag-enhanced,
      title={HyperGraphRAG: Enhanced Implementation with Production Features},
      author={Tao An},
      year={2025},
      url={https://github.com/tao-hpu/HyperGraphRAG},
      note={Enhanced fork with configuration system, visualization, and DynHyperRAG research implementation}
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

### This Fork & DynHyperRAG Research
- **Fork Repository**: [tao-hpu/HyperGraphRAG](https://github.com/tao-hpu/HyperGraphRAG)
- **Thesis Overview**: [docs/THESIS_OVERVIEW.md](docs/THESIS_OVERVIEW.md)
- **Research Specs**: [.kiro/specs/dynhyperrag-quality-aware/](.kiro/specs/dynhyperrag-quality-aware/)
- **Maintainer Homepage**: [tao-hpu.github.io](https://tao-hpu.github.io)
- **ORCID**: [0009-0006-2933-0320](https://orcid.org/0009-0006-2933-0320)

### Related Projects
- [cognitive-workspace](https://github.com/tao-hpu/cognitive-workspace) - Active memory management for LLMs
- [CHDA](https://github.com/slanorgcn/CHDA) - Clinical Hypergraph Data Analysis

### Datasets
- **CAIL2019**: Chinese AI and Law Challenge 2019 (Legal domain)
- **PubMed Knowledge Graph**: Academic papers and citations
- **AMiner**: Academic social network dataset

---

<div align="center">

**⭐ If you find this fork useful, please consider giving it a star!**

Made with ❤️ in Beijing

</div>
