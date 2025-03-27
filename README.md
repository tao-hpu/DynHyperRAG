# HyperGraphRAG

Official resources of **"HyperGraphRAG: Retrieval-Augmented Generation with Hypergraph-Structured Knowledge Representation"**. Haoran Luo, Haihong E, Guanting Chen, Yandan Zheng, Xiaobao Wu, Yikai Guo, Qika Lin, Yu Feng, Zemin Kuang, Meina Song, Yifan Zhu, Luu Anh Tuan.

##  Overview 

![](./figs/F1.png)

## Dependence
```bash
conda create -n hypergraphrag python=3.11
conda activate hypergraphrag
pip install -r requirements.txt
```

## Quick Start
### Knowledge HyperGraph Construction
```python
import os
import json
from hypergraphrag import HyperGraphRAG
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

rag = HyperGraphRAG(working_dir=f"expr/example")

with open(f"example_contexts.json", mode="r") as f:
    unique_contexts = json.load(f)
    
rag.insert(unique_contexts)
```

### Knowledge HyperGraph Query
```python
import os
from hypergraphrag import HyperGraphRAG
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

rag = HyperGraphRAG(working_dir=f"expr/example")

query_text = 'How strong is the evidence supporting a systolic BP target of 120–129 mmHg in elderly or frail patients, considering potential risks like orthostatic hypotension, the balance between cardiovascular benefits and adverse effects, and the feasibility of implementation in diverse healthcare settings?'

result = rag.query(query_text)
print(result)
```

## Acknowledgement

This repo benefits from [LightRAG](https://github.com/HKUDS/LightRAG), [Text2NKG](https://github.com/LHRLAB/Text2NKG), and [HAHE](https://github.com/LHRLAB/HAHE).  Thanks for their wonderful works.